<script lang="ts">
  import { decode, encode } from "@msgpack/msgpack";
  import MdiDeleteOutline from "@iconify-svelte/mdi/delete-outline";
  import MdiEditOutline from "@iconify-svelte/mdi/edit-outline";
  import MdiMapMarkerOutline from "@iconify-svelte/mdi/map-marker-outline";
  import { getMapLibreState } from "$lib/contexts/ml_map.svelte";
  import Input from "$lib/components/Input.svelte";
  import ButtonIcon from "$lib/components/ButtonIcon.svelte";
  import LinkButton from "$lib/components/LinkButton.svelte";
  import LinkIcon from "$lib/components/LinkIcon.svelte";

  import { type AreaInfo } from "$lib/contexts/area_editor.svelte";

  let areas = $state<AreaInfo[]>([]);
  let searchQuery = $state<string>("");
  let newAreaHref = $state("/areas/new");

  let filteredAreas = $derived.by(() => {
    const q = searchQuery.trim().toLowerCase();
    if (!q) return areas;

    return areas.filter(
      (area) =>
        area.name.toLowerCase().includes(q) ||
        area.description?.toLowerCase().includes(q),
    );
  });

  let polygonLinks = $derived(
    filteredAreas.map(({ id, name, geometry }) => ({
      label: name,
      geometry,
      href: `/search?area=${id}`,
    })),
  );

  const mapLibre = getMapLibreState();

  $effect(() => {
    fetch("/api/get-areas")
      .then((r) => r.arrayBuffer())
      .then((buffer) => {
        areas = decode(buffer) as AreaInfo[];
      })
      .catch((error) => {
        console.error("Failed to fetch areas", error);
      });
  });

  $effect(() => {
    mapLibre.setPolygonLinks(polygonLinks);
  });

  $effect(() => {
    const bbox = mapLibre.getCurrentBbox();
    if (bbox) {
      `/areas/new?bbox=${encodeURIComponent(bbox.join(","))}`;
    }

    const cleanup = mapLibre.onMoveEnd((wkt) => {
      newAreaHref = `/areas/new?bbox=${encodeURIComponent(wkt)}`;
    });

    return cleanup;
  });

  async function deleteArea(id: string) {
    const ok = confirm("Delete area?");
    if (!ok) return;

    const response = await fetch("/api/delete-areas", {
      method: "POST",
      headers: { "Content-Type": "application/msgpack" },
      body: encode({ delete: [id] }),
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
    <LinkButton href={newAreaHref}>Add</LinkButton>
    <Input placeholder="Search" bind:value={searchQuery} />
  </form>
  <nav>
    {#each filteredAreas as area (area.id)}
      <div class="area-row">
        <ButtonIcon
          onclick={() => mapLibre.fitToPolygon(area.geometry.coordinates[0])}
          title="Zoom to area"
          ><MdiMapMarkerOutline width="var(--text-lg)" /></ButtonIcon
        >
        <a href={`/search?area=${area.id}`} class="area-text">
          <span class="area-name">{area.name}</span>
          <span class="area-description">{area.description}</span>
        </a>
        <LinkIcon
          href={`/areas/${area.id}`}
          tooltip="Edit area"
          tooltipPlacement="left"
          ><MdiEditOutline width="var(--text-lg)" /></LinkIcon
        >
        <ButtonIcon onclick={() => deleteArea(area.id)} title="Delete area"
          ><MdiDeleteOutline width="var(--text-lg)" /></ButtonIcon
        >
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
    border-bottom: 1px solid oklch(var(--color-secondary-accent));
  }

  .area-row {
    display: grid;
    grid-template-columns: auto 1fr auto auto;
    gap: var(--size-md);
    padding: var(--size-md);
    width: 100%;
    border-bottom: 1px solid oklch(var(--color-secondary-accent));
  }

  .area-text {
    color: inherit;
    text-decoration: none;
    display: flex;
    flex-direction: column;
  }

  .area-description {
    font-size: var(--text-sm);
    opacity: oklch(var(--color-text) / 0.7);
  }
</style>
