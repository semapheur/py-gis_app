<script lang="ts">
  import Input from "$lib/components/Input.svelte";
  import Select from "$lib/components/Select.svelte";

  interface Props {
    geometry: "Point" | "Polygon";
  }

  let { geometry }: Props = $props();
</script>

<form class="personnel-annotation">
  {#if geometry === "Point"}
    <Select options={[]} placeholder="Confidence" />
  {:else if geometry === "Polygon"}
    <Input placeholder="Min count" type="number" min="0" step="1" />
    <Input placeholder="Max count" type="number" min="0" step="1" />
  {/if}
  <Select options={[]} placeholder="Affiliation" />
</form>

<style>
  .personnel-annotation {
    display: flex;
    flex-direction: column;
    gap: var(--size-lg);
  }
</style>
