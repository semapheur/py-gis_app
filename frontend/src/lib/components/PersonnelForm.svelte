<script lang="ts">
  import Input from "#lib/components/Input.svelte";
  import Select from "#lib/components/Select.svelte";
  import { getEquipmentOptions } from "#lib/contexts/common.svelte.js";
  import type {
    PersonnelData,
    PersonnelPatch,
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

  const minCount = $derived((value as PersonnelPatch).min_count ?? undefined);
  const maxCount = $derived((value as PersonnelPatch).max_count ?? undefined);

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
    const n = raw === "" ? undefined : Math.max(0, Math.trunc(Number(raw)));

    if (n === undefined || Number.isNaN(n)) {
      update(key, undefined);
      return;
    }

    const next: Record<string, unknown> = { ...value, [key]: n };

    if (key === "min_count" && maxCount !== undefined && n > maxCount) {
      next.max_count = n;
    } else if (key === "max_count" && minCount !== undefined && n < minCount) {
      next.min_count = n;
    }

    onchange(next as PersonnelData);
  }
</script>

<form class="personnel-annotation">
  {#if geometry === "Polygon"}
    <Input
      placeholder="Min count"
      type="number"
      min="0"
      max={maxCount}
      step="1"
      value={minCount ?? ""}
      onchange={(e) => handleCountChange("min_count", e.currentTarget.value)}
    />
    <Input
      placeholder="Max count"
      type="number"
      min={minCount ?? 0}
      step="1"
      value={maxCount ?? ""}
      onchange={(e) => handleCountChange("max_count", e.currentTarget.value)}
    />
  {/if}
  <Select
    value={(value as PersonnelData).confidence?.id ?? null}
    options={options.confidence}
    placeholder="Confidence"
    onchange={(e) => handleAttributeChange("confidence", e.currentTarget.value)}
  />
  <Select
    value={(value as PersonnelData).affiliation?.id ?? null}
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
