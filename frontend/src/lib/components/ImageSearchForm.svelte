<script lang="ts">
  import { page } from "$app/state";
  import { goto } from "$app/navigation";
  import * as v from "valibot";
  import Input from "$lib/components/Input.svelte";
  import Select from "$lib/components/Select.svelte";
  import Button from "$lib/components/Button.svelte";
  import DaterangePicker from "$lib/components/DaterangePicker.svelte";
  import AzimuthRangePicker from "$lib/components/AzimuthRangePicker.svelte";
  import NumberRangeInput from "$lib/components/NumberRangeInput.svelte";
  import { formatDate, parseIsoDate, type DateRange } from "$lib/utils/date";
  import { type AngleRange } from "$lib/utils/types";
  import {
    ORDERING_OPTIONS,
    ORDER_COLUMN_OPTIONS,
    orderingSchema,
    imageOrderColumnSchema,
  } from "$lib/utils/constants";

  const params = page.url.searchParams;
  let ordering = $state<(typeof ORDERING_OPTIONS)[number]["value"]>(
    v.is(orderingSchema, params.get("ordering"))
      ? params.get("ordering")
      : "desc",
  );
  let orderColumn = $state<(typeof ORDER_COLUMN_OPTIONS)[number]["value"]>(
    v.is(imageOrderColumnSchema, params.get("order_by"))
      ? params.get("order_by")
      : "datetime_collected",
  );
  let filename = $state<string | null>(params.get("filename") ?? null);
  let coverage = $state<number | null>(
    params.has("min_coverage") ? Number(params.get("min_coverage")) : null,
  );
  let iirs = $state<number | null>(
    params.has("min_iirs") ? Number(params.get("min_iirs")) : null,
  );
  let gsd = $state<number | null>(
    params.has("max_gsd") ? Number(params.get("max_gsd")) : null,
  );

  let dateRange = $state<DateRange | null>(
    params.has("date_start") && params.has("date_end")
      ? {
          start: parseIsoDate(params.get("date_start"))!,
          end: parseIsoDate(params.get("date_end"))!,
        }
      : null,
  );
  let azimuthRange = $state<AngleRange | null>(
    params.has("azimuth_start") && params.has("azimuth_end")
      ? {
          start: parseInt(params.get("azimuth_start")!),
          end: parseInt(params.get("azimuth_end")!),
        }
      : null,
  );
  let lookangle_min = $state<number | null>(
    params.has("lookangle_min") ? parseInt(params.get("lookangle_min")!) : null,
  );

  let lookangle_max = $state<number | null>(
    params.has("lookangle_max") ? parseInt(params.get("lookangle_max")!) : null,
  );

  async function submitForm(e: SubmitEvent) {
    e.preventDefault();

    const params = new URLSearchParams(page.url.searchParams);

    params.set("ordering", ordering);
    params.set("order_by", orderColumn);

    if (filename) params.set("filename", filename);
    else params.delete("filename");

    if (coverage !== null) params.set("min_coverage", coverage.toString());
    else params.delete("min_coverage");

    if (iirs !== null) params.set("min_iirs", iirs.toString());
    else params.delete("min_iirs");

    if (gsd !== null) params.set("max_gsd", gsd.toString());
    else params.delete("max_gsd");

    if (dateRange !== null) {
      params.set("date_start", formatDate(dateRange.start));
      params.set("date_end", formatDate(dateRange.end));
    } else {
      params.delete("date_start");
      params.delete("date_end");
    }

    if (lookangle_min !== null) {
      params.set("lookangle_min", lookangle_min.toString());
    } else {
      params.delete("lookangle_min");
    }

    if (lookangle_max !== null) {
      params.set("lookangle_min", lookangle_max.toString());
    } else {
      params.delete("lookangle_min");
    }

    goto(`?${params.toString()}`, { replaceState: true, keepFocus: true });
  }
</script>

<form class="form" onsubmit={submitForm}>
  <Button type="submit">Search</Button>
  <Select
    placeholder="Ordering"
    options={ORDERING_OPTIONS}
    name="ordering"
    bind:value={ordering}
  />
  <Select
    placeholder="Order column"
    options={ORDER_COLUMN_OPTIONS}
    name="order_by"
    bind:value={orderColumn}
  />
  <Input placeholder="File name" name="filename" bind:value={filename} />
  <Input
    placeholder="Min coverage (%)"
    name="min_coverage"
    bind:value={coverage}
    type="number"
    min="0"
    max="100"
  />
  <Input
    placeholder="Min IIRS (0-9)"
    name="min_iirs"
    type="number"
    bind:value={iirs}
    min="0"
    max="9"
    step="any"
  />
  <Input
    placeholder="Max GSD (m)"
    name="max_gsd"
    type="number"
    bind:value={gsd}
    min="0"
    step="any"
  />
  <DaterangePicker bind:selectedRange={dateRange} />
  <AzimuthRangePicker bind:selectedRange={azimuthRange} />
  <Input
    placeholder="Min look angle"
    name="min_lookangle"
    type="number"
    bind:value={lookangle_min}
    min="0"
    max="90"
  />
  <Input
    placeholder="Max look angle"
    name="max_lookangle"
    type="number"
    bind:value={lookangle_max}
    min="0"
    max="90"
  />
</form>

<style>
  .form {
    display: flex;
    flex-wrap: wrap;
    gap: var(--size-md);
    width: 100%;
  }
</style>
