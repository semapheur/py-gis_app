<script lang="ts">
  import Input from "$lib/components/Input.svelte";
  import Select from "$lib/components/Select.svelte";

  import {
    equipmentConfidence,
    equipmentStatus,
    type EquipmentData,
  } from "$lib/states/annotate.svelte";

  interface Props {
    value: EquipmentData;
    onchange: (value: EquipmentData) => void;
    onvalid?: (valid: boolean) => void;
  }

  let { value, onchange, onvalid }: Props = $props();

  function update<K extends keyof EquipmentData>(key: K, v: EquipmentData[K]) {
    const next = { ...value, [key]: v };
    onchange(next);
    onvalid?.(isValid(next));
  }

  function isValid(v: EquipmentData) {
    return Boolean(v.id && v.status && v.confidence);
  }
</script>

<form class="form">
  <Input label="Equipment" value={value.id} oninput={(v) => update("id", v)} />
  <Select
    options={equipmentConfidence}
    label="Confidence"
    value={value.confidence}
    onchange={(v) => update("confidence", v)}
  />
  <Select
    options={equipmentStatus}
    label="Status"
    value={value.status}
    onchange={(v) => update("status", v)}
  />
</form>

<style>
  .form {
    display: flex;
    flex-direction: column;
    gap: var(--size-xs);
  }
</style>
