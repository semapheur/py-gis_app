<script lang="ts">
  import Feature from "ol/Feature";

  import type { PageData } from "./$types";
  import ImageViewer from "$lib/components/ImageViewer.svelte";
  import AnnotateDialog from "$lib/components/AnnotateDialog.svelte";
  import AnnotationEdit from "$lib/components/AnnotationEdit.svelte";
  import type {
    AnnotateForm,
    EquipmentData,
    DrawConfig,
    ImageMetadata,
    RadiometricParams,
  } from "$lib/utils/types";

  let { data } = $props<{ data: PageData }>();
  const image: ImageMetadata = $derived(data.image);
  const radiometricParams: RadiometricParams = $derived(data.radiometricParams);

  let annotateOpen = $state(false);
  let drawConfig = $state<DrawConfig>({
    enabled: false,
    layer: "equipment",
    geometry: "Point",
  });
  let formData = $state<EquipmentData | null>(null);
  let selectedAnnotations = $state<Feature[]>([]);
  let imageViewerRef = $state<ImageViewer | null>(null);

  function handleDelete(feature: Feature) {
    if (!imageViewerRef) return;

    imageViewerRef.deleteFeature(feature);

    selectedAnnotations = selectedAnnotations.filter((f) => f !== feature);
  }
</script>

<div class="container">
  {#if !annotateOpen}
    <button class="toggle-form" onclick={() => (annotateOpen = !annotateOpen)}>
      Add
    </button>
  {/if}
  <AnnotateDialog bind:open={annotateOpen} bind:drawConfig bind:formData />
  <ImageViewer
    bind:this={imageViewerRef}
    {image}
    {radiometricParams}
    {drawConfig}
    {formData}
    bind:selectedFeatures={selectedAnnotations}
  />
  <AnnotationEdit {selectedAnnotations} onDelete={handleDelete} />
</div>

<style>
  .container {
    position: relative;
    width: 100%;
    height: 100%;
  }

  .toggle-form {
    position: absolute;
    left: var(--size-lg);
    bottom: var(--size-lg);
    z-index: 1;
  }
</style>
