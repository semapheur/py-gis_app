<script lang="ts">
  import {
    Grid,
    HeaderMenu,
    Tooltip,
    Willow,
    type IColumnConfig,
  } from "@svar-ui/svelte-grid";
  import Modal from "$lib/components/Modal.svelte";
  import Input from "$lib/components/Input.svelte";
  import DropdownMenu from "$lib/components/DropdownMenu.svelte";
  import { exportFile, parseCsv, parseJson } from "$lib/utils/io";
  import TextArea from "$lib/components/TextArea.svelte";

  type FormMode = "add" | "edit";

  interface CUD {
    create: Record<string, Record<string, string | number>>[];
    update: Record<string, Record<string, string | number>>[];
    delete: Set<string>;
  }

  interface FormState {
    open: boolean;
    mode: FormMode;
    rowId: string | null;
    initial: Record<string, string | number>;
  }

  interface Props {
    columns: IColumnConfig[];
    data: Record<string, string>[];
    autoFill?: Record<string, () => any>;
    inputIds?: Set<string>;
    saveApi?: string;
  }

  let { columns, data, autoFill, saveApi }: Props = $props();
  let gridWrapper: HTMLElement | null = null;
  let fileInput: HTMLInputElement | null = null;
  let isDragging = $state<boolean>(false);

  let api = $state();
  let form = $state<FormState>({
    open: false,
    mode: "add",
    rowId: null,
    initial: {},
  });

  let selectedRows = $state([]);
  let editRow = $state<Record<string, string | number>>({});
  let cud = $state<CUD>({
    create: {} as Record<string, Record<string, string | number>>[],
    update: {} as Record<string, Record<string, string | number>>[],
    delete: new Set<string>(),
  });

  let history = $derived(api?.getReactiveState().history);
  let numSelectedRows = $derived(selectedRows.length);
  let editColumns = $derived(columns.filter((c) => c.hasOwnProperty("editor")));

  function init(api) {
    api.intercept("open-editor", ({ id }) => {
      openEdit(id);
      return false;
    });
  }

  const updateSelected = () => (selectedRows = api.getState().selectedRows);

  function handleUndo(api) {
    api.exec("undo");
  }

  function handleRedo(api) {
    api.exec("redo");
  }

  function openEdit(id: string) {
    const row = structuredClone(api.getRow(id));

    form.open = true;
    form.mode = "edit";
    form.rowId = id;
    form.initial = row;
    editRow = row;
  }

  function openAdd() {
    form.open = true;
    form.mode = "add";
    form.rowId = null;
    form.initial = {};
    editRow = {};
  }

  function resetAddForm() {
    form.initial = {};
    editRow = {};
  }

  function closeForm() {
    form.open = false;
    form.rowId = null;
    form.initial = {};
    editRow = {};
  }

  function addRow() {
    if (autoFill !== undefined) {
      Object.entries(autoFill).forEach(([c, fn]) => {
        editRow[c] = fn();
      });
    }

    const addRow = structuredClone($state.snapshot(editRow));
    api.exec("add-row", {
      row: addRow,
    });
    cud.create[editRow.id] = addRow;
  }

  function saveEdit() {
    if (!form.rowId) return;

    const saveRow = structuredClone($state.snapshot(editRow));

    api.exec("update-row", {
      id: form.rowId,
      row: saveRow,
    });

    if (cud.create.hasOwnProperty(form.rowId)) {
      cud.create[form.rowId] = saveRow;
    } else if (cud.update.hasOwnProperty(form.rowId)) {
      cud.update[form.rowId] = saveRow;
    }
  }

  function saveForm(event: PointerEvent) {
    event.preventDefault();

    if (form.mode === "add") {
      addRow();
      resetAddForm();
    } else {
      saveEdit();
      closeForm();
    }
  }

  function selectAllRows() {
    const allRows = api.getState().data;
    allRows.forEach((row) => {
      api.exec("select-row", { id: row.id, toggle: true, mode: true });
    });
    updateSelected();
  }

  function deleteRow() {
    const ids = api.getState().selectedRows;
    if (!ids) return;

    ids.forEach((id) => {
      api.exec("delete-row", { id });

      if (cud.create.hasOwnProperty(id)) {
        delete cud.create[id];
      } else if (cud.update.hasOwnProperty(id)) {
        delete cud.update[id];
        cud.delete.add(id);
      }
    });

    updateSelected();
  }

  async function saveChanges() {
    if (!saveApi) return;

    if (
      cud.create.length === 0 &&
      cud.update.length === 0 &&
      cud.delete.size === 0
    ) {
      return;
    }

    try {
      const payload = {
        upsert: [...Object.values(cud.create), ...Object.values(cud.update)],
        delete: Array.from(cud.delete),
      };

      const res = await fetch(saveApi, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        throw new Error(await res.text());
      }

      cud.create = {} as Record<string, Record<string, string | number>>[];
      cud.update = {} as Record<string, Record<string, string | number>>[];
      cud.delete = new Set<string>();
    } catch (err) {
      console.error("Failed to save grid changes:", err);
    }
  }

  function exportToJson() {
    const gridData = api.getState().data;
    const json = JSON.stringify(gridData);
    const blob = new Blob([json], { type: "application/json" });
    const fileName = `grid_data_${new Date().toISOString().split("T")[0]}.json`;
    exportFile(blob, fileName);
  }

  function exportToCsv() {
    const gridData = api.getState().data;

    const headers = columns.map((col) => col.id).join(",");

    const rows = gridData.map((row) => {
      return columns
        .map((col) => {
          const value = row[col.id];
          if (value === null || value === undefined) return "";
          const stringValue = String(value);
          if (
            stringValue.includes(",") ||
            stringValue.includes('"') ||
            stringValue.includes("\n")
          ) {
            return `"${stringValue.replace(/"/g, '""')}"`;
          }
          return stringValue;
        })
        .join(",");
    });

    const csv = [headers, ...rows].join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
    const fileName = `grid_export_${new Date().toISOString().split("T")[0]}.csv`;
    exportFile(blob, fileName);
  }

  async function importData(file: File) {
    try {
      const text = await file.text();
      let importedRows: Record<string, string | number>[] = [];

      if (file.name.endsWith(".json")) {
        importedRows = parseJson(text);
      } else if (file.name.endsWith(".csv")) {
        importedRows = parseCsv(text);
      } else {
        throw new Error("Unsupported file type. Please use .json or .csv");
      }

      const columnIds = new Set(columns.map((c) => c.id));

      importedRows.forEach((row) => {
        const rowColumns = new Set(Object.keys(row));
        const validColumns = columnIds.intersection(rowColumns);
        const filteredRow = Object.fromEntries(
          Object.entries(row).filter(([key]) => validColumns.has(key)),
        );

        api.exec("add-row", { row: filteredRow });
        cud.create[filteredRow.id] = filteredRow;
      });

      console.log(`Successfully imported ${importedRows.length} rows`);
    } catch (error) {
      console.log("Import failed:", error);
      alert(`Import failed: ${error.message}`);
    }
  }

  function onfileselect(event: Event) {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];

    if (file) {
      importData(file);
    }
    input.value = "";
  }

  function openFileDialog() {
    fileInput?.click();
  }

  function handleDragOver(event: DragEvent) {
    event.preventDefault();
    isDragging = true;
  }

  function handleDragLeave(event: DragEvent) {
    event.preventDefault();
    isDragging = false;
  }

  function handleDrop(event: DragEvent) {
    event.preventDefault();
    isDragging = false;

    const file = event.dataTransfer?.files[0];
    if (file) {
      importData(file);
    }
  }

  function handleClickOutside(event: MouseEvent) {
    if (!api || selectedRows.length === 0) return;

    const target = event.target as HTMLElement;
    const isButton =
      target.closest("button") || target.closest('[role="button"]');

    if (gridWrapper && !gridWrapper.contains(target) && !isButton) {
      selectedRows.forEach((id) => {
        api.exec("select-row", { id: id, toggle: true, mode: false });
      });
      updateSelected();
    }
  }

  $effect(() => {
    document.addEventListener("pointerdown", handleClickOutside);

    return () => {
      document.removeEventListener("pointerdown", handleClickOutside);
    };
  });
