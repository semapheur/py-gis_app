<script lang="ts">
  import { Grid, type IColumnConfig } from "@svar-ui/svelte-grid";
  import { Willow } from "@svar-ui/svelte-core";
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
  let api = $state();
  let history = $derived(api?.getReactiveState().history);
  let showForm = $state<boolean>(false);
  let newRow = $state<Record<string, string | number>>({});
  let inputColumns = $derived.by(() => {
    if (inputIds === undefined) return columns;

    return columns.filter((c) => inputIds.has(c.id));
  });
  let cud = $state<CUD>({
    create: {} as Record<string, Record<string, string | number>>[],
    update: {} as Record<string, Record<string, string | number>>[],
    delete: new Set<string>(),
  });

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
  }

  function deleteRow() {
    const id = api.getState().selectedRows[0];
    if (id) {
    }
    const gridData = api.getState().data;

    api.exec("delete-row", { id });

    // if (Object.hasOwn(cud.create, id)) {
    // delete cud.create[id]
    // return
    // }
    //
    // if Object.hasOwn(cud.update, id) {
    // delete cud.update(cud.update, id)
    // }
    //
    // cud.delete.add(id)
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
</script>

<Willow>
  <div class="toolbar">
    <button onclick={() => handleUndo(api)} disabled={history && !$history.redo}
      >Undo</button
    >
    <button onclick={() => handleRedo(api)} disabled={history && !$history.undo}
      >Redo</button
    >
    <button onclick={() => (showForm = !showForm)}>Add</button>
    <button onclick={() => deleteRow()}>Delete</button>
    {#if saveApi}
      <button onclick={() => saveChanges()}>Save</button>
    {/if}
    <DropdownMenu label="Export">
      <button onclick={() => exportToJson()}>JSON</button>
      <button onclick={() => exportToCsv()}>CSV</button>
    </DropdownMenu>
  </div>
  <Grid bind:this={api} {data} {columns} multiselect={true} />

  <Modal bind:open={showForm}>
    <form>
      {#each inputColumns as column}
        <Input label={column.header} oninput={(v) => (newRow[column.id] = v)} />
      {/each}
      <button onclick={addRow}>Add</button>
    </form>
  </Modal>
</Willow>

<style>
  .toolbar {
    display: flex;
    gap: var(--size-md);
  }
</style>
