<script lang="ts">
  import EquipmentForm from "$lib/components/EquipmentForm.svelte";
  import ActivityForm from "$lib/components/ActivityForm.svelte";
  import Select from "$lib/components/Select.svelte";
  import Tabs from "$lib/components/Tabs.svelte";
  import Button from "$lib/components/Button.svelte";
  import CloseButton from "$lib/components/CloseButton.svelte";

  import {
    getAnnotateState,
    annotateTabs,
    type ActivityData,
    type EquipmentData,
  } from "$lib/contexts/annotate.svelte";
  import { getImageViewerState } from "$lib/contexts/image_viewer.svelte";

  interface Props {
    open: boolean;
  }

  const annotate = getAnnotateState();
  const imageViewer = getImageViewerState();

  let { open = $bindable() }: Props = $props();
  let isAnnotating = $state<boolean>(false);

  $effect(() => {
    if (isAnnotating) {
      imageViewer.startDrawInteraction("annotation");
    } else {
      imageViewer.stopDrawInteraction("annotation");
    }
  });

  function handleClose() {
    open = false;
    imageViewer.stopDrawInteraction("annotation");
  }
</script>

<div class="annotate-dialog">
  <header class="header">
    <Tabs
      tabs={annotateTabs}
      selected={annotate.layer}
      onselect={(layer: typeof annotate.layer) => annotate.setLayer(layer)}
    />
    <CloseButton onclick={() => handleClose()} />
  </header>
  <main>
    {#key annotate.layer}
      {#if annotate.layer === "equipment"}
        <EquipmentForm
          value={annotate.data as EquipmentData}
          onchange={(d) => annotate.setData(d)}
        />
      {:else if annotate.layer === "activity"}
        <ActivityForm
          value={annotate.data as ActivityData}
          onchange={(d) => annotate.setData(d)}
        />
      {/if}
    {/key}
  </main>
  <footer class="footer">
    {#key annotate.layer}
      <Select
        placeholder="Geometry"
        options={annotate.geometryOptions}
        value={annotate.geometry}
        onchange={(v) => annotate.setGeometry(v)}
      />
    {/key}
    <Button
      background={isAnnotating
        ? "oklch(var(--color-negative))"
        : "oklch(var(--color-positive))"}
      disabled={!annotate.isValid}
      onclick={() => (isAnnotating = !isAnnotating)}
    >
      {isAnnotating ? "Stop" : "Annotate"}
    </Button>
  </footer>
</div>

<style>
  .annotate-dialog {
    position: absolute;
    display: flex;
    flex-direction: column;
    gap: var(--size-sm);
    bottom: var(--size-sm);
    left: var(--size-sm);
    z-index: 2;
    background: oklch(var(--color-primary));
    border-radius: var(--size-md);
    padding: var(--size-md);
  }

  .header {
    display: flex;
    justify-content: space-between;
    border-bottom: 1px solid oklch(var(--color-text) / 0.5);
  }

  .footer {
    display: flex;
    justify-content: end;
    gap: var(--size-sm);
    padding-top: var(--size-sm);
    border-top: 1px solid oklch(var(--color-text) / 0.5);
  }
</style>
