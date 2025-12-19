<script lang="ts">
  import { type ImageMetadata } from "$lib/utils/types";

  export let image: ImageMetadata;
  export let onHoverImage: (image: ImageMetadata | null) => void;

  const href = `/view/${image.id}`;

  const datetime = new Date(image.datetime_collected);
  const dateText = datetime.toISOString().slice(0, 10);
  const timeText = datetime.toTimeString().slice(0, 8);

  const coverage = `${(image.coverage * 100).toFixed(0)}%`;
  const gsd = Math.max(
    image.ground_sample_distance_row,
    image.ground_sample_distance_row,
  );
  const gsd_text = `${(gsd * 100).toFixed(2)}cm`;
  const azimuth_angle = `${image.azimuth_angle.toFixed(0)}°`;
  const look_angle = `${image.look_angle.toFixed(0)}°`;
</script>

<a {href} class="card-link">
  <div class="card">
    <img
      src={`/thumbnails/${image.filename}.png`}
      alt={image.filename}
      onmouseenter={() => onHoverImage(image)}
    />

    <div class="header">
      <div class="parameter-badges">
        <span class="badge">
          {coverage}
        </span>
        <span class="badge">
          {image.interpretation_rating}
        </span>
        <span class="badge">
          {gsd_text}
        </span>
        <span class="badge">
          {azimuth_angle}
        </span>
        <span class="badge">
          {look_angle}
        </span>
      </div>
    </div>

    <div class="footer">
      {dateText}
      {timeText}
    </div>
  </div>
</a>

<style>
  .card {
    position: relative;
    width: 100%;
    border-radius: var(--size-sm);
    overflow: hidden;
  }

  .header {
    position: absolute;
    top: 0;
    display: flex;
    width: 100%;
  }

  .parameter-badges {
    width: 80%;
    display: flex;
    gap: var(--size-sm);
    padding: var(--size-sm);
  }

  .badge {
    background-color: gray;
    font-size: var(--text-xs);
    border-radius: var(--size-sm);
    padding: 0 var(--size-sm);
  }

  .footer {
    position: absolute;
    bottom: 0;
    width: 100%;
    background: rgba(0, 0, 0, 0.65);
    color: white;
    text-align: center;
  }

  img {
    width: 100%;
    aspect-ratio: 16/9;
    object-fit: cover;
    display: block;
    filter: brightness(5);
  }
</style>
