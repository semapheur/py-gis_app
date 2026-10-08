<script lang="ts">
  import type { PageData } from "./$types";
  import { browser } from '$app/env';
  import DataGrid from "#lib/components/DataGrid.svelte";
  import { fetchMsgpack } from "#lib/utils/fetch.js";
  import type { DataGridColumn } from "#lib/utils/types.js";

  async function validateCatalogPath(input: string) {
    const result = await fetchMsgpack<void, { path: string }>(
      "/api/validate-catalog-dir",
      {
        method: "POST",
        body: { path: input },
      },
    );

    if (result.ok) return true;

    throw new Error(
      result.error.message ?? `Validation failed (${result.error.status})`,
    );
  }

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
      id: "path",
      header: "Folder path",
      required: false,
      unique: true,
      editor: "text",
      flexgrow: 1,
      validate: validateCatalogPath,
    },
  ] satisfies DataGridColumn[];

  let { data }: { data: PageData } = $props();
</script>

{#if browser}
  <DataGrid
    columns={columns}
    data={data.catalogs}
    insertApi="/api/insert-catalog"
    updateApi="/api/update-catalog"
    deleteApi=""
  />
{/if}
