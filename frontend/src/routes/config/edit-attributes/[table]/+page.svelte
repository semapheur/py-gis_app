<script lang="ts">
  import type { PageData } from "./$types";
  import { page } from "$app/state";
  import { browser } from "$app/environment";
  import DataGrid from "$lib/components/DataGrid.svelte";
  import type { AttributeData, SchemaBaseData } from "$lib/utils/types";

  let { data }: { data: PageData } = $props();
  let table = $derived(page.params.table);

  let columns = $derived([
    ...(table !== "schema"
      ? [
          {
            id: "schema",
            header: "Schema",
            nullable: false,
            editor: "select",
            template: (v: SchemaBaseData) => v.name,
            selectOptions: data.schemaOptions,
            flexgrow: 1,
          },
        ]
      : []),
    {
      id: "name",
      header: "Name",
      nullable: false,
      unique: table === "schema",
      editor: "text",
      flexgrow: 1,
    },
    {
      id: "description",
      header: "Description",
      nullable: true,
      editor: "textarea",
      flexgrow: 1,
    },
  ]);

  let insertApi = $derived(`/api/insert-attribute/${table}`);
  let updateApi = $derived(`/api/update-attribute/${table}`);
  let deleteApi = $derived(`/api/delete-attribute/${table}`);

  function validateInputRow(
    inputRow: Partial<AttributeData>,
    existingRows: AttributeData[],
  ) {
    const duplicateSchemaNamePair = existingRows.some(
      (row) => row.schema === inputRow.schema && row.name === inputRow.name,
    );

    if (duplicateSchemaNamePair) {
      return {
        valid: false,
        message: `The combination (${inputRow.schema?.name}, ${inputRow.name}) already exists`,
      };
    }

    return {
      valid: true,
      message: null,
    };
  }
</script>

{#if browser}
  <DataGrid
    {columns}
    data={data.data}
    {insertApi}
    {updateApi}
    {deleteApi}
    validateInputRow={table !== "schema" ? validateInputRow : undefined}
  />
{/if}
