<script lang="ts">
  import { getAreaEditorState } from "$lib/contexts/area_editor.svelte";
  import { getAreaMapState } from "$lib/contexts/ol_area_map.svelte";

  const map = getAreaMapState();
  const editor = getAreaEditorState();

  $effect(() => {
    map.updateDrawInteraction(editor);
  });
</script>

<div
  class="map"
  {@attach (el) => {
    map.attach(el);
  }}
></div>
