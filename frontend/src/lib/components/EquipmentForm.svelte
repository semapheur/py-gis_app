<script lang="ts">
  import Input from "$lib/components/Input.svelte";
  import Select from "$lib/components/Select.svelte";

  import {
    equipmentConfidence,
    equipmentStatus,
    type EquipmentData,
  } from "$lib/states/annotate.svelte";

  type EquipmentPatch = Partial<EquipmentData>;

  interface Props {
    value: EquipmentData | EquipmentPatch;
    onchange: (value: EquipmentData | EquipmentPatch) => void;
    onvalid?: (valid: boolean) => void;
    bulk?: boolean;
  }

  let { value, onchange, onvalid, bulk = false }: Props = $props();

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
</script>

<form class="form">
  <Input
    label="Equipment"
    value={value.id ?? ""}
    oninput={(v) => update("id", v || (bulk ? undefined : v))}
  />
  <Select
    options={equipmentConfidence}
    label="Confidence"
    value={value.confidence}
    onchange={(v) => update("confidence", v || (bulk ? undefined : v))}
  />
  <Select
    options={equipmentStatus}
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
