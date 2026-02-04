<script lang="ts">
  import { setAreaMapState } from "$lib/contexts/area_map.svelte";
  import { setAreaEditorState } from "$lib/contexts/area_editor.svelte";
  import AreaMap from "$lib/components/AreaMap.svelte";
  import AreaEditor from "$lib/components/AreaEditor.svelte";

  setAreaMapState();
  setAreaEditorState();
</script>

<div class="layout">
  <AreaMap />
  <AreaEditor />
</div>

<style>
  .layout {
    display: grid;
    grid-template-columns: 2fr 1fr;
  }
</style>
