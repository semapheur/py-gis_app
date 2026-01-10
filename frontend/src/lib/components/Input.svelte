<script lang="ts">
  interface Props {
    value?: string | number | null;
    label?: string;
    required?: boolean;
    fieldSizing?: "content" | "fixed";
    oninput?: (value: string) => void;
  }

  let {
    value = null,
    label = "",
    required = false,
    fieldSizing = "fixed",
    oninput,
  }: Props = $props();
  let placeholder = $derived(label);
  let minCh = $derived(Math.max(label.length + 2, 6));

  const uid = $props.id();
</script>

<div class="container">
  <input
    id={uid}
    {placeholder}
    bind:value
    {required}
    style={`field-sizing: ${fieldSizing}; min-width: ${minCh}ch;`}
    oninput={(e) => oninput?.(e.currentTarget.value)}
  />
  {#if label}
    <label for={uid}>{label}</label>
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
