<script lang="ts">
  import GeoJSON from "ol/format/GeoJSON";
  import EquipmentForm from "$lib/components/EquipmentForm.svelte";
  import ActivityForm from "$lib/components/ActivityForm.svelte";
  import KebabMenu from "$lib/components/KebabMenu.svelte";
  import { getImageViewerState } from "$lib/contexts/image_viewer.svelte";
  import { type EquipmentData } from "$lib/contexts/annotate.svelte";
  import { exportFile } from "$lib/utils/io";

  type BulkEquipmentPatch = Partial<EquipmentData>;

  const viewer = getImageViewerState();

  let selectedIndex = $state<number | null>(null);
  let validForm = $state<boolean>(true);
  let editData = $state<EquipmentData | null>(null);
  let bulkEdit = $state<boolean>(false);
  let bulkPatch = $state<BulkEquipmentPatch>({});
  let validBulkForm = $state(true);

  const selectedFeatures = $derived(viewer.selectedFeatures);
  const selectedFeature = $derived(
    selectedIndex !== null ? (selectedFeatures[selectedIndex] ?? null) : null,
  );
  const selectedType = $derived(selectedFeature?.get("type") ?? null);
  const selectedTypes = $derived(
    Array.from(new Set(selectedFeatures.map((f) => f.get("type")))),
  );
  const canBulkEdit = $derived(
    selectedFeatures.length > 1 && selectedTypes.length === 1,
  );
  const labels = $derived(
    selectedFeatures.map((f) => f.get("label")?.replace("\n", ", ")),
  );

  $effect(() => {
    if (!selectedFeature) {
      editData = null;
      selectedIndex = null;
      return;
    }

    editData = structuredClone(selectedFeature.get("data") ?? null);
  });

  $effect(() => {
    if (selectedIndex !== null && selectedIndex >= selectedFeatures.length) {
      selectedIndex = null;
    }
  });

  function commit(data: EquipmentData) {
    if (!selectedFeature) return;

    viewer.updateFeatureData(selectedFeature, data);
  }

  function saveEdits() {
    if (!editData || !validForm) return;

    commit(editData);
  }

  function deleteFeature() {
    if (!selectedFeature) return;

    viewer.deleteFeature(selectedFeature);
    selectedIndex = null;
    editData = null;
  }

  function exportFeaturesToGeoJson() {
    if (!selectedFeatures.length) return;

    const projection = viewer.projection;
    if (!projection) return;

    const format = new GeoJSON();

    const geojson = format.writeFeatures(selectedFeatures, {
      featureProjection: projection,
      dataProjection: "EPSG:4326",
    });
    const blob = new Blob([geojson], { type: "application/geo+json" });
    const fileName = `annotations_${new Date().toISOString().split("T")[0]}.json`;
    exportFile(blob, fileName);
  }

  function startBulkEdit() {
    if (!canBulkEdit) return;

    bulkEdit = true;
    selectedIndex = null;
    editData = null;
  }

  function applyBulkEdit() {
    if (!validBulkForm) return;

    for (const feature of selectedFeatures) {
      const data = feature.get("data") as EquipmentData;
      if (!data) continue;

      viewer.updateFeatureData(feature, {
        ...data,
        ...bulkPatch,
      });
    }

    bulkEdit = false;
    bulkPatch = {};
  }

  function bulkDelete() {
    const numFeatures = selectedFeatures.length;
    if (!numFeatures) return;

    const ok = confirm(
      `Delete ${numFeatures} selected annotation${numFeatures > 1 ? "s" : ""}?`,
    );
    if (!ok) return;

    viewer.bulkDeleteFeatures(selectedFeatures);
    selectedIndex = null;
    editData = null;
  }
</script>

{#if selectedFeatures.length > 0}
  <aside class="edit-sidebar">
    <header class="edit-header">
      <KebabMenu>
        <button role="menuitem" onclick={exportFeaturesToGeoJson}
          >Export to GeoJSON</button
        >
        {#if selectedFeatures.length > 1}
          <button
            role="menuitem"
            disabled={!canBulkEdit}
            onclick={startBulkEdit}>Bulk edit</button
          >
        {/if}
        <button role="menuitem" onclick={bulkDelete}>Bulk delete</button>
      </KebabMenu>
      <span class="edit-heading">Selected annotations</span>
    </header>
    <ol>
      {#each selectedFeatures as _, i}
        <li>
          <label>
            <input type="radio" value={i} bind:group={selectedIndex} />
            {labels[i]}
          </label>
        </li>
      {/each}
    </ol>
    {#if editData}
      {#key selectedIndex}
        {#if selectedType === "equipment"}
          <EquipmentForm
            value={editData}
            onchange={(v) => (editData = v)}
            onvalid={(v) => (validForm = v)}
          />
        {:else if selectedType === "activity"}
          <ActivityForm />
        {/if}
      {/key}
      <footer class="edit-footer">
        <button class="button-save" disabled={!validForm} onclick={saveEdits}>
          Save
        </button>
        <button class="button-delete" onclick={deleteFeature}> Delete </button>
      </footer>
    {:else if bulkEdit}
      <EquipmentForm
        value={bulkPatch}
        bulk
        onchange={(v) => (bulkPatch = v)}
        onvalid={(v) => (validBulkForm = v)}
      />

      <footer class="edit-footer">
        <button
          class="button-save"
          disabled={!validBulkForm}
          onclick={applyBulkEdit}
        >
          Apply to {selectedFeatures.length}
        </button>

        <button onclick={() => (bulkEdit = false)}> Cancel </button>
      </footer>
    {/if}
  </aside>
{/if}

<style>
  .edit-sidebar {
    height: 100%;
    width: clamp(200px, 25%, 600px);
    position: absolute;
    top: 0;
    right: 0;
    background: rgb(var(--color-primary));
    z-index: 1;
  }

  .edit-header {
    display: flex;
    gap: var(--size-md);
    border-bottom: 1px solid rgb(var(--color-text));
  }

  .edit-heading {
    margin: 0;
    font-size: var(--text-lg);
    font-weight: var(--font-bold);
  }

  .button-save {
    background: rgba(var(--color-positive) / 0.8);
  }

  .button-delete {
    background: rgba(var(--color-negative) / 0.8);
  }
</style>
