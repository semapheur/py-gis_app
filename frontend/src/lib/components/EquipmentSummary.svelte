<script lang="ts">
  import GeoJSON from "ol/format/GeoJSON";
  import { getImageViewerState } from "$lib/contexts/image_viewer.svelte";
  import KebabMenu from "$lib/components/KebabMenu.svelte";
  import CollapsibleList from "$lib/components/CollapsibleList.svelte";
  import type { EquipmentData } from "$lib/contexts/annotate.svelte";
  import { exportFile } from "$lib/utils/io";

  const viewer = getImageViewerState();

  interface StatusCount {
    total: number;
    confidences: Record<string, number>;
  }

  interface EquipmentCount {
    total: number;
    statuses: Record<string, StatusCount>;
  }

  type Summary = Record<string, EquipmentCount>;

  const equipmentFeatures = $derived(viewer.equipmentFeatures);

  const summary = $derived.by<Summary>(() => {
    const aggregate: Summary = {};

    for (const feature of equipmentFeatures) {
      const data = feature.get("data") as EquipmentData | null;
      if (!data) continue;

      const { id, status, confidence } = data;
      if (!id) continue;

      aggregate[id] ??= { total: 0, statuses: {} };
      aggregate[id].total++;

      aggregate[id].statuses[status] ??= {
        total: 0,
        confidences: {},
      };
      aggregate[id].statuses[status].total++;

      aggregate[id].statuses[status].confidences[confidence] ??= 0;
      aggregate[id].statuses[status].confidences[confidence]++;
    }

    return aggregate;
  });

  function exportFeaturesToGeoJson() {
    if (!equipmentFeatures.length) return;

    const projection = viewer.projection;
    if (!projection) return;

    const format = new GeoJSON();

    const geojson = format.writeFeatures(equipmentFeatures, {
      featureProjection: projection,
      dataProjection: "EPSG:4326",
    });
    const blob = new Blob([geojson], { type: "application/geo+json" });

    const fileName = `equipment_${new Date().toISOString().split("T")[0]}.json`;
    exportFile(blob, fileName);
  }
</script>

<section class="equipment-summary">
  <header class="header">
    <KebabMenu>
      <button role="menuitem" onclick={exportFeaturesToGeoJson}
        >Export to GeoJSON</button
      >
    </KebabMenu>
    <span class="heading">Equipment count</span>
  </header>
  {#if Object.keys(summary).length === 0}
    <p>No equipment annotations</p>
  {:else}
    <ul class="summary-list">
      {#each Object.entries(summary) as [id, entry]}
        <CollapsibleList {id}>
          {#snippet header()}
            <span>{entry.total}x {id}</span>
          {/snippet}
          {#snippet children()}
            {#each Object.entries(entry.statuses) as [status, s]}
              {@const statusKey = `${id}-${status}`}
              <CollapsibleList id={statusKey}>
                {#snippet header()}
                  <span>{s.total}x {status}</span>
                {/snippet}
                {#snippet children()}
                  {#each Object.entries(s.confidences) as [conf, count]}
                    <li class="inner-item">{count}x {conf}</li>
                  {/each}
                {/snippet}
              </CollapsibleList>
            {/each}
          {/snippet}
        </CollapsibleList>
      {/each}
    </ul>
  {/if}
</section>

<style>
  :root {
    --arrow-size: 0.4rem;
    --arrow-gap: 0.5rem;
  }

  ul {
    list-style: none;
    margin: 0;
    padding: 0;
  }

  .header {
    display: flex;
    gap: var(--size-md);
  }

  .heading {
    font-size: var(--text-lg);
    font-weight: var(--font-bold);
  }

  .summary-list {
    padding-left: var(--size-md);
  }

  .inner-item {
    margin-left: var(--arrow-size);
    padding-left: var(--arrow-gap);
  }
</style>
