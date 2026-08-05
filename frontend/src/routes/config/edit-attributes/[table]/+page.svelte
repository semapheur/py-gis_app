<script lang="ts">
  import type { PageData } from "./$types";
  import { page } from "$app/state";
  import { browser } from "$app/environment";
  import DataGrid from "$lib/components/DataGrid.svelte";
  import type { DataGridColumn } from "$lib/utils/types";

  let { data }: { data: PageData } = $props();
  let table = $derived(page.params.table);

  const columns = [
    {
      id: "name",
      header: "Name",
      required: false,
      unique: true,
      editor: "text",
      flexgrow: 1,
    },
    {
      id: "description",
      header: "Description",
      required: true,
      editor: "textarea",
      flexgrow: 1,
    },
    {
      id: "ordering",
      header: "Ordering",
      required: true,
      editor: "number",
      flexgrow: 1,
    },
  ] satisfies DataGridColumn[];

  let insertApi = $derived(`/api/insert-attribute/${table}`);
  let updateApi = $derived(`/api/update-attribute/${table}`);
  let deleteApi = $derived(`/api/delete-attribute/${table}`);
</script>

{#if browser}
  <DataGrid {columns} data={data.data} {insertApi} {updateApi} {deleteApi} />
{/if}
