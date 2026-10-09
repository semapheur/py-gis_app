<script lang="ts">
  import GeoJSON from "ol/format/GeoJSON";
  import ActivityForm from "#lib/components/ActivityForm.svelte";
  import Button from "#lib/components/Button.svelte";
  import EquipmentForm from "#lib/components/EquipmentForm.svelte";
  import PersonnelForm from "#lib/components/PersonnelForm.svelte";
  import Input from "#lib/components/Input.svelte";
  import KebabMenu from "#lib/components/KebabMenu.svelte";
  import Modal from "#lib/components/Modal.svelte";
  import SplitPanes from "#lib/components/SplitPanes.svelte";
  import Table from "#lib/components/Table.svelte";
  import Tabs from "#lib/components/Tabs.svelte";
  import { getImageViewerController } from "#lib/contexts/ol_image_viewer/controller.svelte.js";
  import {
    type AnnotateForm,
    type ValidEquipmentData,
    annotateTabs,
  } from "#lib/contexts/annotate.svelte.js";
  import { exportFile } from "#lib/utils/io.js";
  import type { ColumnDefinition } from "#lib/utils/types.js";
  import { Point } from "ol/geom";
  import {
    equipmentColumnFields,
    equipmentDisplayRow,
    type EquipmentData,
    type EquipmentPatch,
  } from "#lib/schemas/equipment_annotation.js";
  import {
    personnelColumnFields,
    personnelDisplayRow,
    type PersonnelData,
    type PersonnelPatch,
    type PersonnelTableData,
  } from "#lib/schemas/personnel_annotation.js";

  const viewerController = getImageViewerController();

  const equipmentColumns: ColumnDefinition[] = [
    {
      id: "id",
      label: "#",
      sortable: true,
      filterable: true,
    },
    { id: "geometry", label: "Geometry", sortable: true, filterable: true },
    ...equipmentColumnFields.map(([key, def]) => ({
      id: key,
      label: def.label,
      sortable: true,
      filterable: true,
    })),
  ];
  const personnelColumns: ColumnDefinition[] = [
    {
      id: "id",
      label: "#",
      sortable: true,
      filterable: true,
    },
    { id: "geometry", label: "Geometry", sortable: true, filterable: true },
    ...personnelColumnFields.map(([key, def]) => ({
      id: key,
      label: def.label,
      sortable: true,
      filterable: true,
    })),
  ];

  const activityColumns: ColumnDefinition[] = [];

  const tableColumns = {
    activity: activityColumns,
    equipment: equipmentColumns,
    personnel: personnelColumns,
  };

  const tableSelectable = {
    activity: "single",
    equipment: "multi",
    personnel: "multi",
  } as const;

  let activeTableTab = $state<AnnotateForm>("equipment");
  let selectedRows = $state<number[]>([]);

  let validForm = $state<boolean>(true);
  let editData = $state<EquipmentData | PersonnelData | null>(null);
  let bulkEdit = $state<boolean>(false);
  let bulkPatch = $state<EquipmentPatch | PersonnelPatch>({});
  let validBulkForm = $state<boolean>(true);
  let polygonSize = $state<number>(2);
  let openConvert = $state<boolean>(false);

  const selectedAnnotations = $derived(viewerController.selectedAnnotations);

  const tableData = $derived({
    activity: [],
    equipment: selectedAnnotations.equipment
      .flatMap((f, i) => {
        const data = f.get("data") as ValidEquipmentData | undefined;
        if (!data) return [];

        return {
          id: i + 1,
          equipment: data.equipment.label,
          geometry: f.getGeometry()?.getType(),
          ...equipmentDisplayRow(data),
        };
      })
      .filter(Boolean),
    personnel: selectedAnnotations.personnel.flatMap((f, i) => {
      const data = f.get("data") as PersonnelTableData | undefined;
      if (!data) return [];

      return {
        id: i + 1,
        geometry: f.getGeometry()?.getType(),
        ...personnelDisplayRow(data),
      };
    }),
  });

  const selectedFeatures = $derived(
    selectedRows
      .map((i) => selectedAnnotations[activeTableTab][i])
      .filter(Boolean),
  );

  const selectedPointFeatures = $derived(
    selectedFeatures.filter((f) => f.getGeometry() instanceof Point),
  );

  const convertTitle = $derived(
    `Convert ${selectedPointFeatures.length} ${selectedPointFeatures.length === 1 ? "point" : "points"} to ${selectedPointFeatures.length === 1 ? "polygon" : "polygons"}`,
  );

  const selectedFeature = $derived(
    selectedFeatures.length === 1 ? selectedFeatures[0] : null,
  );

  const selectedType = $derived(selectedFeature?.get("type") ?? null);
  const selectedGeometryType = $derived(
    selectedFeature?.getGeometry()?.getType() ?? null,
  );
  const selectedGeometryTypes = $derived(
    new Set(selectedFeatures.map((f) => f.getGeometry()?.getType())),
  );
  const mixedGeometry = $derived(
    activeTableTab === "personnel" &&
      selectedFeatures.length > 1 &&
      selectedGeometryTypes.size > 1,
  );
  const bulkGeometry = $derived(
    selectedGeometryTypes.size === 1 ? [...selectedGeometryTypes][0] : null,
  );

  $effect(() => {
    if (selectedFeatures.length > 1) {
      bulkEdit = !mixedGeometry;
      editData = null;
      bulkPatch = mixedGeometry ? {} : getCommonValues(selectedFeatures);
      return;
    }

    bulkEdit = false;
    bulkPatch = {};
    editData = selectedFeature?.get("data") ?? null;
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

  function sameValue(a: unknown, b: unknown) {
    if (a && b && typeof a === "object" && typeof b === "object") {
      return (a as { id?: unknown }).id === (b as { id?: unknown }).id;
    }
    return a === b;
  }

  function getCommonValues(features: typeof selectedFeatures) {
    if (!features.length) return {};

    const firstData = features[0].get("data") as Record<string, unknown> | null;
    if (!firstData) return {};

    const commonValues: Record<string, unknown> = {};

    for (const key in firstData) {
      const isCommon = features.every((feature) => {
        const data = feature.get("data") as Record<string, unknown> | null;
        return !!data && sameValue(data[key], firstData[key]);
      });

      if (isCommon) {
        commonValues[key] = firstData[key];
      }
    }

    return commonValues as EquipmentPatch | PersonnelPatch;
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
        {#if selectedFeatures.length}
          <button
            role="menuitem"
            onclick={() => viewerController.zoomToFeatures(selectedFeatures)}
          >
            Zoom to selection
          </button>
        {/if}
        <button
          role="menuitem"
          onclick={() => viewerController.selectAllAnnotations(activeTableTab)}
          >Select all annotations</button
        >
        {#if activeTableTab === "equipment" && selectedPointFeatures.length}
          <button role="menuitem" onclick={() => (openConvert = true)}>
            Convert to polygons
          </button>
        {/if}
        <button role="menuitem" onclick={exportFeaturesToGeoJson}
          >Export to GeoJSON</button
        >
        <button role="menuitem" onclick={bulkDelete}>Bulk delete</button>
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
  <div class="bottom-pane">
    {#if editData}
      {#if selectedType === "equipment"}
        <EquipmentForm
          value={editData as EquipmentData}
          onchange={(v) => (editData = v)}
          onvalid={(v) => (validForm = v)}
        />
      {:else if selectedType === "personnel"}
        <PersonnelForm
          value={editData as PersonnelData}
          geometry={selectedGeometryType}
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
        <Button
          background="oklch(var(--color-negative))"
          onclick={deleteFeature}>Delete</Button
        >
      </footer>
    {:else if bulkEdit}
      {#if activeTableTab === "equipment"}
        <EquipmentForm
          value={bulkPatch}
          bulk
          onchange={(v) => (bulkPatch = v)}
          onvalid={(v) => (validBulkForm = v)}
        />
      {:else if activeTableTab === "personnel"}
        <PersonnelForm
          value={bulkPatch as PersonnelPatch}
          geometry={bulkGeometry as "Point" | "Polygon"}
          bulk
          onchange={(v) => (bulkPatch = v)}
        />
      {/if}

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

<SplitPanes panes={[topPane, bottomPane]} direction="column" />
<Modal bind:open={openConvert} title={convertTitle}>
  <div class="conversion-form">
    <Input
      bind:value={polygonSize}
      placeholder="Polygon size (meters)"
      type="number"
      min="1"
      step="0.1"
    />
    <div class="conversion-buttons">
      <Button
        background="oklch(var(--color-positive))"
        disabled={!selectedFeatures.length}
        onclick={() => {
          viewerController.convertPointFeaturesToPolygons(
            selectedFeatures,
            polygonSize,
          );
          openConvert = false;
        }}
      >
        Convert
      </Button>
      <Button
        background="oklch(var(--color-negative))"
        onclick={() => (openConvert = false)}
      >
        Cancel
      </Button>
    </div>
  </div>
</Modal>

<style>
  .edit-table {
    display: grid;
    grid-template-rows: auto 1fr;
    gap: var(--size-md);
    padding: 0 var(--size-md);
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

  .bottom-pane {
    display: flex;
    flex-direction: column;
    gap: var(--size-md);
    padding: var(--size-md);
  }

  .conversion-form {
    display: flex;
    flex-direction: column;
    gap: var(--size-md);
    padding-top: var(--size-md);
  }

  .conversion-buttons {
    display: flex;
    gap: var(--size-md);
  }
</style>
