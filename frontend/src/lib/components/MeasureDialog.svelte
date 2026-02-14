<script lang="ts">
  import Button from "$lib/components/Button.svelte";
  import { getImageViewerState } from "$lib/contexts/image_viewer.svelte";

  const imageViewer = getImageViewerState();
</script>

<div class="measurement-dialog">
  <Button onclick={() => imageViewer.startMeasurement("area")}>Start</Button>
</div>

<style>
  .measurement-dialog {
    position: absolute;
    bottom: var(--size-sm);
    left: 50%;
    z-index: 2;
    background: oklch(var(--color-primary));
    border-radius: var(--size-md);
    padding: var(--size-md);
  }
</style>
