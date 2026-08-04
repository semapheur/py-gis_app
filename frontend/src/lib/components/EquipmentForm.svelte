<script lang="ts">
  import { encode, decode } from "@msgpack/msgpack";
  import Autocomplete from "$lib/components/Autocomplete.svelte";
  import MultiAutocomplete from "$lib/components/MultiAutocomplete.svelte";
  import Select from "$lib/components/Select.svelte";
  import MultiSelect from "$lib/components/MultiSelect.svelte";
  import UnitInput from "$lib/components/UnitInput.svelte";
  import { getEquipmentOptions } from "$lib/contexts/common.svelte";
  import { type AttributeValue, type SelectOption } from "$lib/utils/types";
  import { toast } from "$lib/stores/toast.svelte";
  import {
    equipmentSchema,
    type EquipmentData,
    type EquipmentFieldDef,
    type EquipmentFieldKey,
  } from "$lib/schemas/equipment_annotation";

  type EquipmentPatch = Partial<EquipmentData>;

  interface Props {
    value: EquipmentData | EquipmentPatch;
    onchange: (value: EquipmentData | EquipmentPatch) => void;
    onvalid?: (valid: boolean) => void;
    bulk?: boolean;
  }

  let { value, onchange, onvalid, bulk = false }: Props = $props();

  const options = getEquipmentOptions();

  const fieldEntries = Object.entries(equipmentSchema) as [
    EquipmentFieldKey,
    (typeof equipmentSchema)[EquipmentFieldKey],
  ][];

  const numericFieldEntries = fieldEntries.filter(
    (
      entry,
    ): entry is [
      EquipmentFieldKey,
      Extract<EquipmentFieldDef, { kind: "numeric" }>,
    ] => entry[1].kind === "numeric",
  );

  const selectableFieldEntries = fieldEntries.filter(
    (
      entry,
    ): entry is [
      EquipmentFieldKey,
      Extract<EquipmentFieldDef, { kind: "single" | "multi" | "search" }>,
    ] => entry[1].kind !== "numeric",
  );

  const numericUnits = $state(
    Object.fromEntries(
      numericFieldEntries.map(([key, def]) => [key, def.units[0].value]),
    ),
  );

  const isValid = $derived.by(() => {
    if (bulk) return true;

    const full = value as EquipmentData;
    return fieldEntries
      .filter(([, def]) => def.required)
      .every(([key]) => !!full[key]);
  });

  $effect(() => {
    onvalid?.(isValid);
  });

  $effect(() => {
    if (bulk) return;

    const missing = selectableFieldEntries.filter(
      ([key, def]) =>
        def.kind === "single" &&
        def.required &&
        !value[key] &&
        options[key]?.[0],
    );
    if (missing.length === 0) return;

    const next = { ...value } as EquipmentData;

    for (const [key] of missing) {
      next[key] = toAttributeValue(
        options[key][0],
      ) as EquipmentData[typeof key];
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

  function toAttributeValue(
    option: SelectOption | null,
  ): AttributeValue | null {
    return option ? { id: option.value, label: option.label } : null;
  }
  function toSelectOption(value: AttributeValue | null): SelectOption | null {
    return value ? { value: value.id, label: value.label } : null;
  }
  function toAnnotateValues(options: SelectOption[]): AttributeValue[] {
    return options.map((o) => ({ id: o.value, label: o.label }));
  }
  function toSelectOptions(values: AttributeValue[] | null): SelectOption[] {
    return (values ?? []).map((v) => ({ value: v.id, label: v.label }));
  }

  function handleSingleAttributeChange(
    key: EquipmentFieldKey,
    id: string | null,
  ) {
    const option = options[key].find((o) => o.value === id) ?? null;
    update(key, option ? toAttributeValue(option) : bulk ? undefined : null);
  }

  function handleMultiAttributeChange(key: EquipmentFieldKey, ids: string[]) {
    const values = ids
      .map((id) => options[key]?.find((o) => o.value === id))
      .filter((o): o is SelectOption => o != null)
      .map((o) => toAttributeValue(o));

    if (bulk && values.length === 0) {
      update(key, undefined);
    } else {
      update(key, values);
    }
  }

  function handleMultiSearchChange(
    key: EquipmentFieldKey,
    selected: SelectOption[],
  ) {
    if (bulk && selected.length === 0) {
      update(key, undefined);
    } else {
      update(key, toAnnotateValues(selected));
    }
  }

  function factorFor(
    key: EquipmentFieldKey,
    def: Extract<EquipmentFieldDef, { kind: "numeric" }>,
  ) {
    return def.units.find((u) => u.value === numericUnits[key])?.factor ?? 1;
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
  {#each selectableFieldEntries as [key, def] (key)}
    {#if def.kind === "search"}
      <Autocomplete
        value={toSelectOption(value[key] as AttributeValue | null)}
        placeholder={def.label}
        fetchOptions={searchEquipment}
        onchange={(option) =>
          update(
            key,
            option ? toAttributeValue(option) : bulk ? undefined : null,
          )}
      />
    {:else if def.kind === "multi-search"}
      <MultiAutocomplete
        selected={toSelectOptions(value[key] as AttributeValue[] | null)}
        placeholder={def.label}
        fetchOptions={searchEquipment}
        onchange={(selected) => handleMultiSearchChange(key, selected)}
      />
    {:else if def.kind === "single"}
      <Select
        options={options[key] ?? []}
        placeholder={def.label}
        value={(value[key] as AttributeValue | null)?.id ?? null}
        onchange={(e) =>
          handleSingleAttributeChange(key, e.currentTarget.value)}
      />
    {:else if def.kind === "multi"}
      <MultiSelect
        options={options[key] ?? []}
        placeholder={def.label}
        bind:selected={
          () => (value[key] as AttributeValue[] | null)?.map((v) => v.id) ?? [],
          (ids) => handleMultiAttributeChange(key, ids)
        }
      />
    {/if}
  {/each}

  {#each numericFieldEntries as [key, def] (key)}
    <UnitInput
      units={def.units}
      placeholder={def.label}
      min={def.min}
      bind:unit={numericUnits[key]}
      bind:value={
        () =>
          value[key] != null
            ? Math.round(((value[key] as number) / factorFor(key, def)) * 1e6) /
              1e6
            : null,
        () => {}
      }
      bind:baseValue={
        () => (value[key] as number | null) ?? null,
        (v) => update(key, v ?? (bulk ? undefined : null))
      }
    />
  {/each}
</form>

<style>
  .equipment-annotation {
    display: flex;
    flex-direction: column;
    gap: var(--size-lg);
  }
</style>
