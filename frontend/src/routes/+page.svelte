<script lang="ts">
  import { goto } from "$app/navigation";
  import { Pane, Splitpanes } from "svelte-splitpanes";
  import Map from "$lib/components/Map.svelte";
  import Tabs from "$lib/components/Tabs.svelte";
  import CoordinateSearch from "$lib/components/CoordinateSearch.svelte";

  import { setMapLibreState } from "$lib/contexts/maplibre.svelte";

  const tabs = [
    { name: "Areas", value: "areas" },
    { name: "Coordinates", value: "coordinates" },
  ] as const;
  type Tabs = (typeof tabs)[number]["value"];

  let activeTab = $state<Tabs>("coordinates");

  setMapLibreState();

  async function handleSearchExtent(polygonWkt: string) {
    goto(`/search?wkt=${encodeURIComponent(polygonWkt)}`);
  }
</script>

<Splitpanes>
  <Pane>
    <Map showSearchButton={true} onSearchExtent={handleSearchExtent} />
  </Pane>
  <Pane class="right-panel">
    <header class="panel-header">
      <Tabs
        {tabs}
        selected={activeTab}
        onselect={(tab) => (activeTab = tab as Tabs)}
      />
    </header>
    <main class="panel-content">
      {#if activeTab === "coordinates"}
        <CoordinateSearch />
      {/if}
    </main>
  </Pane>
</Splitpanes>

<style>
  .right-panel {
    display: grid;
    grid-template-rows: auto 1fr;
    padding: var(--size-md);
  }

  .panel-content {
    height: 100%;
  }
</style>
