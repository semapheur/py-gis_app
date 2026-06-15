<script lang="ts">
  import type { PageData } from "./$types";
  import { page } from "$app/state";
  import { browser } from "$app/environment";
  import DataGrid from "$lib/components/DataGrid.svelte";

  let { data }: { data: PageData } = $props();
  let table = $derived(page.params.table);

  const columns = [
    ...(table !== "schema"
      ? [
          {
            id: "schema",
            header: "Schema",
            editor: "select",
            options: data.schemaOptions,
            flexgrow: 1,
          },
        ]
      : []),
    { id: "name", header: "Name", editor: "text", unique: true, flexgrow: 1 },
    {
      id: "description",
      header: "Description",
      editor: "textarea",
      flexgrow: 1,
    },
  ];

  let insertApi = $derived(`/api/insert-attribute/${table}`);
  let updateApi = $derived(`/api/update-attribute/${table}`);
  let deleteApi = $derived(`/api/delete-attribute/${table}`);
</script>

{#if browser}
  <DataGrid {columns} data={data.data} {insertApi} {updateApi} {deleteApi} />
{/if}
