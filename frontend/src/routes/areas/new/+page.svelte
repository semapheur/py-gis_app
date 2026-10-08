<script lang="ts">
  import { browser } from '$app/env';
  import { page } from "$app/state";
  import { setAreaMapState } from "#lib/contexts/ol_area_map.svelte.js";
  import { setAreaEditorState } from "#lib/contexts/area_editor.svelte.js";
  import AreaMap from "#lib/components/AreaMap.svelte";
  import AreaEditor from "#lib/components/AreaEditor.svelte";
  import { parseBbox } from "#lib/utils/geo/bbox.js";
  import { untrack } from "svelte";

  const bbox = $derived.by(() => {
    if (!browser) return;
    const raw = page.url.searchParams.get("bbox");
    return raw !== null ? parseBbox(raw) : null;
  });

  setAreaMapState(
    [],
    untrack(() => bbox),
  );
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
