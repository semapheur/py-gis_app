<script lang="ts">
  import Button from "$lib/components/Button.svelte";
  import {
    getImageViewerState,
    measureOptions,
    type MeasurementType,
  } from "$lib/contexts/image_viewer.svelte";
  import Select from "$lib/components/Select.svelte";
  import CloseButton from "./CloseButton.svelte";

  interface Props {
    open: boolean;
  }

  const imageViewer = getImageViewerState();

  let { open = $bindable() } = $props();
  let measureType = $state<MeasurementType>("area");
  let isMeasuring = $state<boolean>(false);

  $effect(() => {
    if (isMeasuring) {
      imageViewer.startMeasurement(measureType);
    } else {
      imageViewer.stopMeasurement();
    }
  });

  function handleClose() {
    open = false;
    imageViewer.stopMeasurement();
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
  <Button onclick={() => imageViewer.clearMeasurements()}>Clear</Button>
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
