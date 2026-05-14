<script lang="ts">
  import RangeSlider from "$lib/components/RangeSlider.svelte";
  import { getImageViewerController } from "$lib/contexts/ol_image_viewer/controller.svelte";
  import { type Enhancement } from "$lib/contexts/ol_image_viewer/styling";
  import Button from "$lib/components/Button.svelte";
  import CloseButton from "$lib/components/CloseButton.svelte";

  interface SliderConfig {
    key: keyof Enhancement;
    label: string;
    min: number;
    max: number;
    step: number;
  }

  interface Props {
    isOpen: boolean;
  }

  let { isOpen = $bindable() }: Props = $props();

  const sliders: SliderConfig[] = [
    { key: "brightness", label: "Brightness", min: -0.5, max: 0.5, step: 0.01 },
    { key: "contrast", label: "Contrast", min: 0, max: 4, step: 0.05 },
    { key: "exposure", label: "Exposure", min: -3, max: 3, step: 0.01 },
    { key: "saturation", label: "Saturation", min: 0, max: 3, step: 0.05 },
    { key: "gamma", label: "Gamma", min: 0.2, max: 5, step: 0.05 },
  ];

  const viewer = getImageViewerController();

  $effect(() => {
    viewer.applyEnhancement();
  });
</script>

<div class="image-enhancement">
  <div class="slider-group">
    {#each sliders as { key, label, min, max, step }}
      <RangeSlider
        {min}
        {max}
        {step}
        {label}
        bind:value={viewer.enhancement[key]}
      />
    {/each}
  </div>
  <div class="reset-group">
    <Button onclick={() => viewer.resetEnhancement()}>Reset</Button>
  </div>
  <div class="close-group">
    <CloseButton onclick={() => (isOpen = false)} />
  </div>
</div>

<style>
  .image-enhancement {
    position: relative;
    display: flex;
    flex-direction: column;
    gap: var(--size-lg);
    padding: var(--size-md);
    background-color: oklch(var(--color-primary));
    border-radius: var(--size-sm);
  }

  .reset-group {
    display: flex;
    justify-content: center;
  }

  .close-group {
    position: absolute;
    left: var(--size-md);
    bottom: var(--size-md);
  }
</style>
