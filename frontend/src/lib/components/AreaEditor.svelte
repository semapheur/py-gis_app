<script lang="ts">
  import { getAreaEditorState } from "$lib/contexts/area_editor.svelte";
  import Input from "./Input.svelte";
  import TextArea from "./TextArea.svelte";

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
    <button onclick={() => editor.toggleDraw()}
      >{editor.hasPolygon ? "Redraw polygon" : "Draw polygon"}</button
    >
    <button disabled={!editor.valid()} onclick={() => editor.persist()}
      >Save</button
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
