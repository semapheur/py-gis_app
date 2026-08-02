<script lang="ts">
  import Switch from "$lib/components/Switch.svelte";
  import CloseButton from "$lib/components/CloseButton.svelte";
  import { getImageViewerController } from "$lib/contexts/ol_image_viewer/controller.svelte";

  interface Props {
    isOpen: boolean;
  }

  let { isOpen = $bindable() }: Props = $props();

  const viewer = getImageViewerController();

  const layers = [
    { key: "labels", label: "Labels" },
    { key: "equipment", label: "Equipment" },
    { key: "activity", label: "Activities" },
    { key: "area", label: "Areas" },
    { key: "measurement", label: "Measurements" },
  ] as const;

  let visibility = $state<Record<(typeof layers)[number]["key"], boolean>>({
    labels: true,
    equipment: true,
    activity: true,
    area: true,
    measurement: true,
  });
</script>

<div class="image-layer-toggle">
  {#each layers as { key, label } (key)}
    <Switch
      bind:checked={visibility[key]}
      {label}
      onchange={(checked) => viewer.toggleLayerVisibility(key, checked)}
    />
  {/each}
  <CloseButton onclick={() => (isOpen = false)} />
</div>

<style>
  .image-layer-toggle {
    position: relative;
    display: flex;
    flex-direction: column;
    gap: var(--size-lg);
    padding: var(--size-md);
    background-color: oklch(var(--color-primary));
    border-radius: var(--size-sm);
  }
</style>
