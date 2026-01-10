<script lang="ts">
  import Input from "$lib/components/Input.svelte";
  import { parseCoordinates } from "$lib/utils/geo/coord";
  import { LatLon } from "$lib/utils/geo/latlon";

  let coordinates = $state<string>("");
  let history = $state<LatLon[]>([]);

  function submit() {
    const latlon = parseCoordinates(coordinates);

    history.push(latlon);
  }

  function deleteAt(index: number) {
    history = history.filter((_, i) => i !== index);
  }
</script>

<div class="container">
  <form class="search-form">
    <Input
      label="Coordinate"
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
          <button type="button">Z</button>
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
  }

  .search-form {
    display: flex;
    max-width: 100%;
    min-width: 0;
    gap: var(--size-sm);
  }
</style>
