<script lang="ts">
  import { getAreaEditorState } from "$lib/contexts/area_editor.svelte";
  import Button from "$lib/components/Button.svelte";
  import Input from "$lib/components/Input.svelte";
  import Link from "$lib/components/Link.svelte";
  import TextArea from "$lib/components/TextArea.svelte";

  const editor = getAreaEditorState();
</script>

<aside class="area-editor">
  {#if editor.mode === "create" && editor.areaId}
    <Link href={`/areas/${editor.areaId}`}>
      {editor.data.name}
    </Link>
  {:else}
    <form class="area-form">
      <Input
        placeholder="Name"
        value={editor.data.name}
        oninput={(e) => (editor.data.name = e.currentTarget.value)}
      />
      <TextArea
        placeholder="Description"
        oninput={(e) => (editor.data.description = e.currentTarget.value)}
      />
    </form>
    <div class="button-group">
      <Button onclick={() => editor.toggleDraw()}
        >{editor.hasPolygon ? "Redraw polygon" : "Draw polygon"}</Button
      >
      <Button disabled={!editor.valid()} onclick={() => editor.persist()}
        >Save</Button
      >
    </div>
  {/if}
</aside>

<style>
  .area-editor {
    display: flex;
    flex-direction: column;
    gap: var(--size-md);
    padding: var(--size-md);
  }

  .area-form {
    display: flex;
    flex-direction: column;
    gap: var(--size-lg);
  }

  .button-group {
    display: flex;
    justify-content: space-between;
  }
</style>
