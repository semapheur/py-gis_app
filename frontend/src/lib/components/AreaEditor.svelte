<script lang="ts">
  import { getAreaEditorState } from "$lib/contexts/area_editor.svelte";

  const editor = getAreaEditorState();
</script>

<aside>
  <button onclick={() => editor.toggleDraw()}>Draw polygon</button>
</aside>
