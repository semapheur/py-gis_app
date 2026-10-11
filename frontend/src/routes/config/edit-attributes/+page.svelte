<script lang="ts">
  import LinkText from "#lib/components/LinkText.svelte";
</script>

<svelte:head>
  <title>Edit attributes</title>
</svelte:head>

<nav>
  <LinkText href="/config" label="Back" />
  <LinkText
    href="/config/edit-attributes/annotation"
    label="Annotation attributes"
  />
  <LinkText
    href="/config/edit-attributes/security"
    label="Security attributes"
  />
  <LinkText
    href="/config/edit-attributes/reference"
    label="Reference attributes"
  />
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
