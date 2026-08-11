<script lang="ts">
  import LinkText from "$lib/components/LinkText.svelte";
</script>

<nav>
  <LinkText href="config/index-images" label="Index images" />
  <LinkText href="config/edit-catalogs" label="Edit catalogs" />
  <LinkText href="config/edit-security" label="Edit security attributes" />
  <LinkText href="config/edit-attributes" label="Edit annotation attributes" />
  <LinkText href="config/edit-equipment" label="Edit equipment" />
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
