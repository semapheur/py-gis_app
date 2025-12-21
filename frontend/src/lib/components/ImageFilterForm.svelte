<script lang="ts">
  import DaterangePicker from "$lib/components/DaterangePicker.svelte";
  import Input from "$lib/components/Input.svelte";

  let filename: string | null = null;
  let coverage: number | null = null;
  let iirs: number | null = null;
  let gsd: number | null = null;

  let dateRange = { start: null, end: null };

  async function submitForm(e: SubmitEvent) {
    e.preventDefault();

    const payload = {
      filename: filename,
      min_iirs: iirs,
      max_gsd: gsd,
      daterange: dateRange,
    };

    const res = await fetch("http://localhost:8000/api/filter-images", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await res.json();
  }
</script>

<div class="container">
  <form class="form" on:submit={submitForm}>
    <Input label="File name" name="filename" bind:value={filename} />
    <Input label="Min coverage" name="coverage" bind:value={coverage} />
    <Input
      label="Min IIRS"
      type="number"
      min="0"
      max="9"
      name="min_iirs"
      bind:value={iirs}
    />
    <Input
      label="Max GSD"
      type="number"
      min="0"
      name="max_gsd"
      bind:value={gsd}
    />
    <DaterangePicker bind:selectedRange={dateRange} />
  </form>
</div>

<style>
  .container {
    width: 100%;
    display: flex;
    flex-direction: column;
    padding: 0.5rem;
  }

  .form {
    display: flex;
    gap: 0.2rem;
  }
</style>
