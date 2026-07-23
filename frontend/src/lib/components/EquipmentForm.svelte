<script lang="ts">
  import { encode, decode } from "@msgpack/msgpack";
  import Autocomplete from "$lib/components/Autocomplete.svelte";
  import Select from "$lib/components/Select.svelte";
  import { getEquipmentOptions } from "$lib/contexts/common.svelte";
  import { type SelectOption } from "$lib/utils/types";
  import type {
    AnnotateValue,
    EquipmentData,
  } from "$lib/contexts/annotate.svelte";
  import { toast } from "$lib/stores/toast.svelte";
  import type { SchemaId } from "$lib/utils/brand";

  type EquipmentPatch = Partial<EquipmentData>;

  interface Props {
    value: EquipmentData | EquipmentPatch;
    onchange: (value: EquipmentData | EquipmentPatch) => void;
    onvalid?: (valid: boolean) => void;
    bulk?: boolean;
  }

  let { value, onchange, onvalid, bulk = false }: Props = $props();

  const {
    schemaOptions,
    confidenceOptions,
    statusOptions,
    configurationOptions,
    modificationOptions,
    visibilityOptions,
  } = getEquipmentOptions();

  const attributeFields = [
    { key: "confidence", label: "Confidence", options: confidenceOptions },
    { key: "status", label: "Status", options: statusOptions },
    {
      key: "configuration",
      label: "Configuration",
      options: configurationOptions,
    },
    {
      key: "modification",
      label: "Modification",
      options: modificationOptions,
    },
    { key: "visibility", label: "Visibility", options: visibilityOptions },
  ] as const satisfies Array<{
    key: keyof Omit<EquipmentData, "equipment">;
    label: string;
    options: Record<SchemaId, SelectOption[]>;
  }>;

  type AttributeKey = (typeof attributeFields)[number]["key"];

  let selectedEquipment = $derived(toSelectOption(value.equipment ?? null));
  let schemaId = $state<SchemaId>(schemaOptions[0].value);
  let attributeIds = $derived.by(() => {
    const ids = {} as Record<AttributeKey, string | null>;
    for (const field of attributeFields) {
      ids[field.key] =
        value[field.key]?.[schemaId]?.id ??
        field.options[schemaId]?.[0]?.value ??
        null;
    }
    return ids;
  });

  let isValid = $derived.by(() => {
    const full = value as EquipmentData;

    if (!bulk && !full.equipment) return false;

    for (const field of attributeFields) {
      const optionsForSchema = field.options[schemaId];

      if (!optionsForSchema) continue;
      if (bulk) continue;
      if (!full[field.key]?.[schemaId]) return false;
    }

    return true;
  });

  $effect(() => {
    onvalid?.(isValid);
  });

  function update<K extends keyof EquipmentData>(
    key: K,
    newValue: EquipmentData[K] | undefined,
  ) {
    const next = { ...value } as EquipmentPatch;

    if (bulk && newValue === undefined) {
      delete next[key];
    } else {
      next[key] = newValue as EquipmentData[K];
    }

    onchange(next);
  }

  function toAnnotateValue(option: SelectOption | null): AnnotateValue | null {
    return option ? { id: option.value, label: option.label } : null;
  }
  function toSelectOption(value: AnnotateValue | null): SelectOption | null {
    return value ? { value: value.id, label: value.label } : null;
  }

  function handleAttributeChange(
    field: (typeof attributeFields)[number],
    id: string | null,
  ) {
    const option = field.options[schemaId]?.find((o) => o.value === id) ?? null;
    update(
      field.key,
      option ? toAnnotateValue(option) : bulk ? undefined : null,
    );
  }

  async function searchEquipment(query: string): Promise<SelectOption[]> {
    const response = await fetch("/api/search-equipment", {
      method: "POST",
      headers: { "Content-Type": "application/msgpack" },
      body: encode({ query }),
    });

    if (!response.ok) {
      toast.error("Failed to search equipment");
    }

    const buffer = await response.arrayBuffer();
    return decode(buffer) as SelectOption[];
  }
</script>

<form class="equipment-annotation">
  <Autocomplete
    value={selectedEquipment}
    placeholder="Equipment"
    fetchOptions={searchEquipment}
    onchange={(option) => {
      selectedEquipment = option;
      update(
        "equipment",
        option ? toAnnotateValue(option) : bulk ? undefined : null,
      );
    }}
  />
  <Select options={schemaOptions} placeholder="Schema" value={schemaId} />
  {#each attributeFields as field (field.key)}
    {#if field.options[schemaId]}
      <Select
        options={field.options[schemaId]}
        placeholder={field.label}
        value={attributeIds[field.key]}
        onchange={(e) => handleAttributeChange(field, e.currentTarget.value)}
      />
    {/if}
  {/each}
</form>

<style>
  .equipment-annotation {
    display: flex;
    flex-direction: column;
    gap: var(--size-lg);
  }
</style>
