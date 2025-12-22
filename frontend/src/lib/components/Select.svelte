<script lang="ts">
  interface SelectOption<T = string> {
    label: string;
    value: T;
    disabled?: boolean;
  }

  type OptionInput = string | SelectOption;

  interface Props {
    label?: string;
    value?: string | null;
    options: readonly OptionInput[];
  }

  let { label = "", value = $bindable(null), options = [] }: Props = $props();
  let placeholder = $derived(label);
  const normalizedOptions = $derived(
    options.map((o) =>
      typeof o === "string" ? { label: o, value: o.toLowerCase() } : o,
    ),
  );

  const uid = crypto.randomUUID();
</script>

<div class="container">
  <select id={uid} bind:value>
    <option value="" disabled hidden>
      {placeholder}
    </option>

    {#each normalizedOptions as o}
      <option value={o.value} disabled={o.disabled}>
        {o.label}
      </option>
    {/each}
  </select>

  {#if label}
    <label for={uid}>{label}</label>
  {/if}
</div>

<style>
  :root {
    --top-float: 0;
  }

  .container {
    position: relative;
    margin-top: var(--text-2xs);
  }

  label {
    position: absolute;
    left: var(--size-sm);
    font-size: var(--text-2xs);
    top: var(--top-float);
    transform: translateY(-50%);
    transition: all 0.15s ease;
    background-color: white;
    pointer-events: none;
  }

  select {
    width: 100%;
    padding: var(--size-sm);

    /* hide placeholder text */
    &:has(option[value=""]:checked) + label {
      font-size: inherit;
      top: 0.35rem;
      background-color: transparent;
    }

    &:focus + label {
      font-size: var(--text-2xs);
      top: var(--top-float);
      transform: translateY(-50%);
      background-color: white;
    }
  }
</style>
