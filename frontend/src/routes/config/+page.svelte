<script lang="ts">
  import Link from "$lib/components/Link.svelte";
</script>

<nav>
  <Link href="config/index-images">Index images</Link>
  <Link href="config/edit-catalogs">Edit catalogs</Link>
  <Link href="config/edit-attributes">Edit attributes</Link>
  <Link href="config/edit-equipment">Edit equipment</Link>
</nav>

<style>
  nav {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    gap: var(--size-md);
  }
</style>
