<script lang="ts">
  import { theme } from "$lib/utils/theme.svelte";
</script>

<button onclick={() => theme.toggle()}>
  {theme.current === "dark" ? "☀️" : "🌙"}
</button>

<style>
  button {
    all: unset;
    cursor: pointer;
  }
</style>
