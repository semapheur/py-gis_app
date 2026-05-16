<script lang="ts">
  import MdiMapMarkerOutline from "@iconify-svelte/mdi/map-marker-outline";
  import MdiSearch from "@iconify-svelte/mdi/search";
  import Input from "$lib/components/Input.svelte";
  import Button from "$lib/components/Button.svelte";
  import LinkButton from "$lib/components/LinkButton.svelte";
  import { parseCoordinates, type Coordinate } from "$lib/utils/geo/coord";
  import { LatLon } from "$lib/utils/geo/latlon";
  import { MGRS } from "$lib/utils/geo/mgrs";
  import { UTM } from "$lib/utils/geo/utm";
  import { getMapLibreState } from "$lib/contexts/ml_map.svelte";

  let coordinates = $state<string>("");
  let history = $state<Record<string, Coordinate>>({});

  const mapLibre = getMapLibreState();

  function submit() {
    if (coordinates in history) return;

    const latlon = parseCoordinates(coordinates);
    history[coordinates] = latlon;
  }

  function deleteAt(key: string) {
    const { [key]: _, ...rest } = history;
    history = rest;
  }

  function zoomToPoint(coord: Coordinate) {
    let latlon: LatLon | null = null;

    if (coord instanceof MGRS) {
      latlon = coord.toLatLon();
    } else if (coord instanceof UTM) {
      latlon = coord.toLatLon();
    } else {
      latlon = coord;
    }

    mapLibre?.zoomToPoint("zoom-point", latlon.toGeoJson());
  }

  function zoomToGrid(coord: MGRS) {
    const gridPolygon = coord.getGridPolygon();
    mapLibre?.zoomToPolygon("zoom-polygon", gridPolygon, { duration: 1000 });
  }

  function coordinateToWktPoint(coord: Coordinate) {
    let latlon: LatLon | null = null;

    if (coord instanceof MGRS) {
      latlon = coord.toLatLon();
    } else if (coord instanceof UTM) {
      latlon = coord.toLatLon();
    } else {
      latlon = coord;
    }

    return latlon.toWkt();
  }

  function printCoordinate(coord: Coordinate) {
    let latlon: LatLon | null = null;

    if (coord instanceof MGRS) {
      latlon = coord.toLatLon();
    } else if (coord instanceof UTM) {
      latlon = coord.toLatLon();
    } else {
      latlon = coord;
    }

    return latlon.print("dms", 0);
  }
</script>

<div class="coordinate-search">
  <form class="coordinate-parse">
    <Input
      placeholder="Coordinate"
      bind:value={coordinates}
      fieldSizing="content"
    />
    <Button type="button" onclick={submit}>Parse</Button>
  </form>
  {#if Object.keys(history).length > 0}
    <table>
      <thead>
        <tr>
          <th>Zoom</th>
          <th>Search</th>
          <th>Lat/lon</th>
          <th>Input</th>
          <th>Delete</th>
        </tr>
      </thead>
      <tbody>
        {#each Object.entries(history) as [input, coord]}
          <tr>
            <td>
              <div class="cell-stack">
                <Button
                  type="button"
                  onclick={() => zoomToPoint(coord)}
                  title="Zoom to point"
                >
                  <MdiMapMarkerOutline width="1rem" />
                  <span>Point</span></Button
                >
                {#if coord instanceof MGRS}
                  <Button
                    type="button"
                    onclick={() => zoomToGrid(coord)}
                    title="Zoom to grid"
                  >
                    <MdiMapMarkerOutline width="1rem" />
                    <span>Grid</span></Button
                  >
                {/if}
              </div>
            </td>
            <td>
              <div class="cell-stack">
                <LinkButton
                  href={`/search?wkt=${encodeURIComponent(
                    coordinateToWktPoint(coord),
                  )}`}
                >
                  <MdiSearch width="1rem" />
                  <span>Point</span></LinkButton
                >
                {#if coord instanceof MGRS}
                  <LinkButton
                    href={`/search?wkt=${encodeURIComponent(coord.gridToWkt())}`}
                  >
                    <MdiSearch width="1rem" />
                    <span>Grid</span></LinkButton
                  >
                {/if}
              </div>
            </td>
            <td>{printCoordinate(coord)}</td>
            <td>{input}</td>
            <td>
              <div class="cell-centered">
                <button
                  class="button-delete"
                  type="button"
                  onclick={() => deleteAt(input)}
                >
                  ✕
                </button>
              </div>
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  {/if}
</div>

<style>
  .coordinate-search {
    display: grid;
    grid-template-rows: auto 1fr;
    padding: var(--size-md);
    gap: var(--size-md);
  }

  .coordinate-parse {
    display: flex;
    max-width: 100%;
    min-width: 0;
    gap: var(--size-sm);
    padding-bottom: var(--size-md);
    border-bottom: 1px solid oklch(var(--color-secondary-accent));
  }

  .cell-stack {
    display: flex;
    flex-direction: column;
    gap: var(--size-sm);
  }

  .cell-centered {
    text-align: center;
  }

  .button-delete {
    all: unset;
    cursor: pointer;

    &:hover {
      color: red;
    }
  }
</style>
