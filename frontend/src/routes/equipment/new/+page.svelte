<script lang="ts">
  import Button from "$lib/components/Button.svelte";
  import Input from "$lib/components/Input.svelte";
  import Select from "$lib/components/Select.svelte";
  import UnitInput from "$lib/components/UnitInput.svelte";

  interface DesignationRow {
    designation: string;
    designationType: (typeof designationTypes)[number]["value"];
    script: (typeof scriptOptions)[number]["value"];
  }

  interface DimensionRow {
    meters: number;
    dimensionType: (typeof dimensionTypes)[number]["value"];
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

  const dimensionTypes = [
    { label: "Hull length", value: "length_hull" },
    { label: "Overal length (gun forward)", value: "length_overall" },
    { label: "beam", value: "beam" },
  ] as const;

  let identifier = $state<string | null>(null);
  let displayName = $state<string | null>(null);
  let designations = $state<DesignationRow[]>([]);
  let dimensions = $state<DimensionRow[]>([]);

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

  function addDimension() {
    dimensions.push({
      meters: 0,
      dimensionType: dimensionTypes[0].value,
    });
  }

  function removeDimension(index: number) {
    dimensions.splice(index, 1);
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
  <fieldset>
    <legend>Dimension</legend>
    <UnitInput
      units={def.units}
      placeholder="Measure"
      min="0"
      bind:unit={numericUnits[key]}
      bind:value={
        () =>
          value[key] != null
            ? Math.round(((value[key] as number) / factorFor(key, def)) * 1e6) /
              1e6
            : null,
        () => {}
      }
      bind:baseValue={
        () => (value[key] as number | null) ?? null,
        (v) => update(key, v ?? (bulk ? undefined : null))
      }
    />
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
    gap: var(--size-md);
  }
</style>
