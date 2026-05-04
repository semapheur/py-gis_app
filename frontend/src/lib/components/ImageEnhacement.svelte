<script lang="ts">
  import RangeSlider from "$lib/components/RangeSlider.svelte";
  import {
    getImageViewerController,
    type Enhancement,
  } from "$lib/contexts/ol_image_viewer/controller.svelte";
  import Button from "$lib/components/Button.svelte";

  interface SliderConfig {
    key: keyof Enhancement;
    label: string;
    min: number;
    max: number;
    step: number;
  }

  const sliders: SliderConfig[] = [
    { key: "brightness", label: "Brightness", min: -1, max: 1, step: 0.01 },
    { key: "contrast", label: "Contrast", min: -1, max: 1, step: 0.01 },
    { key: "exposure", label: "Exposure", min: -1, max: 1, step: 0.01 },
    { key: "saturation", label: "Saturation", min: -1, max: 1, step: 0.01 },
    { key: "gamma", label: "Gamma", min: 1, max: 10, step: 0.1 },
  ];

  const viewer = getImageViewerController();

  $effect(() => {
    viewer.applyEnhancement();
  });
</script>

<div class="image-enhancement">
  {#each sliders as { key, label, min, max, step }}
    <RangeSlider
      {min}
      {max}
      {step}
      {label}
      bind:value={viewer.enhancement[key]}
    />
  {/each}
  <Button onclick={() => viewer.resetEnhancement()}>Reset</Button>
</div>

<style>
  .image-enhancement {
    padding: var(--size-md);
    background-color: oklch(var(--color-primary));
    border-radius: var(--size-sm);
  }
</style>
