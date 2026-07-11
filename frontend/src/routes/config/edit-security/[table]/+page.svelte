<script lang="ts">
  import type { PageData } from "./$types";
  import { page } from "$app/state";
  import { browser } from "$app/environment";
  import DataGrid from "$lib/components/DataGrid.svelte";
  import type { SecurityData } from "$lib/utils/types";

  let { data }: { data: PageData } = $props();
  let table = $derived(page.params.table);

  let columns = $derived([
    {
      id: "name",
      header: "Name",
      nullable: false,
      unique: true,
      editor: "text",
      flexgrow: 1,
    },
    {
      id: "level",
      header: "Level",
      nullable: false,
      unique: true,
      editor: "number",
      flexgrow: 1,
    },
    {
      id: "ordering",
      header: "Ordering",
      nullable: true,
      editor: "number",
      flexgrow: 1,
    },
  ]);

  let insertApi = $derived(`/api/insert-security/${table}`);
  let updateApi = $derived(`/api/update-security/${table}`);
  let deleteApi = $derived(`/api/delete-security/${table}`);
</script>

{#if browser}
  <DataGrid
    {columns}
    data={data.data}
    {insertApi}
    {updateApi}
    {deleteApi}
  />
{/if}
