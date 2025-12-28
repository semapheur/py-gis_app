<script lang="ts">
  import EquipmentForm from "$lib/components/EquipmentForm.svelte";
  import ActivityForm from "$lib/components/ActivityForm.svelte";
  import Select from "$lib/components/Select.svelte";
  import Tabs from "$lib/components/Tabs.svelte";

  import {
    annotateTabs,
    annotateGeometryByForm,
    type EquipmentData,
    type AnnotateForm,
    type AnnotateGeometry,
    type DrawConfig,
  } from "$lib/utils/types";

  interface Props {
    open: boolean;
    drawConfig: DrawConfig;
    formData: EquipmentData | null;
  }

  let {
    open = $bindable(),
    drawConfig = $bindable(),
    formData = $bindable(),
  }: Props = $props();

  let validForm = $state<boolean>(false);
  let annotateOptions = $derived(annotateGeometryByForm[drawConfig.layer]);

  let formRef = $state<EquipmentForm | null>(null);

  function handleCommit(data: EquipmentData) {
    formData = data;
  }

  $effect(() => {
    drawConfig.geometry = annotateOptions[0].value;

    if (!open && drawConfig.enabled) {
      drawConfig.enabled = false;
    }
  });
</script>

{#if open}
  <div class="container">
    <header class="header">
      <Tabs tabs={annotateTabs} bind:selected={drawConfig.layer} />
      <button class="button-close" onclick={() => (open = false)}> ✕ </button>
    </header>
    <main>
      {#key drawConfig.layer}
        {#if drawConfig.layer === "equipment"}
          <EquipmentForm
            bind:this={formRef}
            data={formData}
            oncommit={handleCommit}
            onvalid={(v) => (validForm = v)}
            autoCommit={true}
          />
        {:else if drawConfig.layer === "activity"}
          <ActivityForm />
        {/if}
      {/key}
    </main>
    <footer class="footer">
      {#key drawConfig.layer}
        <Select
          label="Geometry"
          options={annotateOptions}
          bind:value={drawConfig.geometry}
        />
      {/key}
      <button
        class="button-annotate"
        class:draw={drawConfig.enabled}
        disabled={!validForm}
        onclick={() => (drawConfig.enabled = !drawConfig.enabled)}
      >
        {drawConfig.enabled ? "Stop" : "Annotate"}
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
