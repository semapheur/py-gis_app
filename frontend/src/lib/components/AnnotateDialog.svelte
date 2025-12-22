<script lang="ts">
  import EquipmentForm from "$lib/components/EquipmentForm.svelte";
  import ActivityForm from "$lib/components/ActivityForm.svelte";
  import Select from "$lib/components/Select.svelte";
  import Tabs from "$lib/components/Tabs.svelte";

  import {
    annotateTabs,
    annotateGeometryByForm,
    type AnnotateForm,
    type AnnotateGeometry,
  } from "$lib/utils/types";

  interface Props {
    open: boolean;
    drawMode: boolean;
    activeForm: AnnotateForm;
    drawGeometry: AnnotateGeometry<AnnotateForm>;
  }

  let {
    open = $bindable(),
    activeForm = $bindable(),
    drawMode = $bindable(),
    drawGeometry = $bindable(),
  }: Props = $props();

  let annotateOptions = $derived(annotateGeometryByForm[activeForm]);

  $effect(() => {
    drawGeometry = annotateOptions[0].value;

    if (!open && drawMode) {
      drawMode = false;
    }
  });
</script>

{#if open}
  <div class="container">
    <header class="header">
      <Tabs tabs={annotateTabs} bind:selected={activeForm} />
      <button class="button-close" onclick={() => (open = false)}> ✕ </button>
    </header>
    <main>
      {#if activeForm === "equipment"}
        <EquipmentForm />
      {:else if activeForm === "activity"}
        <ActivityForm />
      {/if}
    </main>
    <footer class="footer">
      {#key activeForm}
        <Select
          label="Geometry"
          options={annotateOptions}
          bind:value={drawGeometry}
        />
      {/key}
      <button
        class="button-annotate"
        class:draw={drawMode}
        onclick={() => (drawMode = !drawMode)}
      >
        {drawMode ? "Stop" : "Annotate"}
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
