<script lang="ts">
  import Button from "$lib/components/Button.svelte";
  import Input from "$lib/components/Input.svelte";
  import Select from "$lib/components/Select.svelte";

  interface DesignationRow {
    designation: string;
    designationType: (typeof designationTypes)[number]["value"];
    script: (typeof scriptOptions)[number]["value"];
  }

  const designationTypes = [
    { label: "Serial name", value: "serial_name" },
    { label: "Native nickname", value: "native_nickname" },
    { label: "GRAU index", value: "grau_index" },
    { label: "NATO code", value: "nato_code" },
    { label: "NATO nickname", value: "nato_nickname" },
  ] as const;

  const scriptOptions = [
    { label: "Latin", value: "latin" },
    { label: "Cyrillic", value: "cyrillic" },
  ] as const;

  let identifier = $state<string | null>(null);
  let displayName = $state<string | null>(null);
  let designations = $state<DesignationRow[]>([]);

  function addDesignation() {
    designations.push({
      designation: "",
      designationType: designationTypes[0].value,
      script: scriptOptions[0].value,
    });
  }

  function removeDesignation(index: number) {
    designations.splice(index, 1);
  }

  async function handleSubmit() {
    const payload = {
      display_name: displayName,
      designations: designations
        .filter((d) => d.designation.trim() !== "")
        .map((d) => ({
          designation: d.designation,
          designation_type: d.designationType,
          script: d.script,
        })),
    };
  }
</script>

<div>
  <Input bind:value={identifier} placeholder="Identifier" />
  <Input bind:value={displayName} placeholder="Display name" />

  <fieldset>
    <legend>Designations</legend>
    {#each designations as row, i (i)}
      <div class="designation-row">
        <div class="designation-fields">
          <Input bind:value={row.designation} placeholder="Designation" />
          <Select
            bind:value={row.designationType}
            options={designationTypes}
            placeholder="Type"
          />
          <Select
            bind:value={row.script}
            options={scriptOptions}
            placeholder="Language"
          />
        </div>
        <button
          type="button"
          onclick={() => removeDesignation(i)}
          disabled={designations.length === 1}
          aria-label="Remove designation"
        >
          ✕
        </button>
      </div>
    {/each}

    <Button type="button" onclick={addDesignation}>Add</Button>
  </fieldset>
  <Button type="submit">Save</Button>
</div>

<style>
  .designation-row {
    display: flex;
  }

  .designation-fields {
    display: flex;
    flex-direction: column;
    gap: var(--size-sm);
  }
</style>
