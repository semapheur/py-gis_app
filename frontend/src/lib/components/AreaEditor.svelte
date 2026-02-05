<script lang="ts">
  import { getAreaEditorState } from "$lib/contexts/area_editor.svelte";
  import Input from "./Input.svelte";
  import TextArea from "./TextArea.svelte";

  const editor = getAreaEditorState();
</script>

<aside class="area-editor">
  <form>
    <Input placeholder="Name" />
    <TextArea placeholder="Description" />
  </form>
  <button onclick={() => editor.toggleDraw()}
    >{editor.hasPolygon ? "Redraw polygon" : "Draw polygon"}</button
  >
</aside>

<style>
  .area-editor {
    display: flex;
    flex-direction: column;
  }
</style>
