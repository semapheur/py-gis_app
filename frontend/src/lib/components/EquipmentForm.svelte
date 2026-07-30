<script lang="ts">
  import { encode, decode } from "@msgpack/msgpack";
  import Autocomplete from "$lib/components/Autocomplete.svelte";
  import Select from "$lib/components/Select.svelte";
  import MultiSelect from "$lib/components/MultiSelect.svelte";
  import UnitInput from "$lib/components/UnitInput.svelte";
  import { getEquipmentOptions } from "$lib/contexts/common.svelte";
  import { type SelectOption } from "$lib/utils/types";
  import type {
    AnnotateValue,
    EquipmentData,
  } from "$lib/contexts/annotate.svelte";
  import { toast } from "$lib/stores/toast.svelte";

  type EquipmentPatch = Partial<EquipmentData>;

  interface Props {
    value: EquipmentData | EquipmentPatch;
    onchange: (value: EquipmentData | EquipmentPatch) => void;
    onvalid?: (valid: boolean) => void;
    bulk?: boolean;
  }

  let { value, onchange, onvalid, bulk = false }: Props = $props();

  const {
    confidenceOptions,
    statusOptions,
    visibilityOptions,
    configurationOptions,
    modificationOptions,
    camoflageOptions,
  } = getEquipmentOptions();

  const speedUnits = [
    { label: "km/h", value: "kmph", factor: 1.0 / 3.6 },
    { label: "m/s", value: "mps", factor: 1 },
    { label: "kt", value: "kt", factor: 0.514444 },
  ];

  const singleAttributeFields = [
    { key: "confidence", label: "Confidence", options: confidenceOptions },
    { key: "status", label: "Status", options: statusOptions },
    { key: "visibility", label: "Visibility", options: visibilityOptions },
    {
      key: "configuration",
      label: "Configuration",
      options: configurationOptions,
    },
  ] as const satisfies Array<{
    key: keyof Pick<
      EquipmentData,
      "confidence" | "status" | "visibility" | "configuration"
    >;
    label: string;
    options: SelectOption[];
  }>;

  const multiAttributeFields = [
    {
      key: "modification",
      label: "Modification",
      options: modificationOptions,
    },
    {
      key: "camoflage",
      label: "Camoflage",
      options: camoflageOptions,
    },
  ] as const satisfies Array<{
    key: keyof Pick<EquipmentData, "modification" | "camoflage">;
    label: string;
    options: SelectOption[];
  }>;

  type SingleAttributeKey = (typeof singleAttributeFields)[number]["key"];
  type MultiAttributeKey = (typeof multiAttributeFields)[number]["key"];

  let selectedEquipment = $derived(toSelectOption(value.equipment ?? null));

  let singleAttributeIds = $derived.by(() => {
    const ids = {} as Record<SingleAttributeKey, string | null>;
    for (const field of singleAttributeFields) {
      ids[field.key] = value[field.key]?.id ?? null;
    }
    return ids;
  });

  let multiAttributeIds = $derived.by(() => {
    const ids = {} as Record<MultiAttributeKey, string[]>;
    for (const field of multiAttributeFields) {
      ids[field.key] = (value[field.key] ?? []).map((v) => v.id);
    }
    return ids;
  });

  let isValid = $derived.by(() => {
    const full = value as EquipmentData;

    if (bulk) return true;

    if (!full.equipment) return false;

    for (const field of singleAttributeFields) {
      if (!full[field.key]) return false;
    }

    return true;
  });

  $effect(() => {
    onvalid?.(isValid);
  });

  $effect(() => {
    if (bulk) return;

    const missing = singleAttributeFields.filter(
      (field) => !value[field.key] && field.options?.[0],
    );
    if (missing.length === 0) return;

    const next = { ...value } as EquipmentData;

    for (const field of missing) {
      next[field.key] = toAnnotateValue(
        field.options[0],
      ) as EquipmentData[typeof field.key];
    }

    onchange(next);
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

  function handleSingleAttributeChange(
    field: (typeof singleAttributeFields)[number],
    id: string | null,
  ) {
    const option = field.options.find((o) => o.value === id) ?? null;
    update(
      field.key,
      option ? toAnnotateValue(option) : bulk ? undefined : null,
    );
  }

  function handleMultiAttributeChange(
    field: (typeof multiAttributeFields)[number],
    ids: string[],
  ) {
    const values = ids
      .map((id) => field.options.find((o) => o.value === id))
      .filter((o): o is SelectOption => o != null)
      .map((o) => toAnnotateValue(o));

    if (bulk && values.length === 0) {
      update(field.key, undefined);
    } else {
      update(field.key, values);
    }
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
  {#each singleAttributeFields as field (field.key)}
    <Select
      options={field.options}
      placeholder={field.label}
      value={singleAttributeIds[field.key]}
      onchange={(e) =>
        handleSingleAttributeChange(field, e.currentTarget.value)}
    />
  {/each}
  {#each multiAttributeFields as field (field.key)}
    <MultiSelect
      options={field.options}
      placeholder={field.label}
      bind:selected={
        () => multiAttributeIds[field.key],
        (ids) => handleMultiAttributeChange(field, ids)
      }
    />
  {/each}
  <UnitInput units={speedUnits} placeholder="Speed" />
</form>

<style>
  .equipment-annotation {
    display: flex;
    flex-direction: column;
    gap: var(--size-lg);
  }
</style>
