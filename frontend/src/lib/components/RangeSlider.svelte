<script lang="ts">
  import Input from "$lib/components/Input.svelte";

  interface Props {
    min: number;
    max: number;
    step: number;
    value: number;
    label: string;
  }

  let { min, max, step, value = $bindable(), label }: Props = $props();
  let current = $state<number>(value);
  let hovered = $state<boolean>(false);
  let slider = $state<HTMLInputElement | null>(null);

  const clamp = (v: number) => Math.min(max, Math.max(min, v));

  $effect(() => {
    current = clamp(value);
  });

  const percent = $derived(((current - min) / (max - min)) * 100);
  const correctedPercent = $derived.by(() => {
    if (!slider) return percent;
    const thumbR = slider.offsetHeight / 2;
    const w = slider.offsetWidth;
    return (((percent / 100) * (w - 2 * thumbR) + thumbR) / w) * 100;
  });

  function update(v: number) {
    current = clamp(v);
    value = current;
  }
</script>

<div class="range">
  {#if label}
    <label>{label}</label>
  {/if}

  <div class="controls">
    <div
      class="slider"
      role="slider"
      tabindex="0"
      aria-valuenow={value}
      aria-valuemin={min}
      aria-valuemax={max}
      onmouseenter={() => (hovered = true)}
      onmouseleave={() => (hovered = false)}
    >
      {#if hovered}
        <div class="slider-tooltip" style="left: {correctedPercent}%">
          {current}
        </div>
      {/if}
      <input
        bind:this={slider}
        type="range"
        {min}
        {max}
        {step}
        value={current}
        oninput={(e) => update(e.target.value)}
        style="--percent: {percent}%"
      />
    </div>
    <Input
      type="number"
      {min}
      {max}
      {step}
      value={current}
      oninput={(e) => update(e.target.value)}
    />
  </div>
</div>

<style>
  .range {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .controls {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .slider {
    position: relative;
  }

  .slider-tooltip {
    position: absolute;
    top: -2rem;
    transform: translateX(-50%);
    padding: 0 var(--size-sm);
    background-color: oklch(var(--color-secondary-accent));
    border-radius: var(--size-sm);
  }

  input[type="range"] {
    flex: 1;
  }

  label {
    font-size: var(--text-sm);
  }
</style>
