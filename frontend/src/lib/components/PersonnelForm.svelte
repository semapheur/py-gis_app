<script lang="ts">
  import Input from "#lib/components/Input.svelte";
  import Select from "#lib/components/Select.svelte";
  import { getEquipmentOptions } from "#lib/contexts/common.svelte.js";
  import type {
    PersonnelData,
    PersonnelPatch,
    PersonnelPointData,
  } from "#lib/schemas/personnel_annotation.js";
  import type { AttributeValue } from "#lib/utils/types.js";

  interface Props {
    value: PersonnelData;
    onchange: (value: PersonnelData) => void;
    geometry: "Point" | "Polygon";
    bulk?: boolean;
  }

  let { value, onchange, geometry, bulk = false }: Props = $props();

  const options = getEquipmentOptions();

  function update<K extends keyof PersonnelPatch>(
    key: K,
    newValue: AttributeValue | number | null | undefined,
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

  function handleAttributeChange(
    key: "confidence" | "affiliation",
    id: string | null,
  ) {
    const option = options[key]?.find((o) => o.value === id) ?? null;
    const attribute: AttributeValue | null = option
      ? { id: option.value, label: option.label }
      : null;
    update(key, attribute ?? undefined);
  }

  function handleCountChange(key: "min_count" | "max_count", raw: string) {
    const n = raw === "" ? undefined : Number(raw);
    update(key, n);
  }
</script>

<form class="personnel-annotation">
  {#if geometry === "Point"}
    <Select
      value={(value as PersonnelPointData).confidence?.id ?? null}
      options={options.confidence}
      placeholder="Confidence"
      onchange={(e) =>
        handleAttributeChange("confidence", e.currentTarget.value)}
    />
  {:else if geometry === "Polygon"}
    <Input
      placeholder="Min count"
      type="number"
      min="0"
      step="1"
      oninput={(e) => handleCountChange("min_count", e.currentTarget.value)}
    />
    <Input
      placeholder="Max count"
      type="number"
      min="0"
      step="1"
      oninput={(e) => handleCountChange("max_count", e.currentTarget.value)}
    />
  {/if}
  <Select
    value={(value as PersonnelPointData).affiliation?.id ?? null}
    options={options.affiliation}
    placeholder="Affiliation"
    onchange={(e) =>
      handleAttributeChange("affiliation", e.currentTarget.value)}
  />
</form>

<style>
  .personnel-annotation {
    display: flex;
    flex-direction: column;
    gap: var(--size-lg);
  }
</style>
