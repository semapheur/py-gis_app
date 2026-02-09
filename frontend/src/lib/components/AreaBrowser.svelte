<script lang="ts">
  import Input from "$lib/components/Input.svelte";
  import { getMapLibreState } from "$lib/contexts/maplibre.svelte";
  import LinkButton from "$lib/components/LinkButton.svelte";

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

  async function deleteArea(id: string) {
    const response = await fetch("/api/delete-areas", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ delete: [id] }),
    });

    if (!response.ok) {
      console.error(`Failed to delete area: ${id}`);
      return;
    }

    areas = areas.filter((area) => area.id !== id);
  }
</script>

<div class="area-browser">
  <form class="area-search">
    <LinkButton href="/area">Add</LinkButton>
    <Input placeholder="Name" />
  </form>
  <nav>
    {#each areas as area (area.id)}
      <div class="area-row">
        <button
          onclick={() => mapLibre.fitToPolygon(area.geometry.coordinates[0])}
          >Z</button
        >
        <span>{area.name}</span>
        <a href={`/area/${area.id}`}>E</a>
        <button onclick={() => deleteArea(area.id)}>D</button>
      </div>
    {/each}
  </nav>
</div>

<style>
  .area-browser {
    display: grid;
    grid-template-rows: auto 1fr;
    padding: var(--size-md);
    gap: var(--size-md);
  }

  .area-search {
    display: flex;
    gap: var(--size-md);
    padding-bottom: var(--size-md);
    border-bottom: 1px solid oklch(var(--color-accent));
  }

  .area-row {
    display: flex;
    gap: var(--size-md);
    padding: var(--size-md);
    border-bottom: 1px solid oklch(var(--color-accent));
  }
</style>
