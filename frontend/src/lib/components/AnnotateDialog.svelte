<script lang="ts">
  import EquipmentForm from "$lib/components/EquipmentForm.svelte";
  import ActivityForm from "$lib/components/ActivityForm.svelte";
  import Select from "$lib/components/Select.svelte";
  import Tabs from "$lib/components/Tabs.svelte";

  interface Props {
    open: boolean;
  }

  let { open = $bindable() }: Props = $props();
  const tabs = [
    { name: "Equipment", value: "equipment" },
    { name: "Activity", value: "activity" },
  ];
  let currentTab = $state("equipment");

  const annotateOptions = [
    {
      label: "Point",
      value: "Point",
    },
    {
      label: "Polygon",
      value: "Polygon",
    },
  ];
</script>

{#if open}
  <div class="container">
    <header class="header">
      <Tabs {tabs} bind:selected={currentTab} />
      <button class="button-close" onclick={() => (open = false)}> ✕ </button>
    </header>
    <main>
      {#if currentTab === "equipment"}
        <EquipmentForm />
      {:else if currentTab === "activity"}
        <ActivityForm />
      {/if}
    </main>
    <footer class="footer">
      <Select label="Geometry" options={annotateOptions} />
      <button> Annotate </button>
    </footer>
  </div>
{/if}

<style>
  .container {
    position: absolute;
    display: flex;
    flex-direction: column;
    gap: var(--size-sm);
    bottom: var(--size-sm);
    left: var(--size-sm);
    z-index: 2;
    background: rgb(var(--color-primary));
    padding: var(--size-md);
  }

  .header {
    display: flex;
    justify-content: space-between;
    border-bottom: 1px solid rgba(var(--color-text) / 0.5);
  }

  .footer {
    display: flex;
  }

  .button-close {
    all: unset;

    &:hover {
      color: red;
    }
  }
</style>
