<script lang="ts">
  import { Grid, type IColumnConfig } from "@svar-ui/svelte-grid";
  import { Willow } from "@svar-ui/svelte-core";

  import Modal from "$lib/components/Modal.svelte";
  import Input from "$lib/components/Input.svelte";

  interface Props {
    columns: IColumnConfig[];
    data: Record<string, string>[];
    autoFill?: Record<string, () => any>;
    inputIds?: Set<string>;
  }

  let { columns, data, autoFill, inputIds }: Props = $props();
  let api = $state();
  let showForm = $state<boolean>(false);
  let newRow = $state<Record<string, any>>({});
  let inputColumns = $derived.by(() => {
    if (inputIds === undefined) return columns;

    return columns.filter((c) => inputIds.has(c.id));
  });
  $inspect(inputIds);

  function addRow() {
    if (autoFill !== undefined) {
      Object.entries(autoFill).forEach(([c, fn]) => {
        newRow[c] = fn();
      });
    }

    api.exec("add-row", {
      row: { ...newRow },
    });

    newRow = {};
  }
</script>

<Willow>
  <div class="toolbar">
    <button onclick={() => (showForm = !showForm)}>Add</button>
  </div>
  <Grid bind:this={api} {data} {columns} />

  <Modal bind:open={showForm}>
    <form>
      {#each inputColumns as column}
        <Input label={column.header} oninput={(v) => (newRow[column.id] = v)} />
      {/each}
      <button onclick={addRow}>Add</button>
    </form>
  </Modal>
</Willow>
