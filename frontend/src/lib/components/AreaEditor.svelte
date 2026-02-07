<script lang="ts">
  import { getAreaEditorState } from "$lib/contexts/area_editor.svelte";
  import Input from "$lib/components/Input.svelte";
  import TextArea from "$lib/components/TextArea.svelte";
  import Button from "$lib/components/Button.svelte";

  const editor = getAreaEditorState();
</script>

<aside class="area-editor">
  <form>
    <Input
      placeholder="Name"
      value={editor.data.name}
      oninput={(v) => (editor.data.name = v)}
    />
    <TextArea
      placeholder="Description"
      oninput={(v) => (editor.data.description = v)}
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
</aside>

<style>
  .area-editor {
    display: flex;
    flex-direction: column;
    gap: var(--size-md);
    padding: 0 var(--size-md);
  }

  .button-group {
    display: flex;
    justify-content: space-between;
  }
</style>
