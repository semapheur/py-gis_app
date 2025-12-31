<script lang="ts">
  import { getImageViewerState } from "$lib/states/image_viewer.svelte";
  import CollapsibleList from "$lib/components/CollapsibleList.svelte";
  import type {
    EquipmentConfidence,
    EquipmentData,
    EquipmentStatus,
  } from "$lib/states/annotate.svelte";

  const viewer = getImageViewerState();

  interface StatusCount {
    total: number;
    confidences: Record<EquipmentConfidence, number>;
  }

  interface EquipmentCount {
    total: number;
    statuses: Record<EquipmentStatus, StatusCount>;
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
</script>

<section class="equipment-summary">
  <span>Equipment summary</span>
  {#if Object.keys(summary).length === 0}
    <p>No equipment annotations</p>
  {:else}
    <ul class="summary-list">
      {#each Object.entries(summary) as [id, entry]}
        <!-- Level 1: Equipment -->
        <CollapsibleList {id}>
          {#snippet header()}
            <span>{entry.total}x {id}</span>
          {/snippet}
          {#snippet children()}
            {#each Object.entries(entry.statuses) as [status, s]}
              {@const statusKey = `${id}-${status}`}
              <!-- Level 2: Status -->
              <CollapsibleList id={statusKey}>
                {#snippet header()}
                  <span>{s.total}x {status}</span>
                {/snippet}
                {#snippet children()}
                  <!-- Level 3: Confidence (Leaf items) -->
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

  .summary-list {
    padding-left: var(--size-md);
  }

  .inner-item {
    margin-left: var(--arrow-size);
    padding-left: var(--arrow-gap);
  }
</style>
