<script lang="ts">
  import { goto } from "$app/navigation";
  import SplitPanes from "$lib/components/SplitPanes.svelte";
  import Map from "$lib/components/Map.svelte";
  import Tabs from "$lib/components/Tabs.svelte";
  import CoordinateSearch from "$lib/components/CoordinateSearch.svelte";

  import { setMapLibreState } from "$lib/contexts/ml_map.svelte";
  import AreaBrowser from "$lib/components/AreaBrowser.svelte";

  const tabs = [
    { name: "Areas", value: "areas" },
    { name: "Coordinates", value: "coordinates" },
  ] as const;
  type Tabs = (typeof tabs)[number]["value"];

  let activeTab = $state<Tabs>("areas");

  setMapLibreState();

  async function handleSearchExtent(polygonWkt: string) {
    goto(`/search?wkt=${encodeURIComponent(polygonWkt)}`);
  }
</script>

{#snippet leftPane()}
  <Map showSearchButton syncBbox onSearchExtent={handleSearchExtent} />
{/snippet}

{#snippet rightPane()}
  <div class="right-panel">
    <header class="panel-header">
      <Tabs
        {tabs}
        selected={activeTab}
        onselect={(tab) => (activeTab = tab as Tabs)}
      />
    </header>
    <main class="panel-content">
      {#if activeTab === "areas"}
        <AreaBrowser />
      {:else if activeTab === "coordinates"}
        <CoordinateSearch />
      {/if}
    </main>
  </div>
{/snippet}

<SplitPanes panes={[leftPane, rightPane]} />

<style>
  .right-panel {
    display: grid;
    grid-template-rows: auto 1fr;
    padding: var(--size-md);
    background-color: oklch(var(--color-primary));
  }

  .panel-content {
    height: 100%;
  }
</style>
