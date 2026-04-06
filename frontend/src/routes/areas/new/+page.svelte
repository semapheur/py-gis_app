<script lang="ts">
  import { page } from "$app/state";
  import { setAreaMapState } from "$lib/contexts/ol_area_map.svelte";
  import { setAreaEditorState } from "$lib/contexts/area_editor.svelte";
  import AreaMap from "$lib/components/AreaMap.svelte";
  import AreaEditor from "$lib/components/AreaEditor.svelte";
  import { parseBbox } from "$lib/utils/geo/bbox";

  const initialBbox = page.url.searchParams.get("bbox");
  const bbox = initialBbox !== null ? parseBbox(initialBbox) : initialBbox;

  setAreaMapState([], bbox);
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
