<script lang="ts">
  import { untrack } from "svelte";
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

  let selectedEquipment = $state<SelectOption | null>(
    toSelectOption(untrack(() => value?.equipment) ?? null),
  );
  let schemaId = $state<SchemaId>(schemaOptions[0].value);
  let confidenceId = $derived<string | null>(
    value.confidence?.[schemaId].id ?? null,
  );
  let statusId = $derived<string | null>(value.status?.[schemaId].id ?? null);
  let configurationId = $derived<string | null>(
    value.configuration?.[schemaId].id ?? null,
  );
  let modificationId = $derived<string | null>(
    value.modification?.[schemaId].id ?? null,
  );
  let visibilityId = $derived<string | null>(
    value.visibility?.[schemaId].id ?? null,
  );

  const isValid = $derived.by(() => {
    if (bulk) {
      return true;
    }

    const full = value as EquipmentData;
    return Boolean(full.equipment && full.status && full.confidence);
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

  function handleConfidenceChange(id: string | null) {
    const option =
      confidenceOptions[schemaId].find((o) => o.value === id) ?? null;
    update(
      "confidence",
      option ? toAnnotateValue(option) : bulk ? undefined : null,
    );
  }

  function handleStatusChange(id: string | null) {
    const option = statusOptions[schemaId].find((o) => o.value === id) ?? null;
    update(
      "status",
      option ? toAnnotateValue(option) : bulk ? undefined : null,
    );
  }

  function handleConfigurationChange(id: string | null) {
    const option =
      configurationOptions[schemaId].find((o) => o.value === id) ?? null;
    update(
      "configuration",
      option ? toAnnotateValue(option) : bulk ? undefined : null,
    );
  }

  function handleModificationChange(id: string | null) {
    const option =
      modificationOptions[schemaId].find((o) => o.value === id) ?? null;
    update(
      "modification",
      option ? toAnnotateValue(option) : bulk ? undefined : null,
    );
  }

  function handleVisibilityChange(id: string | null) {
    const option =
      visibilityOptions[schemaId].find((o) => o.value === id) ?? null;
    update(
      "visibility",
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
  {#if confidenceOptions[schemaId]}
    <Select
      options={confidenceOptions[schemaId]}
      placeholder="Confidence"
      value={confidenceId}
      onchange={(e) => handleConfidenceChange(e.currentTarget.value)}
    />
  {/if}
  {#if statusOptions[schemaId]}
    <Select
      options={statusOptions[schemaId]}
      placeholder="Status"
      value={statusId}
      onchange={(e) => handleStatusChange(e.currentTarget.value)}
    />
  {/if}
  {#if configurationOptions[schemaId]}
    <Select
      options={configurationOptions[schemaId]}
      placeholder="Configuration"
      value={configurationId}
      onchange={(e) => handleConfigurationChange(e.currentTarget.value)}
    />
  {/if}
  {#if modificationOptions[schemaId]}
    <Select
      options={modificationOptions[schemaId]}
      placeholder="Status"
      value={modificationId}
      onchange={(e) => handleModificationChange(e.currentTarget.value)}
    />
  {/if}
  {#if visibilityOptions[schemaId]}
    <Select
      options={visibilityOptions[schemaId]}
      placeholder="Visibility"
      value={visibilityId}
      onchange={(e) => handleVisibilityChange(e.currentTarget.value)}
    />
  {/if}
</form>

<style>
  .equipment-annotation {
    display: flex;
    flex-direction: column;
    gap: var(--size-lg);
  }
</style>
