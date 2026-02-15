<script lang="ts">
  import { getContext } from "svelte";
  import { error } from "@sveltejs/kit";
  import Autocomplete from "$lib/components/Autocomplete.svelte";
  import Select from "$lib/components/Select.svelte";
  import { type SelectOption } from "$lib/utils/types";
  import type {
    AnnotateValue,
    EquipmentData,
  } from "$lib/contexts/annotate.svelte";

  type EquipmentPatch = Partial<EquipmentData>;

  interface Props {
    value: EquipmentData | EquipmentPatch;
    onchange: (value: EquipmentData | EquipmentPatch) => void;
    onvalid?: (valid: boolean) => void;
    bulk?: boolean;
  }

  let { value, onchange, onvalid, bulk = false }: Props = $props();

  const { confidenceOptions, statusOptions } = getContext("equipment-options");

  let selectedEquipment = $state<SelectOption | null>(
    toSelectOption(value?.equipment ?? null),
  );
  let confidenceId = $derived<string | null>(value.confidence?.id ?? null);
  let statusId = $derived<string | null>(value.status?.id ?? null);

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
    newValue: EquipmentData[K],
  ) {
    const next = { ...value };

    if (bulk && newValue === undefined) {
      delete (next as EquipmentPatch)[key];
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
    const option = confidenceOptions.find((o) => o.value === id) ?? null;
    update(
      "confidence",
      option ? toAnnotateValue(option) : bulk ? undefined : null,
    );
  }

  function handleStatusChange(id: string | null) {
    const option = statusOptions.find((o) => o.value === id) ?? null;
    update(
      "status",
      option ? toAnnotateValue(option) : bulk ? undefined : null,
    );
  }
  async function searchEquipment(query: string): Promise<SelectOption[]> {
    const response = await fetch("/api/search-equipment", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });

    if (!response.ok) {
      throw error(response.status, "Failed to search equipment");
    }

    return await response.json();
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
  <Select
    options={confidenceOptions}
    placeholder="Confidence"
    value={confidenceId}
    onchange={handleConfidenceChange}
  />
  <Select
    options={statusOptions}
    placeholder="Status"
    value={statusId}
    onchange={handleStatusChange}
  />
</form>

<style>
  .equipment-annotation {
    display: flex;
    flex-direction: column;
    gap: var(--size-lg);
  }
</style>
