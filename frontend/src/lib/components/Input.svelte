<script lang="ts">
  interface Props {
    value?: string | number | null;
    label?: string;
    required?: boolean;
    oninput?: (event: Event) => void;
  }

  let {
    value = $bindable(null),
    label = "",
    required = false,
    oninput,
  }: Props = $props();
  let placeholder = $derived(label);

  const uid = crypto.randomUUID();
</script>

<div class="container">
  <input id={uid} {placeholder} bind:value {required} {oninput} />
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

  input {
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
