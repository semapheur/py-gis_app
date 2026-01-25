<script lang="ts">
  interface Props {
    min: number;
    max: number;
    step: number;
    value: number;
    label: string;
  }

  let { min, max, step, value = $bindable(), label }: Props = $props();
  let current = $state<number>(value);

  const clamp = (v: number) => Math.min(max, Math.max(min, v));

  $effect(() => {
    current = clamp(value);
  });

  const percent = $derived(((current - min) / (max - min)) * 100);

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
    <input
      type="range"
      {min}
      {max}
      {step}
      value={current}
      oninput={(e) => update(e.target.value)}
      style="--percent: {percent}%"
    />
    <input
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

  input[type="range"] {
    flex: 1;
  }

  input[type="number"] {
    width: 5rem;
  }

  label {
    font-size: var(--text-sm);
  }
</style>
