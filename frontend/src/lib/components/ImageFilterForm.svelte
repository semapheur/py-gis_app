<script lang="ts">
  import DaterangePicker from "$lib/components/DaterangePicker.svelte";
  import Input from "$lib/components/Input.svelte";
  import Button from "$lib/components/Button.svelte";

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

<form class="form" on:submit={submitForm}>
  <Button>Filter</Button>
  <Input placeholder="File name" name="filename" value={filename} />
  <Input
    placeholder="Min coverage"
    name="coverage"
    value={coverage}
    type="number"
    min="0"
    max="100"
  />
  <Input
    placeholder="Min IIRS"
    type="number"
    value={iirs}
    min="0"
    max="9"
    name="min_iirs"
  />
  <Input
    placeholder="Max GSD"
    name="max_gsd"
    type="number"
    value={gsd}
    min="0"
  />
  <DaterangePicker bind:selectedRange={dateRange} />
</form>

<style>
  .form {
    display: flex;
    flex-wrap: wrap;
    gap: 0.2rem;
    width: 100%;
  }
</style>
