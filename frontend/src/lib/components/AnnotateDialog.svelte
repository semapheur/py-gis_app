<script lang="ts">
  import EquipmentForm from "$lib/components/EquipmentForm.svelte";
  import ActivityForm from "$lib/components/ActivityForm.svelte";
  import Select from "$lib/components/Select.svelte";
  import Tabs from "$lib/components/Tabs.svelte";

  import {
    getAnnotateState,
    annotateTabs,
    type ActivityData,
    type EquipmentData,
  } from "$lib/contexts/annotate.svelte";

  interface Props {
    open: boolean;
  }

  let { open = $bindable() }: Props = $props();

  const annotate = getAnnotateState();

  $effect(() => {
    if (!open) annotate.stop();
  });
</script>

{#if open}
  <div class="container">
    <header class="header">
      <Tabs
        tabs={annotateTabs}
        selected={annotate.layer}
        onselect={(layer: typeof annotate.layer) => annotate.setLayer(layer)}
      />
      <button class="button-close" onclick={() => (open = false)}> ✕ </button>
    </header>
    <main>
      {#key annotate.layer}
        {#if annotate.layer === "equipment"}
          <EquipmentForm
            value={annotate.data as EquipmentData}
            onchange={(d) => annotate.setData(d)}
          />
        {:else if annotate.layer === "activity"}
          <ActivityForm
            value={annotate.data as ActivityData}
            onchange={(d) => annotate.setData(d)}
          />
        {/if}
      {/key}
    </main>
    <footer class="footer">
      {#key annotate.layer}
        <Select
          label="Geometry"
          options={annotate.geometryOptions}
          value={annotate.geometry}
          onchange={(v) => annotate.setGeometry(v)}
        />
      {/key}
      <button
        class="button-annotate"
        class:draw={annotate.active}
        disabled={!annotate.validData}
        onclick={() => annotate.toggleActive()}
      >
        {annotate.active ? "Stop" : "Annotate"}
      </button>
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
    border-radius: var(--size-md);
    padding: var(--size-md);
  }

  .header {
    display: flex;
    justify-content: space-between;
    border-bottom: 1px solid rgba(var(--color-text) / 0.5);
  }

  .footer {
    display: flex;
    justify-content: end;
    gap: var(--size-sm);
    padding-top: var(--size-sm);
    border-top: 1px solid rgba(var(--color-text) / 0.5);
  }

  .button-close {
    all: unset;

    &:hover {
      color: red;
    }
  }

  .button-annotate {
    background: rgba(var(--color-positive) / 0.8);

    &.draw {
      background: rgb(var(--color-negative));
    }
  }
</style>
