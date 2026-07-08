<script
  lang="ts"
  generics="T extends Record<string, unknown> = Record<string, unknown>"
>
  import {
    Grid,
    HeaderMenu,
    Tooltip,
    Willow,
    type IColumnConfig,
  } from "@svar-ui/svelte-grid";
  import Button from "$lib/components/Button.svelte";
  import DropdownMenu from "$lib/components/DropdownMenu.svelte";
  import Input from "$lib/components/Input.svelte";
  import Modal from "$lib/components/Modal.svelte";
  import Select from "$lib/components/Select.svelte";
  import TextArea from "$lib/components/TextArea.svelte";
  import { toast } from "$lib/stores/toast.svelte";
  import { fetchMsgpack } from "$lib/utils/fetch";
  import { exportFile, parseCsv, parseJson } from "$lib/utils/io";
  import type { ComponentExports, SelectOption } from "$lib/utils/types";

  type FormMode = "add" | "edit";

  type GridApi = ComponentExports<typeof Grid>;

  interface FormState {
    open: boolean;
    mode: FormMode;
    rowId: string | null;
  }

  interface Column extends IColumnConfig {
    nullable: boolean;
    validate?: (input: unknown) => Promise<boolean>;
    unique?: boolean;
    selectOptions?: SelectOption[];
  }

  interface ValidationResult {
    valid: boolean;
    message: string | null;
  }

  interface Props {
    columns: Column[];
    data: T[];
    insertApi: string;
    updateApi: string;
    deleteApi: string;
    inputIds?: Set<string>;
    validateInputRow?: (
      inputRow: Partial<T>,
      existingRows: T[],
    ) => ValidationResult;
  }

  let {
    columns,
    data,
    insertApi,
    updateApi,
    deleteApi,
    validateInputRow,
  }: Props = $props();
  let gridWrapper: HTMLElement | null = null;
  let fileInput: HTMLInputElement | null = null;
  let isDragging = $state<boolean>(false);

  let api = $state<GridApi | undefined>();
  let form = $state<FormState>({
    open: false,
    mode: "add",
    rowId: null,
  });

  let selectedRows = $state([]);
  let inputRow = $state<Partial<T>>({});
  let columnErrors = $state<Record<string, string>>({});

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
    const row = structuredClone(api.getRow(id)) as T;

    form.open = true;
    form.mode = "edit";
    form.rowId = id;
    inputRow = row;
  }

  function openAdd() {
    form.open = true;
    form.mode = "add";
    form.rowId = null;
    inputRow = {};
  }

  function resetAddForm() {
    inputRow = {};
  }

  function closeForm() {
    form.open = false;
    form.rowId = null;
    inputRow = {};
    columnErrors = {};
  }

  async function addRow() {
    const result = await fetchMsgpack(insertApi, {
      method: "POST",
      body: $state.snapshot(inputRow),
    });

    if (!result.ok) {
      toast.error(
        `Failed to insert row: ${result.error.message} (${result.error.status})`,
      );
      return;
    }

    const baseRow = $state.snapshot(inputRow);
    const newRow = result.data?.inserted_row
      ? { ...baseRow, ...result.data.inserted_row }
      : baseRow;

    api.exec("add-row", {
      row: newRow,
    });
  }

  async function updateRow() {
    if (!form.rowId) return;

    const result = await fetchMsgpack(updateApi, {
      method: "POST",
      body: inputRow,
    });

    if (!result.ok) {
      toast.error(
        `Failed to update row: ${result.error.message} (${result.error.status})`,
      );
      return;
    }

    const baseRow = $state.snapshot(inputRow);
    const newRow = result.data?.updated_row
      ? { ...baseRow, ...result.data.updated_row }
      : baseRow;

    api.exec("update-row", {
      id: form.rowId,
      row: newRow,
    });
  }

  function deleteRow() {
    const ids = api.getState().selectedRows;
    if (!ids) return;
    return;
  }

  async function validateColumn(
    column: Column,
    value: T,
    rowId: string | null,
  ): Promise<string | null> {
    if (column.validate) {
      try {
        const isValid = await column.validate(value);
        if (!isValid) {
          return `Invalid value for ${column.header}`;
        }
      } catch (error) {
        return error instanceof Error
          ? error.message
          : `Validation failed for ${column.header}`;
      }
    }
    if (column?.unique) {
      const duplicate = api
        .getState()
        .data.some((row) => row.id !== rowId && row[column.id] === value);

      if (duplicate) {
        return "Value already exists in data grid";
      }
    }

    if (!column.nullable && value == null) {
      return "Value cannot be empty";
    }

    return null;
  }

  async function saveForm(event: PointerEvent) {
    event.preventDefault();

    const errors = await Promise.all(
      editColumns.map((column) =>
        validateColumn(column, inputRow[column.id], form.rowId).then(
          (error) => [column.id, error] as const,
        ),
      ),
    );

    const newErrors = Object.fromEntries(
      errors.filter(([, error]) => error !== null),
    );

    for (const key in columnErrors) delete columnErrors[key];

    if (Object.keys(newErrors).length > 0) {
      Object.assign(columnErrors, newErrors);
      return;
    }

    if (validateInputRow) {
      const validationResult = validateInputRow(inputRow, api.getState().data);
      if (!validationResult.valid) {
        console.error(validationResult.message);
        return;
      }
    }

    if (form.mode === "add") {
      await addRow();
      resetAddForm();
    } else if (form.mode === "edit") {
      await updateRow();
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
    <Button onclick={() => handleUndo(api)} disabled={history && !$history.undo}
      >Undo</Button
    >
    <Button onclick={() => handleRedo(api)} disabled={history && !$history.redo}
      >Redo</Button
    >
    <Button onclick={openAdd}>Add</Button>
    <Button onclick={selectAllRows}>Select all</Button>
    <Button onclick={deleteRow} disabled={!selectedRows.length}>Delete</Button>
    <DropdownMenu label="Export">
      <Button onclick={exportToJson}>JSON</Button>
      <Button onclick={exportToCsv}>CSV</Button>
    </DropdownMenu>
    <Button onclick={openFileDialog}>Import</Button>
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
    role="none"
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
  <form class="grid-form" onsubmit={saveForm}>
    {#each editColumns as column}
      {#if column.editor === "text"}
        <Input bind:value={inputRow[column.id]} placeholder={column.header} />
      {:else if column.editor === "textarea"}
        <TextArea
          bind:value={inputRow[column.id]}
          placeholder={column.header}
        />
      {:else if column.editor === "select"}
        <Select
          bind:value={inputRow[column.id]}
          options={column.selectOptions}
          placeholder={column.header}
        />
      {/if}
      {#if columnErrors[column.id]}
        <span class="error">
          {columnErrors[column.id]}
        </span>
      {/if}
    {/each}

    <Button type="submit"
      >{form.mode === "add" ? "Add row" : "Save changes"}</Button
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
    color: oklch(var(--color-text));
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

  .grid-form {
    display: flex;
    flex-direction: column;
    gap: var(--size-md);
  }

  .grid-footer {
    min-height: calc(1rem + var(--size-sm));
    padding: var(--size-sm);
    background: oklch(var(--color-secondary-accent));
  }

  .error {
    color: red;
    font-size: var(--text-sm);
  }
</style>
