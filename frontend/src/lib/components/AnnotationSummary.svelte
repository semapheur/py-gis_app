<script lang="ts">
  import Tabs from "#lib/components/Tabs.svelte";
  import EquipmentSummary from "#lib/components/EquipmentSummary.svelte";
  import CloseButton from "#lib/components/CloseButton.svelte";

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
  <dev class="annotation-summary">
    <header class="header">
      <CloseButton onclick={() => (open = false)} />
      <Tabs
        tabs={summaryTabs}
        selected={activeTab}
        onselect={(tab) => (activeTab = tab as SummaryTabs)}
      />
    </header>
    {#if activeTab === "equipment"}
      <EquipmentSummary />
    {/if}
  </dev>
{/if}

<style>
  .annotation-summary {
    height: 100%;
  }

  .header {
    display: flex;
    justify-content: start;
    gap: var(--size-md);
    border-bottom: 1px solid oklch(var(--color-text) / 0.5);
  }
</style>
