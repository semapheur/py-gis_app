<script lang="ts">
  interface Props {
    value?: string | number | null;
    placeholder?: string;
    required?: boolean;
    invalid?: boolean;
    fieldSizing?: "content" | "fixed";
    oninput?: (value: string) => void;
    onfocus?: () => void;
    onblur?: () => void;
  }

  let {
    value = null,
    placeholder,
    required = false,
    invalid = false,
    fieldSizing = "fixed",
    oninput,
    onfocus,
    onblur,
  }: Props = $props();
  let minCh = $derived(placeholder ? Math.max(placeholder.length + 2, 6) : 0);

  let internal = $state(value ?? "");

  $effect(() => {
    internal = value ?? "";
  });

  const uid = $props.id();
</script>

<div class="input">
  <input
    id={uid}
    class:invalid
    {placeholder}
    bind:value={internal}
    {required}
    style={`field-sizing: ${fieldSizing}; min-width: ${minCh}ch;`}
    oninput={(e) => oninput?.(e.currentTarget.value)}
    {onfocus}
    {onblur}
  />
  {#if placeholder}
    <label for={uid}>{placeholder}</label>
  {/if}
</div>

<style>
  .input {
    position: relative;
    min-width: 0;
  }

  label {
    position: absolute;
    left: var(--size-md);
    font-size: var(--text-2xs);
    top: 0;
    transform: translateY(-50%);
    transition: all 0.15s ease;
    pointer-events: none;
    text-shadow: var(--text-shadow);
  }

  input {
    padding: var(--size-md);
    max-width: 100%;
    font-size: inherit;
    border: 1px solid oklch(var(--color-accent));
    border-radius: var(--size-sm);

    &.invalid {
      border-color: red;
    }

    &::placeholder {
      color: transparent;
    }

    &:placeholder-shown + label {
      font-size: inherit;
      background-color: transparent;
      transform: translateY(0);
      top: var(--size-sm);
    }

    &:focus + label {
      font-size: var(--text-2xs);
      top: 0;
      transform: translateY(-50%);
      text-shadow: var(--text-shadow);
    }
  }
</style>
