<script lang="ts">
  import { Grid, type IColumnConfig } from "@svar-ui/svelte-grid";
  import { Willow } from "@svar-ui/svelte-core";

  import Modal from "$lib/components/Modal.svelte";
  import Input from "$lib/components/Input.svelte";

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
    api.exec("delete-row", {
      id: null,
    });

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
</script>

<Willow>
  <div class="toolbar">
    <button onclick={() => (showForm = !showForm)}>Add</button>
    {#if saveApi}
      <button onclick={() => saveChanges}>Save</button>
    {/if}
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
