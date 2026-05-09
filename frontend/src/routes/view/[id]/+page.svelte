<script lang="ts">
  import { untrack } from "svelte";
  import type { PageData } from "./$types";

  import { setAnnotateState } from "$lib/contexts/annotate.svelte";
  import { setImageViewerController } from "$lib/contexts/ol_image_viewer/controller.svelte";
  import { setImageViewerState } from "$lib/contexts/ol_image_viewer/state.svelte";
  import {
    setEquipmentOptions,
    setImageViewerOptions,
    type ImageViewerOptions,
  } from "$lib/contexts/common.svelte";

  import ImageViewer from "$lib/components/ImageViewer.svelte";

  let { data } = $props<{ data: PageData }>();

  let viewerOptions = $state<ImageViewerOptions>(
    untrack(() => ({
      imageInfo: data.imageInfo,
      radiometricParams: data.radiometricParams,
      annotations: data.annotations,
    })),
  );

  $effect(() => {
    viewerOptions.imageInfo = data.imageInfo;
    viewerOptions.radiometricParams = data.radiometricParams;
    viewerOptions.annotations = data.annotations;
  });

  setImageViewerOptions(viewerOptions);
  setEquipmentOptions(
    untrack(() => ({
      confidenceOptions: data.confidenceOptions.options,
      statusOptions: data.statusOptions.options,
    })),
  );
  setAnnotateState();
  setImageViewerController();
  setImageViewerState();
</script>

<ImageViewer />
