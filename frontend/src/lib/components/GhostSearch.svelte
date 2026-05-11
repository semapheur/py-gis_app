<script lang="ts">
  import type { GhostCollection } from "$lib/contexts/annotate.svelte";
  import { getImageViewerOptions } from "$lib/contexts/common.svelte";
  import { getImageViewerController } from "$lib/contexts/ol_image_viewer/controller.svelte";
  import { toast } from "$lib/stores/toast.svelte";
  import Button from "$lib/components/Button.svelte";

  const imageViewer = getImageViewerController();
  const imageInfo = getImageViewerOptions();

  let future = $state<boolean>(false);
  let ghostData = $state<GhostCollection[]>([]);

  async function searchGhosts() {
    const payload = {
      wkt: imageViewer.getViewExtentWkt(),
      datetime_collected: imageInfo.imageInfo.datetime_collected,
      future: future,
    };

    const response = await fetch("/api/get-annotation-ghosts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      toast.error("Failed to fetch ghost annotations");
    }

    const result = await response.json();
    return result;
  }
</script>

<div class="ghost-search">
  <form>
    <Button
      onclick={() => searchGhosts().then((result) => (ghostData = result))}
      >Update extent</Button
    >
    <label>
      Show future
      <input type="checkbox" bind:checked={future} />
    </label>
  </form>
  <GhostBrowser data={ghostData} />
</div>

<style>
  .ghost-search {
  }
</style>
