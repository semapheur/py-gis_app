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

  type EquipmentPatch = Partial<EquipmentData>;

  interface Props {
    value: EquipmentData | EquipmentPatch;
    onchange: (value: EquipmentData | EquipmentPatch) => void;
    onvalid?: (valid: boolean) => void;
    bulk?: boolean;
  }

  let { value, onchange, onvalid, bulk = false }: Props = $props();

  const { confidenceOptions, statusOptions } = getEquipmentOptions();

  let selectedEquipment = $state<SelectOption | null>(
    toSelectOption(untrack(() => value?.equipment) ?? null),
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
