<script lang="ts">
  import { goto } from "$app/navigation";
  import { Pane, Splitpanes } from "svelte-splitpanes";
  import Map from "$lib/components/Map.svelte";
  import Tabs from "$lib/components/Tabs.svelte";
  import CoordinateSearch from "$lib/components/CoordinateSearch.svelte";

  const tabs = [
    { name: "Areas", value: "areas" },
    { name: "Coordinates", value: "coordinates" },
  ] as const;
  type Tabs = (typeof tabs)[number]["value"];

  let activeTab = $state<Tabs>("coordinates");

  async function handleSearchExtent(polygonWkt: string) {
    goto(`/search?wkt=${encodeURIComponent(polygonWkt)}`);
  }
</script>

<div class="page-container">
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
</div>

<style>
  .page-container {
    width: 100%;
    height: 100%;
  }

  .right-panel {
    display: grid;
    grid-template-rows: auto 1fr;
  }

  .panel-content {
    height: 100%;
  }
</style>
