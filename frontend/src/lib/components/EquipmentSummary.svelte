<script lang="ts">
  import { getImageViewerState } from "$lib/states/image_viewer.svelte";
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

  let openIds = $state<Set<string>>(new Set());
  let openStatuses = $state<Set<string>>(new Set());

  function toggle(set: Set<string>, key: string) {
    set.has(key) ? set.delete(key) : set.add(key);
    return new Set(set);
  }
</script>

<section class="equipment-summary">
  <span>Equipment summary</span>

  {#if Object.keys(summary).length === 0}
    <p>No equipment annotations</p>
  {:else}
    <ul>
      {#each Object.entries(summary) as [id, entry]}
        <li>
          <button onclick={() => toggle(openIds, id)}>
            {openIds.has(id) ? "▾" : "▸"}
            <strong>{id}</strong> ({entry.total})
          </button>
        </li>

        {#if openIds.has(id)}
          <ul>
            {#each Object.entries(entry.statuses) as [status, s]}
              {@const statusKey = `${id}:${status}`}
              <li>
                <button onclick={() => toggle(openStatuses, statusKey)}
                  >>
                  {openStatuses.has(statusKey) ? "▾" : "▸"}
                  {status} ({s.total})
                </button>
              </li>

              {#if openStatuses.has(statusKey)}
                <ul>
                  {#each Object.entries(s.confidences) as [conf, count]}
                    <li>
                      {conf}: {count}
                    </li>
                  {/each}
                </ul>
              {/if}
            {/each}
          </ul>
        {/if}
      {/each}
    </ul>
  {/if}
</section>
