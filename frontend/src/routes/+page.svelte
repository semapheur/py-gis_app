<script lang="ts">
  import { Pane, Splitpanes } from "svelte-splitpanes";
  import Map from "$lib/components/Map.svelte";
  import { goto } from "$app/navigation";
  import { savePolygon } from "$lib/utils/searchStore";

  async function handleSearchExtent(polygon: GeoJSON.Polygon) {
    const id = savePolygon(polygon);

    goto(`/search/${id}`);
  }
</script>

<main class="container">
  <Splitpanes>
    <Pane>
      <Map showSearchButton={true} onSearchExtent={handleSearchExtent} />
    </Pane>
    <Pane>
      <div></div>
    </Pane>
  </Splitpanes>
</main>

<style>
  .container {
    width: 100%;
    height: 100%;
  }
</style>
