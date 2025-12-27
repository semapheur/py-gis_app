<script lang="ts">
  import Feature from "ol/Feature";

  import EquipmentForm from "$lib/components/EquipmentForm.svelte";
  import ActivityForm from "$lib/components/ActivityForm.svelte";
  import KebabMenu from "$lib/components/KebabMenu.svelte";

  import { type EquipmentData } from "$lib/utils/types";

  interface Props {
    selectedAnnotations: Feature[];
    onDelete: (feature: Feature) => void;
  }

  let { selectedAnnotations, onDelete }: Props = $props();

  let selectedIndex = $state<number | null>(null);
  let validForm = $state<boolean>(true);
  let editData = $state<EquipmentData | null>(null);
  let formRef = $state<EquipmentForm | null>(null);

  const labels = $derived(
    selectedAnnotations.map((f) => f.get("label")?.replace("\n", ", ")),
  );
  const selectedFeature = $derived(
    selectedIndex !== null
      ? (selectedAnnotations[selectedIndex] ?? null)
      : null,
  );
  const selectedType = $derived(selectedFeature?.get("type") ?? null);

  $effect(() => {
    if (!selectedFeature) return;

    const data = selectedFeature.get("data");
    editData = data ?? null;
  });

  function handleCommit(data: EquipmentData) {
    if (!selectedFeature) return;

    selectedFeature.set("data", data);
    const label =
      selectedType === "equipment"
        ? `${data.id}\n${data.status}\n${data.confidence}`
        : "";

    selectedFeature.set("label", label);
    selectedFeature.changed();
    selectedAnnotations = [...selectedAnnotations];
  }

  function saveEdits() {
    if (!formRef || !validForm) return;

    handleCommit(formRef.commit());
  }

  function deleteFeature() {
    if (!selectedFeature) return;

    onDelete(selectedFeature);
    selectedIndex = null;
  }
</script>

{#if selectedAnnotations.length > 0}
  <aside class="edit-sidebar">
    <header class="edit-header">
      <KebabMenu>
        <button role="menuitem">Export to GeoJSON</button>
        <button role="menuitem">Bulk edit</button>
        <button role="menuitem">Bulk delete</button>
      </KebabMenu>
      <span class="edit-heading">Selected annotations</span>
    </header>
    <ol>
      {#each selectedAnnotations as annotation, i}
        <li>
          <label>
            <input type="radio" value={i} bind:group={selectedIndex} />
            {labels[i]}
          </label>
        </li>
      {/each}
    </ol>
    {#if editData}
      {#key selectedIndex}
        {#if selectedType === "equipment"}
          <EquipmentForm
            bind:this={formRef}
            data={editData}
            oncommit={handleCommit}
            onvalid={(v) => (validForm = v)}
            autoCommit={false}
          />
        {:else if selectedType === "activity"}
          <ActivityForm />
        {/if}
      {/key}
      <footer class="edit-footer">
        <button class="button-save" disabled={!validForm} onclick={saveEdits}>
          Save
        </button>
        <button class="button-delete" onclick={deleteFeature}> Delete </button>
      </footer>
    {/if}
  </aside>
{/if}

<style>
  .edit-sidebar {
    height: 100%;
    width: clamp(200px, 25%, 600px);
    position: absolute;
    top: 0;
    right: 0;
    background: rgb(var(--color-primary));
  }

  .edit-header {
    display: flex;
    gap: var(--size-md);
    border-bottom: 1px solid rgb(var(--color-text));
  }

  .edit-heading {
    margin: 0;
    font-size: var(--text-lg);
    font-weight: var(--font-bold);
  }

  .button-save {
    background: rgba(var(--color-positive) / 0.8);
  }

  .button-delete {
    background: rgba(var(--color-negative) / 0.8);
  }
</style>
