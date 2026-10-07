<script lang="ts">
  import Input from "$lib/components/Input.svelte";
  import Select from "$lib/components/Select.svelte";
  import { getEquipmentOptions } from "$lib/contexts/common.svelte";
  import type {
    PersonnelData,
    PersonnelPointData,
  } from "$lib/schemas/personnel_annotation";

  interface Props {
    value: PersonnelData;
    onchange: (value: PersonnelData) => void;
    geometry: "Point" | "Polygon";
    bulk?: boolean;
  }

  let { value, onchange, geometry, bulk = false }: Props = $props();

  const options = getEquipmentOptions();

  function update<K extends keyof PersonnelData>(
    key: K,
    newValue: PersonnelData[K] | undefined,
  ) {
    const next: Record<string, unknown> = { ...value };

    if (newValue === undefined) {
      if (bulk) delete next[key];
      else next[key] = null;
    } else {
      next[key] = newValue;
    }

    onchange(next as PersonnelData);
  }
</script>

<form class="personnel-annotation">
  {#if geometry === "Point"}
    <Select
      value={(value as PersonnelPointData).confidence?.id ?? null}
      options={options.confidence}
      placeholder="Confidence"
      onchange={(e) => update("confidence", e.currentTarget.value)}
    />
  {:else if geometry === "Polygon"}
    <Input placeholder="Min count" type="number" min="0" step="1" />
    <Input placeholder="Max count" type="number" min="0" step="1" />
  {/if}
  <Select
    value={(value as PersonnelPointData).affiliation?.id ?? null}
    options={options.affiliation}
    placeholder="Affiliation"
    onchange={(e) => update("affiliation", e.currentTarget.value)}
  />
</form>

<style>
  .personnel-annotation {
    display: flex;
    flex-direction: column;
    gap: var(--size-lg);
  }
</style>
