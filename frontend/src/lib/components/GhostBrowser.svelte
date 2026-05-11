<script lang="ts">
  import { untrack } from "svelte";
  import type {
    AnnotationBaseInfo,
    GhostCollection,
  } from "$lib/contexts/annotate.svelte";
  import { formatDatetime } from "$lib/utils/date";
  import Button from "$lib/components/Button.svelte";
  import LinkButton from "$lib/components/LinkButton.svelte";
  import { getImageViewerController } from "$lib/contexts/ol_image_viewer/controller.svelte";

  interface Props {
    data: GhostCollection[];
  }

  const { data }: Props = $props();

  const imageViewer = getImageViewerController();

  let equipmentList = $derived(
    untrack(() => data).map((gc) => aggregateEquipment(gc.annotations)),
  );

  function aggregateEquipment(annotations: AnnotationBaseInfo[]) {
    const equipmentCount: Record<string, number> = {};

    for (const a of annotations) {
      equipmentCount[a.label] ??= 0;
      equipmentCount[a.label]++;
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
    <ul>
      {#each equipmentList[i] as countRow}
        <li>
          {`${countRow.count}x ${countRow.label}`}
        </li>
      {/each}
    </ul>
  </div>
{/each}

<style></style>
