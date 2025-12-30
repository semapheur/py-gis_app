<script lang="ts">
  import GeoJSON from "ol/format/GeoJSON";

  import EquipmentForm from "$lib/components/EquipmentForm.svelte";
  import ActivityForm from "$lib/components/ActivityForm.svelte";
  import KebabMenu from "$lib/components/KebabMenu.svelte";

  import { getImageViewerState } from "$lib/states/image_viewer.svelte";
  import { type EquipmentData } from "$lib/states/annotate.svelte";

  const viewer = getImageViewerState();

  let selectedIndex = $state<number | null>(null);
  let validForm = $state<boolean>(true);
  let editData = $state<EquipmentData | null>(null);

  const selectedFeatures = $derived(viewer.selectedFeatures);
  const selectedFeature = $derived(
    selectedIndex !== null ? (selectedFeatures[selectedIndex] ?? null) : null,
  );
  const selectedType = $derived(selectedFeature?.get("type") ?? null);
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

  function commit(data: EquipmentData) {
    if (!selectedFeature) return;

    selectedFeature.set("data", data);
    const label =
      selectedType === "equipment"
        ? `${data.id}\n${data.status}\n${data.confidence}`
        : "";

    selectedFeature.set("label", label);
    selectedFeature.changed();
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

    const format = new GeoJSON();

    const geojson = format.writeFeatures(selectedFeatures);
    console.log(geojson);
  }
</script>

{#if selectedFeatures.length > 0}
  <aside class="edit-sidebar">
    <header class="edit-header">
      <KebabMenu>
        <button role="menuitem" onclick={exportFeaturesToGeoJson}
          >Export to GeoJSON</button
        >
        <button role="menuitem">Bulk edit</button>
        <button role="menuitem">Bulk delete</button>
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
