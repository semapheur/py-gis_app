<script lang="ts">
  import { untrack } from "svelte";
  import Button from "$lib/components/Button.svelte";
  import LinkButton from "$lib/components/LinkButton.svelte";
  import { getImageViewerController } from "$lib/contexts/ol_image_viewer/controller.svelte";
  import type {
    AnnotationBaseInfo,
    GhostCollection,
  } from "$lib/contexts/annotate.svelte";
  import { type ColumnDefinition } from "$lib/utils/types";
  import { formatDatetime } from "$lib/utils/date";
  import Table from "$lib/components/Table.svelte";

  interface Props {
    data: GhostCollection[];
  }

  let { data }: Props = $props();

  const imageViewer = getImageViewerController();

  const columns: ColumnDefinition[] = [
    {
      id: "count",
      label: "Count",
      sortable: true,
    },
    {
      id: "label",
      label: "Equipment",
      sortable: true,
      filterable: true,
    },
  ];

  let equipmentList = $derived(
    untrack(() => data).map((gc) => aggregateEquipment(gc.annotations)),
  );

  function aggregateEquipment(annotations: AnnotationBaseInfo[]) {
    const equipmentCount: Record<string, number> = {};

    for (const a of annotations) {
      const label = a.data.equipment?.label;
      if (!label) continue;

      equipmentCount[label] ??= 0;
      equipmentCount[label]++;
    }

    const result = [];
    for (const [label, count] of Object.entries(equipmentCount)) {
      result.push({ count: count, label: label });
    }
    return result.sort((a, b) => a.label.localeCompare(b.label));
  }
</script>

<div class="ghost-browser"></div>
{#each data as ghostRow, i}
  <div class="ghost-row">
    <header>
      <span>{formatDatetime(ghostRow.datetime)}</span>
      <LinkButton href={`/view/${ghostRow.image_id}`}>Open image</LinkButton>
      <Button onclick={() => imageViewer.addGhosts(ghostRow.annotations)}
        >Add ghosts</Button
      >
    </header>
    <Table {columns} data={equipmentList[i]} />
  </div>
{/each}

<style></style>
