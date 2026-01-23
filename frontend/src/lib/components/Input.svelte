<script lang="ts">
  interface Props {
    value?: string | number | null;
    placeholder?: string;
    required?: boolean;
    fieldSizing?: "content" | "fixed";
    oninput?: (value: string) => void;
    onfocus?: () => void;
    onblur?: () => void;
  }

  let {
    value = null,
    placeholder,
    required = false,
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

<div class="container">
  <input
    id={uid}
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
  :root {
    --top-float: 0rem;
  }

  .container {
    position: relative;
    margin-top: var(--text-2xs);
    min-width: 0;
  }

  label {
    position: absolute;
    left: var(--size-md);
    font-size: var(--text-2xs);
    top: var(--top-float);
    transform: translateY(-50%);
    transition: all 0.15s ease;
    background-color: white;
    pointer-events: none;
  }

  input {
    padding: var(--size-sm);
    max-width: 100%;

    &::placeholder {
      color: transparent;
    }

    &:placeholder-shown + label {
      font-size: inherit;
      background-color: transparent;
      transform: translateY(0);
    }

    &:focus + label {
      font-size: var(--text-2xs);
      top: var(--top-float);
      transform: translateY(-50%);
      background-color: white;
    }
  }
</style>
