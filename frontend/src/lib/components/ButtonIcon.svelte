<script lang="ts">
  import { type Snippet } from "svelte";
  import { type HTMLButtonAttributes } from "svelte/elements";

  interface Props extends HTMLButtonAttributes {
    children: Snippet;
  }

  const { children, ...rest }: Props = $props();
</script>

<button {...rest}>
  {@render children()}
</button>

<style>
  button {
    all: unset;
    cursor: pointer;
  }
</style>
