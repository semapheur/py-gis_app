<script lang="ts">
  import RangeSlider from "$lib/components/RangeSlider.svelte";
  import {
    getImageViewerState,
    type Enhancement,
  } from "$lib/contexts/image_viewer.svelte";

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

  let enhancement = $state<Enhancement>({
    brightness: 0,
    contrast: 0,
    exposure: 0,
    saturation: 0,
    gamma: 1,
  });

  const viewer = getImageViewerState();
  $effect(() => {
    viewer.updateEnhancement(enhancement);
  });
</script>

{#each sliders as { key, label, min, max, step }}
  <RangeSlider {min} {max} {step} {label} bind:value={enhancement[key]} />
{/each}
