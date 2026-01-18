<script lang="ts">
  import {
    Grid,
    HeaderMenu,
    Tooltip,
    type IColumnConfig,
  } from "@svar-ui/svelte-grid";
  import Modal from "$lib/components/Modal.svelte";
  import Input from "$lib/components/Input.svelte";
  import DropdownMenu from "$lib/components/DropdownMenu.svelte";
  import { exportFile } from "$lib/utils/io";

  interface CUD {
    create: Record<string, Record<string, string | number>>[];
    update: Record<string, Record<string, string | number>>[];
    delete: Set<string>;
  }

  interface Props {
    columns: IColumnConfig[];
    data: Record<string, string>[];
    autoFill?: Record<string, () => any>;
    inputIds?: Set<string>;
    saveApi?: string;
  }

  let { columns, data, autoFill, inputIds, saveApi }: Props = $props();
  let gridWrapper: HTMLElement | null = null;

  let api = $state();
  let selectedRows = $state([]);
  let showForm = $state<boolean>(false);
  let newRow = $state<Record<string, string | number>>({});
  let cud = $state<CUD>({
    create: {} as Record<string, Record<string, string | number>>[],
    update: {} as Record<string, Record<string, string | number>>[],
    delete: new Set<string>(),
  });

  let history = $derived(api?.getReactiveState().history);
  let numSelectedRows = $derived(selectedRows.length);
  let inputColumns = $derived.by(() => {
    if (inputIds === undefined) return columns;

    return columns.filter((c) => inputIds.has(c.id));
  });

  function init(api) {
    api.on("update-row", (e) => {
      const row = e.row;

      if (Object.hasOwn(cud.create, row.id)) {
        cud.create[row.id] = row;
        return;
      }

      cud.update[row.id] = row;
    });
  }

  const updateSelected = () => (selectedRows = api.getState().selectedRows);

  function handleUndo(api) {
    api.exec("undo");
  }

  function handleRedo(api) {
    api.exec("redo");
  }

  function addRow() {
    if (autoFill !== undefined) {
      Object.entries(autoFill).forEach(([c, fn]) => {
        newRow[c] = fn();
      });
    }

    api.exec("add-row", {
      row: { ...newRow },
    });

    cud.create[newRow.id] = newRow;

    newRow = {};
    updateSelected();
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

      if (Object.hasOwn(cud.create, id)) {
        delete cud.create[id];
      } else if (Object.hasOwn(cud.update, id)) {
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
      // Deselect all rows
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
    <button onclick={() => (showForm = !showForm)}>Add</button>
    <button onclick={() => selectAllRows()}>Select all</button>
    <button onclick={() => deleteRow()} disabled={!selectedRows.length}
      >Delete</button
    >
    {#if saveApi}
      <button onclick={() => saveChanges()}>Save</button>
    {/if}
    <DropdownMenu label="Export">
      <button onclick={() => exportToJson()}>JSON</button>
      <button onclick={() => exportToCsv()}>CSV</button>
    </DropdownMenu>
  </div>

  <div class="grid" bind:this={gridWrapper}>
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
  </div>

  <div class="grid-footer">
    {#if numSelectedRows > 0}
      <span>{numSelectedRows} rows selected</span>
    {/if}
  </div>
</div>

<Modal bind:open={showForm}>
  <form>
    {#each inputColumns as column}
      <Input label={column.header} oninput={(v) => (newRow[column.id] = v)} />
    {/each}
    <button onclick={addRow}>Add</button>
  </form>
</Modal>

<style>
  .grid-container {
    display: grid;
    grid-template-rows: auto 1fr auto;
  }

  .grid {
    --wx-table-header-background: rgb(var(--color-accent));
    --wx-table-header-cell-border: 1px solid rgba(var(--color-text) / 0.1);
    --wx-table-cell-border: 1px solid rgba(var(--color-text) / 0.1);
    --wx-table-select-background: #eaedf5;
    --wx-table-select-border: inset 3px 0 rgb(var(--color-text));
    --wx-color-primary-font: rgb(var(--color-primary));
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
