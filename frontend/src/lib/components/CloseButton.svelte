<script lang="ts">
  interface Props {
    onclick: () => void;
  }

  let { onclick }: Props = $props();
</script>

<button type="button" {onclick}> ✕ </button>

<style>
  button {
    all: unset;
    cursor: pointer;
    color: oklch(var(--color-text));

    &:hover {
      color: red;
    }
  }
</style>
