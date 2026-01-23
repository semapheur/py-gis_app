<script lang="ts">
  import Input from "$lib/components/Input.svelte";
  import { parseCoordinates } from "$lib/utils/geo/coord";
  import { LatLon } from "$lib/utils/geo/latlon";
  import { getMapLibreState } from "$lib/contexts/maplibre.svelte";

  let coordinates = $state<string>("");
  let history = $state<LatLon[]>([]);

  const mapLibre = getMapLibreState();

  function submit() {
    const latlon = parseCoordinates(coordinates);
    history.push(latlon);
  }

  function deleteAt(index: number) {
    history = history.filter((_, i) => i !== index);
  }

  function zoomTo(latlon: LatLon) {
    mapLibre?.zoomToLatLon(latlon.latitude, latlon.longitude);
  }
</script>

<div class="container">
  <form class="search-form">
    <Input
      placeholder="Coordinate"
      value={coordinates}
      fieldSizing="content"
      oninput={(v) => (coordinates = v)}
    />
    <button type="button" onclick={submit}>Parse</button>
  </form>
  {#if history.length > 0}
    <nav>
      {#each history as latlon, i}
        <div class="coordinate-row">
          <button type="button" onclick={() => zoomTo(latlon)}>Z</button>
          <a href="/search?wkt=${encodeURIComponent(latlon.toWkt())}"
            >{latlon.print("dms", 0)}</a
          >
          <button type="button" onclick={() => deleteAt(i)}>Delete</button>
        </div>
      {/each}
    </nav>
  {/if}
</div>

<style>
  .container {
    display: grid;
    grid-template-rows: auto 1fr;
    padding: var(--size-md);
    gap: var(--size-md);
  }

  .search-form {
    display: flex;
    max-width: 100%;
    min-width: 0;
    gap: var(--size-sm);
    padding-bottom: var(--size-md);
    border-bottom: 1px solid rgb(var(--color-accent));
  }
</style>
