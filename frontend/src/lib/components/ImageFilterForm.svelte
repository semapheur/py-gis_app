<script lang="ts">
  import { page } from "$app/state";
  import { goto } from "$app/navigation";
  import DaterangePicker from "$lib/components/DaterangePicker.svelte";
  import Input from "$lib/components/Input.svelte";
  import Button from "$lib/components/Button.svelte";
  import { formatDate, parseIsoDate, type DateRange } from "$lib/utils/date";

  const params = page.url.searchParams;
  let filename = $state<string | null>(params.get("filename") ?? null);
  let coverage = $state<number | null>(
    params.has("coverage") ? Number(params.get("coverage")) : null,
  );
  let iirs = $state<number | null>(
    params.has("min_iirs") ? Number(params.get("min_iirs")) : null,
  );
  let gsd = $state<number | null>(
    params.has("max_gsd") ? Number(params.get("max_gsd")) : null,
  );

  let dateRange = $state<DateRange>({
    start: parseIsoDate(params.get("date_start")),
    end: parseIsoDate(params.get("date_end")),
  });

  let lastDateRangeKey = $state<string>("");

  $effect(() => {
    if (!dateRange.start || !dateRange.end) return;

    const start = formatDate(dateRange.start);
    const end = formatDate(dateRange.end);
    const key = `${start}_${end}`;

    if (key === lastDateRangeKey) return;
    lastDateRangeKey = key;

    const params = new URLSearchParams(page.url.searchParams);
    if (dateRange.start) params.set("date_start", start);
    else params.delete("date_start");

    if (dateRange.end) params.set("date_end", end);
    else params.delete("date_end");

    goto(`?${params.toString()}`, { replaceState: true, keepFocus: true });
  });

  async function submitForm(e: SubmitEvent) {
    e.preventDefault();

    const params = new URLSearchParams(page.url.searchParams);

    if (filename) params.set("filename", filename);
    else params.delete("filename");

    if (coverage !== null) params.set("coverage", String(coverage));
    else params.delete("coverage");

    if (iirs !== null) params.set("min_iirs", String(iirs));
    else params.delete("min_iirs");

    if (gsd !== null) params.set("max_gsd", String(gsd));
    else params.delete("max_gsd");

    goto(`?${params.toString()}`, { replaceState: true, keepFocus: true });

    const payload = {
      filename: filename,
      min_iirs: iirs,
      max_gsd: gsd,
      daterange: dateRange,
    };

    //const res = await fetch("http://localhost:8000/api/filter-images", {
    //  method: "POST",
    //  headers: { "Content-Type": "application/json" },
    //  body: JSON.stringify(payload),
    //});
    //
    //const data = await res.json();
  }
</script>

<form class="form" onsubmit={submitForm}>
  <Button type="submit">Filter</Button>
  <Input placeholder="File name" name="filename" bind:value={filename} />
  <Input
    placeholder="Min coverage"
    name="coverage"
    bind:value={coverage}
    type="number"
    min="0"
    max="100"
  />
  <Input
    placeholder="Min IIRS"
    type="number"
    bind:value={iirs}
    min="0"
    max="9"
    name="min_iirs"
  />
  <Input
    placeholder="Max GSD"
    name="max_gsd"
    type="number"
    bind:value={gsd}
    min="0"
    step="any"
  />
  <DaterangePicker bind:selectedRange={dateRange} />
</form>

<style>
  .form {
    display: flex;
    flex-wrap: wrap;
    gap: var(--size-md);
    width: 100%;
  }
</style>
