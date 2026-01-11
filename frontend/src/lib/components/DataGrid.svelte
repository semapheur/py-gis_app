<script lang="ts">
  import { Grid } from "@svar-ui/svelte-grid";
  import { Willow } from "@svar-ui/svelte-core";

  import Modal from "$lib/components/Modal.svelte";
  import Input from "$lib/components/Input.svelte";

  interface Props {
    columns: Record<string, string>[];
    data: Record<string, string>[];
  }

  let { columns, data }: Props = $props();
  let api = $state();
  let showForm = $state<boolean>(false);
  let newRow = $state<Record<string, any>>({});

  function addRow() {
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
      {#each columns as column}
        <Input label={column.header} />
      {/each}
      <button onclick={addRow}>Add</button>
    </form>
  </Modal>
</Willow>
