<script lang="ts">
  import type { PageData } from "./$types";
  import { page } from "$app/state";
  import { browser } from "$app/env";
  import DataGrid from "#lib/components/DataGrid.svelte";

  let { data }: { data: PageData } = $props();
  let table = $derived(page.params.table);

  const commonColumns = {
    name: {
      id: "name",
      header: "Name",
      nullable: false,
      unique: true,
      editor: "text",
      flexgrow: 1,
    },
    short_name: {
      id: "short_name",
      header: "Short name",
      nullable: false,
      unique: true,
      editor: "text",
      flexgrow: 1,
    },
    ordering: {
      id: "ordering",
      header: "Ordering",
      nullable: true,
      editor: "number",
      flexgrow: 1,
    },
  };

  let columns = $derived.by(() => {
    if (table === undefined) return [];

    const tableColumns = {
      classification: [
        commonColumns.name,
        commonColumns.short_name,
        {
          id: "level",
          header: "Level",
          nullable: false,
          unique: true,
          editor: "number",
          flexgrow: 1,
        },
        commonColumns.ordering,
      ],
      keyword: [
        commonColumns.name,
        commonColumns.short_name,
        commonColumns.ordering,
      ],
      partner: [
        commonColumns.name,
        commonColumns.short_name,
        {
          id: "type",
          header: "Type", // Note: check if header should be "Type" instead
          nullable: false,
          unique: true,
          editor: "select",
          selectOptions: ["Country", "Group"],
          flexgrow: 1,
        },
        {
          id: "member",
          header: "Members",
          nullable: false,
          unique: true,
          editor: "text",
          flexgrow: 1,
        },
      ],
    };

    return tableColumns[table] ?? [];
  });

  let insertApi = $derived(`/api/insert-security/${table}`);
  let updateApi = $derived(`/api/update-security/${table}`);
  let deleteApi = $derived(`/api/delete-security/${table}`);
</script>

{#if browser}
  <DataGrid {columns} data={data.data} {insertApi} {updateApi} {deleteApi} />
{/if}
