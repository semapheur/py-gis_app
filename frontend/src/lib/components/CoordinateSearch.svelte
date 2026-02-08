<script lang="ts">
  import Input from "$lib/components/Input.svelte";
  import InputGroup from "$lib/components/InputGroup.svelte";
  import Button from "$lib/components/Button.svelte";
  import LinkButton from "$lib/components/LinkButton.svelte";
  import { parseCoordinates } from "$lib/utils/geo/coord";
  import { LatLon } from "$lib/utils/geo/latlon";
  import { getMapLibreState } from "$lib/contexts/maplibre.svelte";

  let coordinates = $state<string>("");
  let history = $state<Record<string, LatLon>>({});

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

  function zoomTo(latlon: LatLon) {
    mapLibre?.zoomToLatLon(latlon.latitude, latlon.longitude);
  }
</script>

<div class="coordinate-search">
  <form class="coordinate-parse">
    <Input
      placeholder="Coordinate"
      value={coordinates}
      fieldSizing="content"
      oninput={(v) => (coordinates = v)}
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
        {#each Object.entries(history) as [input, latlon]}
          <tr>
            <td>
              <button type="button" onclick={() => zoomTo(latlon)}>Z</button>
            </td>
            <td>
              <LinkButton
                href="/search?wkt=${encodeURIComponent(latlon.toWkt())}"
                >Search</LinkButton
              >
            </td>
            <td>{latlon.print("dms", 0)}</td>
            <td>{input}</td>
            <td>
              <Button type="button" onclick={() => deleteAt(input)}
                >Delete</Button
              >
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
    border-bottom: 1px solid oklch(var(--color-accent));
  }
</style>
