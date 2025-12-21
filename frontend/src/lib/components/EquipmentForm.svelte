<script lang="ts">
  import Input from "$lib/components/Input.svelte";
  import Select from "$lib/components/Select.svelte";

  let equipmentId: string | null = null;
  let equipmentConfidence: "high" | "medium" | "low" | null = null;

  const confidenceOptions = ["High", "Medium", "Low"];
  const statusOptions = ["Intact", "Damaged", "Destroyed"];
</script>

<form class="form">
  <Input label="Equipment" name="equipment" />
  <Select options={confidenceOptions} label="Confidence" value="high" />
  <Select options={statusOptions} label="Status" value="intact" />
</form>

<style>
  .form {
    display: flex;
    flex-direction: column;
    gap: var(--size-xs);
  }
</style>
