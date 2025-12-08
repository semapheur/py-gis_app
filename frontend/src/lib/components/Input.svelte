<script lang="ts">
  export let id: string;
  export let value: string | number | null;
  export let label: string = "";

  $: placeholder = label;
</script>

<div class="container">
  <input {id} {placeholder} bind:value {...$$props} />
  {#if label}
    <label for={id}>{label}</label>
  {/if}
</div>

<style>
  :root {
    --padding-x: 0.4rem;
    --top-float: -0.6rem;
    --font-small: 0.75rem;
  }

  .container {
    position: relative;
  }

  label {
    position: absolute;
    left: var(--padding-x);
    font-size: var(--font-small);
    top: var(--top-float);
    transition: all 0.15s ease;
    background-color: white;
    pointer-events: none;
  }

  input {
    padding: 0.4rem var(--padding-x) 0.2rem var(--padding-x);

    &::placeholder {
      color: transparent;
    }

    &:placeholder-shown + label {
      font-size: inherit;
      top: 0.2rem;
      background-color: transparent;
    }

    &:focus + label {
      font-size: var(--font-small);
      top: var(--top-float);
      background-color: white;
    }
  }
</style>
