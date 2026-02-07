<script lang="ts">
  import Input from "./Input.svelte";
  import { getMapLibreState } from "$lib/contexts/maplibre.svelte";

  interface AreaInfo {
    id: string;
    name: string;
    geometry: GeoJSON.Polygon;
  }

  let areas = $state<AreaInfo[]>([]);
  let polygonLinks = $derived(
    areas.map(({ id, name, geometry }) => ({
      label: name,
      geometry,
      href: `/search?area=${id}`,
    })),
  );

  const mapLibre = getMapLibreState();

  $effect(() => {
    fetch("/api/get-areas")
      .then((r) => r.json())
      .then((data: AreaInfo[]) => {
        areas = data;
      })
      .catch((error) => {
        console.error("Failed to fetch areas", error);
      });
  });

  $effect(() => {
    mapLibre.setPolygonLinks(polygonLinks);
  });
</script>

<div class="area-browser">
  <form class="area-search">
    <Input placeholder="Name" />
    <button>Search</button>
  </form>
  <nav>
    {#each areas as area}
      <div class="area-row">
        <button
          onclick={() => mapLibre.fitToPolygon(area.geometry.coordinates[0])}
          >Z</button
        >
        <span>{area.name}</span>
        <a href={`/area/${area.id}`}>E</a>
      </div>
    {/each}
  </nav>
</div>

<style>
  .area-search {
    display: flex;
  }

  .area-row {
    display: flex;
  }
</style>
