<script lang="ts">
  import "../app.css";
  import favicon from "$lib/assets/favicon.svg";
  import MenuSidebar from "$lib/components/MenuSidebar.svelte";

  let { children } = $props();
</script>

<svelte:head>
  <link rel="icon" href={favicon} />
</svelte:head>

<div class="layout">
  <MenuSidebar />
  {@render children()}
</div>

<style>
  .layout {
    display: grid;
    grid-template-columns: auto 1fr;
    height: 100%;
  }
</style>
