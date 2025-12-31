<script lang="ts">
  import Tabs from "$lib/components/Tabs.svelte";
  import EquipmentSummary from "$lib/components/EquipmentSummary.svelte";

  const summaryTabs = [
    { name: "Equipment", value: "equipment" },
    { name: "Activity", value: "activity" },
  ] as const;
  type SummaryTabs = (typeof summaryTabs)[number]["value"];

  interface Props {
    open: boolean;
  }

  let { open = $bindable() }: Props = $props();
  let activeTab = $state<SummaryTabs>("equipment");
</script>

{#if open}
  <aside class="summary-sidebar">
    <header class="header">
      <button class="button-close" onclick={() => (open = false)}> ✕ </button>
      <Tabs
        tabs={summaryTabs}
        selected={activeTab}
        onselect={(tab) => (activeTab = tab as SummaryTabs)}
      />
    </header>
    {#if activeTab === "equipment"}
      <EquipmentSummary />
    {/if}
  </aside>
{/if}

<style>
  .summary-sidebar {
    height: 100%;
    width: clamp(200px, 25%, 600px);
    position: absolute;
    top: 0;
    right: 0;
    padding: 0 var(--size-lg);
    background: rgb(var(--color-primary));
  }

  .header {
    display: flex;
    justify-content: start;
    gap: var(--size-md);
    border-bottom: 1px solid rgba(var(--color-text) / 0.5);
  }

  .button-close {
    all: unset;

    &:hover {
      color: red;
    }
  }
</style>