</script>

<div class="grid-container">
  <div class="grid-toolbar">
    <button onclick={() => handleUndo(api)} disabled={history && !$history.undo}
      >Undo</button
    >
    <button onclick={() => handleRedo(api)} disabled={history && !$history.redo}
      >Redo</button
    >
    <button onclick={openAdd}>Add</button>
    <button onclick={selectAllRows}>Select all</button>
    <button onclick={deleteRow} disabled={!selectedRows.length}>Delete</button>
    {#if saveApi}
      <button onclick={saveChanges}>Save</button>
    {/if}
    <DropdownMenu label="Export">
      <button onclick={exportToJson}>JSON</button>
      <button onclick={exportToCsv}>CSV</button>
    </DropdownMenu>
    <button onclick={openFileDialog}>Import</button>
  </div>

  <input
    type="file"
    accept=".json,.csv"
    bind:this={fileInput}
    onchange={onfileselect}
    style="display: none"
  />

  <div
    class="grid"
    class:dragging={isDragging}
    bind:this={gridWrapper}
    ondragover={handleDragOver}
    ondragleave={handleDragLeave}
    ondrop={handleDrop}
    role="drag"
    undo
  >
    {#if isDragging}
      <div class="drop-overlay">
        <div class="drop-message">Drop file to import</div>
      </div>
    {/if}
    <Willow>
      <Tooltip {api}>
        <HeaderMenu {api}>
          <Grid
            bind:this={api}
            {data}
            {columns}
            {init}
            multiselect={true}
            onselectrow={updateSelected}
          />
        </HeaderMenu>
      </Tooltip>
    </Willow>
  </div>

  <div class="grid-footer">
    {#if numSelectedRows > 0}
      <span>{numSelectedRows} rows selected</span>
    {/if}
  </div>
</div>

<Modal bind:open={form.open}>
  <form onsubmit={saveForm}>
    {#each editColumns as column}
      {#if column.editor === "text"}
        <Input
          value={form.initial[column.id]}
          label={column.header}
          oninput={(v) => (editRow[column.id] = v)}
        />
      {:else if column.editor === "textarea"}
        <TextArea
          value={form.initial[column.id]}
          label={column.header}
          oninput={(v) => (editRow[column.id] = v)}
        />
      {/if}
    {/each}

    <button type="submit"
      >{form.mode === "add" ? "Add row" : "Save changes"}</button
    >
  </form>
</Modal>

<style>
  .grid-container {
    display: grid;
    grid-template-rows: auto 1fr auto;
  }

  .grid {
    height: 100%;
    overflow-y: scroll;

    &.dragging {
      outline: 2px dashed #4a90e2;
      outline-offset: -2px;
    }
  }

  .drop-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(74, 144, 226, 0.1);
    display: flex;
    align-items: center;
    justify-content: center;
    pointer-events: none;
    z-index: 10;
  }

  .drop-message {
    background: #4a90e2;
    color: rgb(var(--color-text));
    padding: 1rem 2rem;
    border-radius: var(--size-sm);
    font-size: var(--text-lg);
    font-weight: var(--font-bold);
    box-shadow: 0 4px 12px rgba(0 0 0 0.15);
  }

  .grid-toolbar {
    display: flex;
    gap: var(--size-md);
  }

  .grid-footer {
    min-height: calc(1rem + var(--size-sm));
    padding: var(--size-sm);
    background: rgb(var(--color-accent));
  }
</style>
