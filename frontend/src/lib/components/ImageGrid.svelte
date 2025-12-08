<script lang="ts">
  import { type Image } from "$lib/utils/types";

  export let images: Image[] = [];
</script>

{#if images.length === 0}
  <p>No images found</p>
{:else}
  <div class="image-grid">
    {#each images as img}
      <div class="thumbnail">
        <img src={`/thumbnails/${img.filename}.png`} alt={img.filename} />

        <div class="metadata">
          <span class="datetime-collected"
            >{new Date(img.datetime_collected).toLocaleDateString()}</span
          >
          <span class="sensor-type">{img.sensor_type}</span>
          <span class="look-angle">{img.look_angle}</span>
          <span class="azimuth-angle">{img.azimuth_angle}</span>
          <span class="gsd"
            >{Math.max(
              img.ground_sample_distance_row,
              img.ground_sample_distance_col,
            )}</span
          >
          <span class="interpretation-rating">{img.interpretation_raing}</span>
        </div>
      </div>
    {/each}
  </div>
{/if}

<style>
  .image-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: 1rem;
  }

  .thumbnail {
    position: relative;

    & img {
      width: 100%;
      aspect-ratio: 1/1;
      object-fit: cover;
    }

    & span {
      position: absolute;
    }
  }

  .datetime-collected {
    top: 1rem;
    left: 1rem;
  }

  .sensor-type {
    top: 2rem;
    left: 1rem;
  }

  .look-angle {
    top: 1rem;
    right: 1rem;
  }

  .azimuth-angle {
    top: 2rem;
    right: 1rem;
  }

  .gsd {
    top: 3rem;
    right: 1rem;
  }

  .interpretation-rating {
    top: 4rem;
    right: 1rem;
  }
</style>
