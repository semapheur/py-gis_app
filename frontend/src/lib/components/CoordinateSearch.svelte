<script lang="ts">
  import Input from "$lib/components/Input.svelte";
  import { parseCoordinates } from "$lib/utils/geo/coord";

  let coordinates = $state<string>("");

  function submit() {
    const latlon = parseCoordinates(coordinates);

    console.log(latlon);
  }
</script>

<div class="container">
  <form class="search-form">
    <Input
      label="Coordinate"
      value={coordinates}
      oninput={(v) => (coordinates = v)}
    />
    <button onclick={submit}>Parse</button>
  </form>
</div>

<style>
  .container {
    display: grid;
    grid-template-rows: auto 1fr;
  }

  .search-form {
    display: flex;
    gap: var(--size-sm);
  }
</style>
