<script lang="ts">
  import Badge from "$lib/components/Badge.svelte";
  import { type ImageMetadata } from "$lib/utils/types";

  interface Props {
    image: ImageMetadata;
    onHoverImage?: (image: ImageMetadata | null) => void;
  }

  const { image, onHoverImage }: Props = $props();

  const datetime = $derived(new Date(image.datetime_collected));
  const gsd = $derived(
    Math.max(
      image.ground_sample_distance_row,
      image.ground_sample_distance_row,
    ),
  );

  const formattedProps = $derived({
    href: `/view/${image.id}`,
    dateText: datetime.toISOString().slice(0, 10),
    timeText: datetime.toTimeString().slice(0, 8),
    coverage: Number.isFinite(image.coverage)
      ? `${(image.coverage * 100).toFixed(0)}%`
      : null,
    gsd_text: `${(gsd * 100).toFixed(2)}cm`,
    azimuth_angle: `${image.azimuth_angle.toFixed(0)}°`,
    look_angle: `${image.look_angle.toFixed(0)}°`,
  });
</script>

<a href={formattedProps.href} class="card-link">
  <div class="card">
    <img
      src={`/thumbnails/${image.filename}.png`}
      alt={image.filename}
      onmouseenter={() => onHoverImage?.(image)}
    />

    <div class="header">
      <div class="parameter-badges">
        {#if formattedProps.coverage !== null}
          <Badge tooltip="Coverage">
            {formattedProps.coverage}
          </Badge>
        {/if}
        {#if image.interpretation_rating !== null}
          <Badge tooltip="Image interpretation rating scale">
            {image.interpretation_rating}
          </Badge>
        {/if}
        <Badge tooltip="Ground sample distance">
          {formattedProps.gsd_text}
        </Badge>
        <Badge tooltip="Azimuth angle">
          {formattedProps.azimuth_angle}
        </Badge>
        <Badge tooltip="Look angle">
          {formattedProps.look_angle}
        </Badge>
      </div>
    </div>

    <div class="footer">
      {formattedProps.dateText}
      {formattedProps.timeText}
    </div>
  </div>
</a>

<style>
  .card-link {
    color: inherit;
  }

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
