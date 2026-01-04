<script lang="ts">
  type Resize =
    | "none"
    | "both"
    | "horizontal"
    | "vertical"
    | "block"
    | "inline";

  interface Props {
    value?: string | number | null;
    label?: string;
    required?: boolean;
    rows?: number;
    resize?: Resize;
    oninput?: (value: string) => void;
  }

  let {
    value = null,
    label = "",
    required = false,
    rows = 4,
    resize = "vertical",
    oninput,
  }: Props = $props();

  let placeholder = $derived(label);
  const uid = $props.id();
</script>

<div class="container">
  <textarea
    id={uid}
    {placeholder}
    bind:value
    {required}
    {rows}
    style:resize
    oninput={(e) => oninput?.(e.currentTarget.value)}
  ></textarea>

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

  textarea {
    padding: var(--size-sm);

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
