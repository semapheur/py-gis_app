<script lang="ts">
  import type { Snippet } from "svelte";

  interface Props {
    label: string;
    children: Snippet;
  }

  let { children, label }: Props = $props();
  let showDropdown = $state<boolean>(false);

  let container: HTMLElement;

  function toggle(event: MouseEvent) {
    event.stopPropagation();
    showDropdown = !showDropdown;
  }

  function close() {
    showDropdown = false;
  }

  function handleClickOutside(event: MouseEvent) {
    if (!container.contains(event.target as Node)) {
      close();
    }
  }
</script>

<svelte:window onclick={handleClickOutside} />

<div class="dropdown-container" role="group" bind:this={container}>
  <button
    type="button"
    aria-haspopup="menu"
    aria-expanded={showDropdown}
    onclick={toggle}>{label}</button
  >
  {#if showDropdown}
    <div class="dropdown-menu" role="menu">
      {@render children()}
    </div>
  {/if}
</div>

<style>
  .dropdown-container {
    position: relative;
    display: inline-block;
  }

  .dropdown-menu {
    position: absolute;
    top: 100%;
    left: 0;
    z-index: 9;
  }
</style>
