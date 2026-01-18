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
  import { exportFile } from "$lib/utils/io";
  import TextArea from "$lib/components/TextArea.svelte";
  import { reset } from "ol/transform";

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

  let api = $state();
  let form = $state<FormState>({
    open: false,
    mode: "add",
    rowId: null,
    initial: {},
  });

  let selectedRows = $state([]);
  let dataToEdit = $state<Record<string, string | number>>({});
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
    const row = api.getRow(id);

    form.open = true;
    form.mode = "edit";
    form.rowId = id;
    form.initial = row;
    editRow = structuredClone(row);
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

    api.exec("add-row", {
      row: structuredClone($state.snapshot(editRow)),
    });
    cud.create[editRow.id] = editRow;
  }

  function saveEdit() {
    if (!form.rowId) return;

    const tempRow = structuredClone($state.snapshot(editRow));

    api.exec("update-row", {
      id: form.rowId,
      row: tempRow,
    });

    if (cud.create.hasOwnProperty(form.rowId)) {
      cud.create[form.rowId] = tempRow;
    } else if (cud.update.hasOwnProperty(form.rowId)) {
      cud.update[form.rowId] = tempRow;
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
    <button onclick={() => handleUndo(api)} disabled={history && !$history.redo}
      >Undo</button
    >
    <button onclick={() => handleRedo(api)} disabled={history && !$history.undo}
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
  </div>

  <div class="grid" bind:this={gridWrapper}>
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
          oninput={(v) => editRow[column.id]}
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
