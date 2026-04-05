<script lang="ts">
  import MdiWeatherSunny from "@iconify-svelte/mdi/weather-sunny";
  import MdiWeatherNight from "@iconify-svelte/mdi/weather-night";
  import { theme } from "$lib/utils/theme.svelte";
</script>

<button
  onclick={() => theme.toggle()}
  title={theme.current === "dark"
    ? "Switch to light mode"
    : "Switch to dark mode"}
>
  {#if theme.current === "dark"}
    <MdiWeatherSunny width="var(--text-xl)" />
  {:else}
    <MdiWeatherNight width="var(--text-xl)" />
  {/if}
</button>

<style>
  button {
    all: unset;
    cursor: pointer;
  }
</style>
