<script lang="ts">
  import Input from "$lib/components/Input.svelte";
  import Select from "$lib/components/Select.svelte";

  import {
    equipmentConfidence,
    equipmentStatus,
    type EquipmentData,
    type EquipmentConfidence,
    type EquipmentStatus,
  } from "$lib/utils/types";

  interface Props {
    data: EquipmentData | null;
    onvalid: (valid: boolean) => void;
    oncommit: (data: EquipmentData) => void;
    autoCommit: boolean;
  }

  let { data, onvalid, oncommit, autoCommit = false }: Props = $props();

  function createDefault(): EquipmentData {
    return {
      id: null,
      confidence: equipmentConfidence[0].toLowerCase() as EquipmentConfidence,
      status: equipmentStatus[0].toLowerCase() as EquipmentStatus,
    };
  }

  let draft = $state<EquipmentData>(createDefault());

  $effect(() => {
    draft = data
      ? {
          id: data.id,
          confidence: data.confidence,
          status: data.status,
        }
      : createDefault();
  });

  $effect(() => {
    onvalid(!!draft.id && !!draft.confidence && !!draft.status);
  });

  export function commit() {
    const snapshot = structuredClone($state.snapshot(draft));
    oncommit(snapshot);
    return snapshot;
  }

  function handleChange() {
    if (autoCommit) commit();
  }
</script>

<form class="form">
  <Input label="Equipment" bind:value={draft.id} oninput={handleChange} />
  <Select
    options={equipmentConfidence}
    label="Confidence"
    bind:value={draft.confidence}
    onchange={handleChange}
  />
  <Select
    options={equipmentStatus}
    label="Status"
    bind:value={draft.status}
    onchange={handleChange}
  />
</form>

<style>
  .form {
    display: flex;
    flex-direction: column;
    gap: var(--size-xs);
  }
</style>
