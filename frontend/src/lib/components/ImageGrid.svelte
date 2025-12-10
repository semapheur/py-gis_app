<script lang="ts">
  import { type ImageMetadata } from "$lib/utils/types";
  import ImageCard from "$lib/components/ImageCard.svelte";

  export let images: ImageMetadata[] = [];
  export let onHoverImage: (image: ImageMetadata | null) => void;
</script>

{#if images.length === 0}
  <p>No images found</p>
{:else}
  <div class="image-grid">
    {#each images as image}
      <ImageCard {image} {onHoverImage} />
    {/each}
  </div>
{/if}

<style>
  .image-grid {
    width: 100%;
    height: 100%;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(min(100%, 200px), 1fr));
    grid-auto-rows: min-content;
    gap: var(--size-lg);
    padding: var(--size-lg);
    overflow-y: scroll;
  }
</style>
