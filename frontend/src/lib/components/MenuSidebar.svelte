<script lang="ts">
  import MdiMapOutline from "@iconify-svelte/mdi/map-outline";
  import MdiImageSearchOutline from "@iconify-svelte/mdi/image-search-outline";
  import MdiSettingsOutline from "@iconify-svelte/mdi/settings-outline";
  import ThemeToggle from "$lib/components/ThemeToggle.svelte";
  import LinkIcon from "$lib/components/LinkIcon.svelte";
</script>

<nav class="menu">
  <div class="links">
    <LinkIcon href="/" tooltip="Map explorer" tooltipPlacement="right"
      ><MdiMapOutline width="var(--text-xl)" /></LinkIcon
    >
    <LinkIcon href="/search" tooltip="Image search" tooltipPlacement="right"
      ><MdiImageSearchOutline width="var(--text-xl)" /></LinkIcon
    >
    <LinkIcon href="/config" tooltip="Configuration" tooltipPlacement="right"
      ><MdiSettingsOutline width="var(--text-xl)" /></LinkIcon
    >
  </div>

  <div>
    <ThemeToggle />
  </div>
</nav>

<style>
  .menu {
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: var(--size-sm);
    background-color: oklch(var(--color-accent));
  }

  .links {
    display: flex;
    flex-direction: column;
  }
</style>
