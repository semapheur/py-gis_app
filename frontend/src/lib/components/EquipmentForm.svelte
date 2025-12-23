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
    data: EquipmentData;
    valid: boolean;
  }

  let { data = $bindable(), valid = $bindable() }: Props = $props();

  $effect(() => {
    valid = !!data.id && !!data.confidence && !!data.status;
  });
</script>

<form class="form">
  <Input label="Equipment" bind:value={data.id} />
  <Select
    options={equipmentConfidence}
    label="Confidence"
    bind:value={data.confidence}
  />
  <Select options={equipmentStatus} label="Status" bind:value={data.status} />
</form>

<style>
  .form {
    display: flex;
    flex-direction: column;
    gap: var(--size-xs);
  }
</style>
