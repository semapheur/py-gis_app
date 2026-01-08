<script lang="ts">
  import Input from "$lib/components/Input.svelte";
  import { parseLatLon } from "$lib/utils/geo";

  let coordinate = $state<string>("");

  function submit() {
    const latlon = parseLatLon(coordinate);

    console.log(latlon);
  }
</script>

<div class="container">
  <form class="search-form">
    <Input
      label="Coordinate"
      value={coordinate}
      oninput={(v) => (coordinate = v)}
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
