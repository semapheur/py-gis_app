<script lang="ts">
  import { untrack } from "svelte";
  import type { PageData } from "./$types";

  import { setAnnotateState } from "$lib/contexts/annotate.svelte";
  import { setImageViewerController } from "$lib/contexts/ol_image_viewer/controller.svelte";
  import { setImageViewerState } from "$lib/contexts/ol_image_viewer/state.svelte";
  import {
    setEquipmentOptions,
    setImageViewerOptions,
    type EquipmentOptions,
    type ImageViewerOptions,
  } from "$lib/contexts/common.svelte";

  import ImageViewer from "$lib/components/ImageViewer.svelte";
  import { equipmentAttributeTables } from "$lib/schemas/equipment_annotation";

  let { data } = $props<{ data: PageData }>();

  let viewerOptions = $state<ImageViewerOptions>(
    untrack(() => ({
      imageInfo: data.imageInfo,
      radiometricParams: data.radiometricParams,
      annotations: data.annotations,
      areas: data.areas,
    })),
  );

  $effect(() => {
    viewerOptions.imageInfo = data.imageInfo;
    viewerOptions.radiometricParams = data.radiometricParams;
    viewerOptions.annotations = data.annotations;
    viewerOptions.areas = data.areas;
  });

  setImageViewerOptions(viewerOptions);
  setEquipmentOptions(
    Object.fromEntries(
      Object.keys(equipmentAttributeTables).map((key) => [
        key,
        data[key].options,
      ]),
    ) as EquipmentOptions,
  );
  setAnnotateState();
  setImageViewerController();
  setImageViewerState();
</script>

<ImageViewer />
