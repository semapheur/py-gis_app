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
  import { getImageViewerState } from "$lib/contexts/image_viewer/state.svelte";
  import { getImageViewerController } from "$lib/contexts/image_viewer/controller.svelte";

  interface Props {
    open: boolean;
  }

  const annotateState = getAnnotateState();
  const viewerController = getImageViewerController();
  const viewerState = getImageViewerState();

  let { open = $bindable() }: Props = $props();
  let isAnnotating = $state<boolean>(false);

  $effect(() => {
    const mode = isAnnotating ? "draw" : "edit";
    viewerState.setActiveMode(mode);
  });

  $effect(() => {
    if (viewerState.activeSet !== "annotation" || !annotateState.isValid)
      return;

    const isActive = viewerState.activeMode === "draw";
    viewerController.updateDrawAnnotationInteraction(annotateState, isActive);
  });

  function handleClose() {
    open = false;
    viewerState.setActiveMode("edit");
  }
</script>

<div class="annotate-dialog">
  <header class="header">
    <Tabs
      tabs={annotateTabs}
      selected={annotateState.layer}
      onselect={(layer) =>
        annotateState.setLayer(layer as typeof annotateState.layer)}
    />
    <CloseButton onclick={() => handleClose()} />
  </header>
  <main>
    {#key annotateState.layer}
      {#if annotateState.layer === "equipment"}
        <EquipmentForm
          value={annotateState.data as EquipmentData}
          onchange={(d) => annotateState.setData(d)}
        />
      {:else if annotateState.layer === "activity"}
        <ActivityForm
          value={annotateState.data as ActivityData}
          onchange={(d) => annotateState.setData(d)}
        />
      {/if}
    {/key}
  </main>
  <footer class="footer">
    {#key annotateState.layer}
      <Select
        placeholder="Geometry"
        options={annotateState.geometryOptions}
        value={annotateState.geometry}
        onchange={(v) => annotateState.setGeometry(v)}
      />
    {/key}
    <Button
      background={isAnnotating
        ? "oklch(var(--color-negative))"
        : "oklch(var(--color-positive))"}
      disabled={!annotateState.isValid}
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
