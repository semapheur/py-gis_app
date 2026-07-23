<script lang="ts">
  import GeoJSON from "ol/format/GeoJSON";
  import ActivityForm from "$lib/components/ActivityForm.svelte";
  import Button from "$lib/components/Button.svelte";
  import EquipmentForm from "$lib/components/EquipmentForm.svelte";
  import KebabMenu from "$lib/components/KebabMenu.svelte";
  import SplitPanes from "$lib/components/SplitPanes.svelte";
  import Table from "$lib/components/Table.svelte";
  import Tabs from "$lib/components/Tabs.svelte";
  import { getImageViewerController } from "$lib/contexts/ol_image_viewer/controller.svelte";
  import {
    type AnnotateForm,
    type EquipmentData,
    type CompleteEquipmentData,
    annotateTabs,
  } from "$lib/contexts/annotate.svelte";
  import { exportFile } from "$lib/utils/io";
  import type { ColumnDefinition } from "$lib/utils/types";

  type BulkEquipmentPatch = Partial<EquipmentData>;

  const viewerController = getImageViewerController();

  const equipmentColumns: ColumnDefinition[] = [
    {
      id: "id",
      label: "#",
      sortable: true,
      filterable: true,
    },
    {
      id: "equipment",
      label: "Equipment",
      sortable: true,
      filterable: true,
    },
    {
      id: "confidence",
      label: "Confidence",
      sortable: true,
      filterable: true,
    },
    {
      id: "status",
      label: "Status",
      sortable: true,
      filterable: true,
    },
    {
      id: "configuration",
      label: "Configuration",
      sortable: true,
      filterable: true,
    },
    {
      id: "modification",
      label: "Modification",
      sortable: true,
      filterable: true,
    },
    {
      id: "visibility",
      label: "Visibility",
      sortable: true,
      filterable: true,
    },
  ] as const;

  const activityColumns = [];

  const tableColumns = {
    equipment: equipmentColumns,
    activity: activityColumns,
  };

  const tableSelectable = {
    equipment: "multi",
    activity: "single",
  } as const;

  let activeTableTab = $state<AnnotateForm>("equipment");
  let selectedRows = $state<number[]>([]);

  let validForm = $state<boolean>(true);
  let editData = $state<EquipmentData | null>(null);
  let bulkEdit = $state<boolean>(false);
  let bulkPatch = $state<BulkEquipmentPatch>({});
  let validBulkForm = $state(true);

  const selectedAnnotations = $derived(viewerController.selectedAnnotations);
  const hasSelectedAnnotations = $derived.by(() => {
    const totalLength =
      selectedAnnotations.equipment.length +
      selectedAnnotations.activity.length;
    return totalLength > 0;
  });

  const tableData = $derived({
    equipment: selectedAnnotations.equipment
      .map((f, i) => {
        const data = f.get("data") as EquipmentData | undefined;
        if (!data) return null;

        return {
          id: i + 1,
          equipment: data.equipment?.label,
          confidence: data.confidence?.label,
          status: data.status?.label,
        };
      })
      .filter(Boolean),
    activity: [],
  });

  const selectedFeatures = $derived(
    selectedRows
      .map((i) => selectedAnnotations[activeTableTab][i])
      .filter(Boolean),
  );

  const selectedFeature = $derived(
    selectedFeatures.length === 1 ? selectedFeatures[0] : null,
  );

  const selectedType = $derived(selectedFeature?.get("type") ?? null);
  const selectedGeometry = $derived(selectedFeature?.getGeometryName() ?? null);

  const canBulkEdit = $derived(selectedFeatures.length > 1);

  $effect(() => {
    if (selectedFeatures.length > 1) {
      bulkEdit = true;
      editData = null;
      bulkPatch = getCommonValues(selectedFeatures);
      return;
    }

    bulkEdit = false;
    bulkPatch = {};

    if (selectedFeature) {
      editData = selectedFeature.get("data");

      return;
    }

    editData = null;
  });

  function saveEdits() {
    if (!selectedFeature || !editData || !validForm) return;

    viewerController.updateFeatureData(
      selectedFeature,
      $state.snapshot(editData),
    );
  }

  function deleteFeature() {
    if (!selectedFeature) return;

    viewerController.removeAnnotations([selectedFeature]);
  }

  function getCommonValues(
    features: typeof selectedFeatures,
  ): BulkEquipmentPatch {
    if (!features.length) return {};

    const commonValues: BulkEquipmentPatch = {};

    const firstData = features[0].get("data") as CompleteEquipmentData | null;
    if (!firstData) return {};

    for (const key in firstData) {
      const typedKey = key as keyof CompleteEquipmentData;
      const firstValue = firstData[typedKey];

      const isCommon = features.every((feature) => {
        const data = feature.get("data") as CompleteEquipmentData | null;

        if (!data) return false;

        return data[typedKey]?.id === firstValue?.id;
      });

      if (isCommon) {
        commonValues[typedKey] = firstValue;
      }
    }

    return commonValues;
  }

  function applyBulkEdit() {
    if (!validBulkForm) return;

    for (const feature of selectedFeatures) {
      const data = feature.get("data") as EquipmentData;
      if (!data) continue;

      viewerController.updateFeatureData(feature, {
        ...data,
        ...bulkPatch,
      });
    }

    bulkEdit = false;
    bulkPatch = {};
  }

  function bulkDelete() {
    const count = selectedFeatures.length;
    if (!count) return;

    const confirmed = confirm(
      `Delete ${count} selected annotation${count > 1 ? "s" : ""}?`,
    );
    if (!confirmed) return;

    viewerController.removeAnnotations(selectedFeatures);
  }

  function polygonize() {
    if (!selectedFeature) return;

    viewerController.convertPointFeatureToPolygon(selectedFeature, 2);
  }

  function exportFeaturesToGeoJson() {
    if (!selectedFeatures.length) return;

    const projection = viewerController.projection;
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
</script>

{#snippet topPane()}
  <div class="edit-table">
    <header class="edit-table-header">
      <KebabMenu>
        {#if activeTableTab === "equipment"}
          <button role="menuitem" onclick={() => {}}
            >Select all annotations</button
          >
          <button role="menuitem" onclick={exportFeaturesToGeoJson}
            >Export to GeoJSON</button
          >
          {#if selectedAnnotations.equipment.length > 1}
            <button
              role="menuitem"
              disabled={!canBulkEdit}
              onclick={startBulkEdit}>Bulk edit</button
            >
          {/if}
          <button role="menuitem" onclick={bulkDelete}>Bulk delete</button>
        {:else if activeTableTab === "activity"}
          <button role="menuitem" onclick={() => {}}
            >Select all annotations</button
          >
        {/if}
      </KebabMenu>
      <Tabs tabs={annotateTabs} bind:selected={activeTableTab} />
    </header>
    <Table
      data={tableData[activeTableTab]}
      columns={tableColumns[activeTableTab]}
      selectable={tableSelectable[activeTableTab]}
      onselectionchange={(rows) =>
        (selectedRows = rows.map((r) => Number(r.id) - 1))}
    />
  </div>
{/snippet}

{#snippet bottomPane()}
  <div>
    {#if editData}
      {#if selectedType === "equipment"}
        <EquipmentForm
          value={editData}
          onchange={(v) => (editData = v)}
          onvalid={(v) => (validForm = v)}
        />
      {:else if selectedType === "activity"}
        <ActivityForm />
      {/if}
      <footer class="edit-form-footer">
        <Button
          background="oklch(var(--color-positive))"
          disabled={!validForm}
          onclick={saveEdits}
        >
          Save
        </Button>
        {#if selectedGeometry === "Point"}
          <Button onclick={() => polygonize()}>Polygonize</Button>
        {/if}
        <Button
          background="oklch(var(--color-negative))"
          onclick={deleteFeature}>Delete</Button
        >
      </footer>
    {:else if bulkEdit}
      <EquipmentForm
        value={bulkPatch}
        bulk
        onchange={(v) => (bulkPatch = v)}
        onvalid={(v) => (validBulkForm = v)}
      />

      <footer class="edit-form-footer">
        <Button
          background="oklch(var(--color-positive))"
          disabled={!validBulkForm}
          onclick={applyBulkEdit}
        >
          Apply to {selectedFeatures.length}
        </Button>

        <Button
          background="oklch(var(--color-negative))"
          onclick={() => (bulkEdit = false)}
        >
          Cancel
        </Button>
      </footer>
    {/if}
  </div>
{/snippet}

{#if hasSelectedAnnotations}
  <aside class="edit-sidebar">
    <SplitPanes panes={[topPane, bottomPane]} direction="column" />
  </aside>
{/if}

<style>
  .edit-sidebar {
    display: flex;
    flex-direction: column;
    gap: var(--size-md);
    height: 100%;
    width: clamp(200px, 30%, 600px);
    position: absolute;
    top: 0;
    right: 0;
    padding: var(--size-md);
    background: oklch(var(--color-primary));
    z-index: 1;
  }

  .edit-table {
    display: grid;
    grid-template-rows: auto 1fr;
    gap: var(--size-md);
    height: 100%;
    overflow: hidden;
    border-bottom: 1px solid oklch(var(--color-secondary-accent));
  }

  .edit-table-header {
    display: flex;
    gap: var(--size-md);
    padding-bottom: var(--size-md);
    border-bottom: 1px solid oklch(var(--color-secondary-accent));
    z-index: 2;
  }
</style>
