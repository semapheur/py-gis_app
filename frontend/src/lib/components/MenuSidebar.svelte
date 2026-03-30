<script lang="ts">
  import ThemeToggle from "$lib/components/ThemeToggle.svelte";
</script>

<nav class="menu">
  <div class="links">
    <a href="/"> H </a>
    <a href="/search"> S </a>
    <a href="/config"> C </a>
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
  }

  .links {
    display: flex;
    flex-direction: column;
  }
</style>
