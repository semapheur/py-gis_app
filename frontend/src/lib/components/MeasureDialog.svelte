<script lang="ts">
  import Button from "$lib/components/Button.svelte";
  import {
    getImageViewerState,
    measureOptions,
    type MeasurementType,
  } from "$lib/contexts/image_viewer/state.svelte";
  import Select from "$lib/components/Select.svelte";
  import CloseButton from "./CloseButton.svelte";
  import { getImageViewerController } from "$lib/contexts/image_viewer/controller.svelte";

  interface Props {
    open: boolean;
  }

  const viewerController = getImageViewerController();
  const viewerState = getImageViewerState();

  let { open = $bindable() }: Props = $props();
  let measureType = $state<MeasurementType>("area");
  let isMeasuring = $state<boolean>(false);

  $effect(() => {
    const mode = isMeasuring ? "draw" : "edit";
    viewerState.setActiveMode(mode);
  });

  $effect(() => {
    viewerController.updateDrawMeasurementInteraction(measureType, isMeasuring);
  });

  function handleClose() {
    open = false;
    viewerState.setActiveSet("annotation");
    viewerState.setActiveMode("edit");
  }
</script>

<div class="measurement-dialog">
  <CloseButton onclick={() => handleClose()} />
  <Select
    options={measureOptions}
    placeholder="Type"
    value={measureType}
    onchange={(v) => (measureType = v as MeasurementType)}
  />
  <Button onclick={() => (isMeasuring = !isMeasuring)}
    >{isMeasuring ? "Stop" : "Start"}</Button
  >
  <Button
    background="oklch(var(--color-negative))"
    onclick={() => viewerController.clearMeasurements()}>Clear</Button
  >
</div>

<style>
  .measurement-dialog {
    display: flex;
    gap: var(--size-md);
    position: absolute;
    bottom: var(--size-sm);
    left: 50%;
    transform: translateX(-50%);
    z-index: 2;
    background: oklch(var(--color-primary));
    border-radius: var(--size-md);
    padding: var(--size-md);
  }
</style>
