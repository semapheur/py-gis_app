<script lang="ts">
  import { Grid } from "@svar-ui/svelte-grid";
  import { Willow } from "@svar-ui/svelte-core";

  const typeOptions = [
    { id: "vehicle", label: "Vehicle" },
    { id: "vessel", label: "Vessel" },
    { id: "submarine", label: "Submarine" },
    { id: "aircraft", label: "Aircraft" },
  ];

  const columns = [
    {
      id: "type",
      header: "Type",
      editor: "combo",
      options: typeOptions,
    },
  ];

  const data = [{ type: "vehicle" }];
</script>

<Willow>
  <Grid {data} {columns} />
</Willow>
