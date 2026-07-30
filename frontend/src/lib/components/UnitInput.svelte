<script lang="ts">
  interface UnitOption {
    label: string;
    value: string;
    factor: number;
  }

  interface Props {
    value: number | null;
    baseValue: number | null;
    unit: string;
    units: UnitOption[];
    placeholder: string;
    min?: string;
    max?: string;
    step?: string;
  }

  let {
    value = $bindable(null),
    unit,
    units,
    baseValue = $bindable(null),
    placeholder,
    min,
    max,
    step = "any",
  }: Props = $props();

  const uid = $props.id();

  $effect(() => {
    if (units.length && !units.some((u) => u.value === unit)) {
      unit = units[0].value;
    }
  });

  const selectedUnit = $derived(units.find((u) => u.value === unit));
  const factor = $derived(selectedUnit?.factor ?? 1);

  $effect(() => {
    const n = Number(value);
    baseValue = Number.isFinite(n) ? n * factor : NaN;
  });

  function handleNumberInput(e: Event) {
    const raw = (e.currentTarget as HTMLInputElement).value;
    value = raw === "" ? null : Number(raw);
  }
</script>

<div class="unit-input">
  <input
    id={uid}
    type="number"
    {value}
    {min}
    {max}
    {step}
    {placeholder}
    oninput={handleNumberInput}
  />
  {#if placeholder}
    <label for={uid}>{placeholder}</label>
  {/if}
  <select bind:value={unit} aria-label="Unit">
    {#each units as u (u.value)}
      <option value={u.value}>{u.label}</option>
    {/each}
  </select>
</div>

<style>
  .unit-input {
    position: relative;
    display: flex;
  }

  label {
    position: absolute;
    left: var(--size-md);
    font-size: var(--text-2xs);
    top: 0;
    transform: all 0.15s ease;
    color: oklch(var(--color-text));
    pointer-events: none;
    text-shadow: var(--text-shadow);
  }

  input {
    max-width: 100%;
    height: var(--input-height, auto);
    padding: 0 var(--size-md);
    font-size: inherit;
    color: oklch(var(--color-text));
    background-color: oklch(var(--color-primary-accent));
    border: 1px solid oklch(var(--color-secondary));
    border-radius: var(--size-sm) 0 0 var(--size-sm);

    &::placeholder {
      color: transparent;
    }

    &:placeholder-shown + label {
      font-size: inherit;
      background-color: transparent;
      transform: translateY(0);
      top: var(--size-sm);
      text-shadow: none;
    }

    &:focus + label {
      font-size: var(--text-2xs);
      top: 0;
      transform: translateY(-50%);
      text-shadow: var(--text-shadow);
    }
  }

  select {
    width: 100%;
    height: var(--input-height, auto);
    background-color: oklch(var(--color-secondary));
    color: oklch(var(--color-text));
    font-size: inherit;
    border: 1px solid oklch(var(--color-secondary));
    border-radius: 0 var(--size-sm) var(--size-sm) 0;
  }
</style>
