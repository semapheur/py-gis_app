<script lang="ts">
  import type { PageData } from "./$types";

  import { setAnnotateState } from "$lib/contexts/annotate.svelte";
  import { setImageViewerController } from "$lib/contexts/image_viewer/controller.svelte";
  import { setImageViewerState } from "$lib/contexts/image_viewer/state.svelte";
  import {
    setEquipmentOptions,
    setImageViewerOptions,
    type ImageViewerOptions,
  } from "$lib/contexts/context.svelte";

  import ImageViewer from "$lib/components/ImageViewer.svelte";

  let { data } = $props<{ data: PageData }>();

  let viewerOptions = $derived<ImageViewerOptions>({
    imageInfo: data.imageInfo,
    radiometricParams: data.radiometricParams,
    annotations: data.annotations,
  });

  $effect(() => {
    setImageViewerOptions(viewerOptions);
  });

  setEquipmentOptions({
    confidenceOptions: data.confidenceOptions.options,
    statusOptions: data.statusOptions.options,
  });
  setAnnotateState();
  setImageViewerController();
  setImageViewerState();
</script>

<ImageViewer />
