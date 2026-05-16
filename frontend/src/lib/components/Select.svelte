<script lang="ts">
  import type { HTMLSelectAttributes } from "svelte/elements";

  interface SelectOption<T = string> {
    label: string;
    value: T;
    disabled?: boolean;
  }

  type OptionInput<T = string> = T | SelectOption<T>;

  interface Props<T = string> extends HTMLSelectAttributes {
    placeholder?: string | null;
    value?: T | null;
    options: readonly OptionInput[];
  }

  const uid = $props.id();
  let {
    placeholder = null,
    value = $bindable(),
    options = [],
    ...rest
  }: Props = $props();

  const normalizedOptions = $derived(
    options.map((o) =>
      typeof o === "string" ? { label: o, value: o.toLowerCase() } : o,
    ),
  );
</script>

<div class="select">
  <select id={uid} bind:value {...rest}>
    {#if placeholder}
      <option value="" disabled hidden>
        {placeholder}
      </option>
    {/if}

    {#each normalizedOptions as o}
      <option value={o.value} disabled={o.disabled}>
        {o.label}
      </option>
    {/each}
  </select>

  {#if placeholder}
    <label for={uid}>{placeholder}</label>
  {/if}
</div>

<style>
  :root {
    --top-float: 0;
  }

  .select {
    position: relative;
  }

  label {
    position: absolute;
    left: var(--size-sm);
    font-size: var(--text-2xs);
    top: var(--top-float);
    transform: translateY(-50%);
    transition: all 0.15s ease;
    text-shadow: var(--text-shadow);
    pointer-events: none;
  }

  select {
    width: 100%;
    height: var(--input-height, auto);
    background-color: oklch(var(--color-primary-accent));
    color: oklch(var(--color-text));
    font-size: inherit;
    border: 1px solid oklch(var(--color-secondary));
    border-radius: var(--size-sm);

    /* hide placeholder text */
    &:has(option[value=""]:checked) + label {
      font-size: inherit;
      background-color: transparent;
    }

    &:focus + label {
      font-size: var(--text-2xs);
      top: var(--top-float);
      transform: translateY(-50%);
      text-shadow: var(--text-shadow);
    }
  }
</style>
