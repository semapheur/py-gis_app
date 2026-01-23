<script lang="ts">
  import { getContext } from "svelte";
  import { error } from "@sveltejs/kit";
  import Autocomplete from "$lib/components/Autocomplete.svelte";
  import Select from "$lib/components/Select.svelte";
  import { type SelectOption } from "$lib/utils/types";

  import { type EquipmentData } from "$lib/contexts/annotate.svelte";

  type EquipmentPatch = Partial<EquipmentData>;

  interface Props {
    value: EquipmentData | EquipmentPatch;
    onchange: (value: EquipmentData | EquipmentPatch) => void;
    onvalid?: (valid: boolean) => void;
    bulk?: boolean;
  }

  let { value, onchange, onvalid, bulk = false }: Props = $props();

  const { confidence, status } = getContext("equipment-options");

  function update<K extends keyof EquipmentData>(key: K, v: EquipmentData[K]) {
    const next = { ...value, [key]: v };

    if (bulk && v === undefined) {
      delete (next as EquipmentPatch)[key];
    }

    onchange(next);
    onvalid?.(isValid(next));
  }

  function isValid(v: EquipmentData | EquipmentPatch) {
    if (bulk) {
      return true;
    }

    const full = v as EquipmentData;
    return Boolean(full.id && full.status && full.confidence);
  }

  async function searchEquipment(query: string) {
    const response = await fetch("/api/search-equipment", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });

    if (!response.ok) {
      throw error(response.status, "Failed to search equipment");
    }

    return (await response.json()) as SelectOption[];
  }
</script>

<form class="form">
  <Autocomplete placeholder="Equipment" fetchOptions={searchEquipment} />
  <Select
    options={confidence}
    label="Confidence"
    value={value.confidence}
    onchange={(v) => update("confidence", v || (bulk ? undefined : v))}
  />
  <Select
    options={status}
    label="Status"
    value={value.status}
    onchange={(v) => update("status", v || (bulk ? undefined : v))}
  />
</form>

<style>
  .form {
    display: flex;
    flex-direction: column;
    gap: var(--size-xs);
  }
</style>
