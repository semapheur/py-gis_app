<script lang="ts">
  import { getAreaMapState } from "$lib/contexts/area_map.svelte";

  const map = getAreaMapState();
</script>

<div
  class="map"
  {@attach (el) => {
    map.attach(el);
  }}
></div>
