<script lang="ts">
  import { onMount } from "svelte";
  import FilterOutlineIcon from "@iconify-svelte/mdi/filter-outline";
  import ButtonIcon from "$lib/components/ButtonIcon.svelte";
  import Input from "$lib/components/Input.svelte";
  import { type ColumnDefinition } from "$lib/utils/types";

  type RowSelect = "none" | "single" | "multi";

  interface Props {
    data: Record<string, string | number | string[]>[];
    columns: ColumnDefinition[];
    selectable?: RowSelect;
    selected?: Record<string, string | number>[];
    onselectionchange?: (rows: Record<string, string | number>[]) => void;
    rowHeightRem?: number;
    overscan?: number;
  }

  let {
    data,
    columns,
    selectable = "none",
    selected = $bindable([]),
    onselectionchange,
    rowHeightRem = 1,
    overscan = 5,
  }: Props = $props();

  let rootFontSize = $state(16);
  let rowHeight = $derived(rowHeightRem * rootFontSize);
  let scrollTop = $state(0);
  let viewportHeight = $state(0);

  let openFilter = $state<string | null>(null);
  let filterSearch = $state<Record<string, string>>({});
  let checkedValues = $state<Record<string, Set<string>>>({});
  let sortKey = $state<string | null>(null);
  let sortOrder = $state<"asc" | "desc">("asc");
  let selectedRows = $state<Set<number>>(new Set());
  let lastSelectedIndex = $state<number | null>(null);

  const columnValues = $derived(
    Object.fromEntries(
      columns
        .filter((c) => c.filterable)
        .map((c) => [
          c.id,
          [
            ...new Set(
              data.flatMap((r) => {
                const v = r[c.id];
                return Array.isArray(v) ? v.map(String) : [String(v)];
              }),
            ),
          ].sort(),
        ]),
    ),
  );

  function toggleSort(colId: string) {
    if (sortKey === colId) {
      sortOrder = sortOrder === "asc" ? "desc" : "asc";
    } else {
      sortKey = colId;
      sortOrder = "asc";
    }
  }

  function getChecked(colId: string): Set<string> {
    return checkedValues[colId] ?? new Set(columnValues[colId]);
  }

  function toggleValue(colId: string, value: string) {
    const current = getChecked(colId);
    const next = new Set(current);
    next.has(value) ? next.delete(value) : next.add(value);
    checkedValues[colId] = next;
  }

  function isAllChecked(colId: string) {
    const checked = getChecked(colId);
    return columnValues[colId].every((v) => checked.has(v));
  }

  function toggleAll(colId: string) {
    if (isAllChecked(colId)) {
      checkedValues[colId] = new Set();
    } else {
      checkedValues[colId] = new Set(columnValues[colId]);
    }
  }

  function isFilterActive(colId: string) {
    return !isAllChecked(colId);
  }

  function closeFilter() {
    openFilter = null;
  }

  const processedData = $derived.by(() => {
    let rows = [...data];

    for (const col of columns.filter((c) => c.filterable)) {
      if (isFilterActive(col.id)) {
        const checked = getChecked(col.id);
        rows = rows.filter((r) => {
          const v = r[col.id];
          if (Array.isArray(v)) {
            return v.length === 0
              ? checked.has("")
              : v.some((item) => checked.has(String(item)));
          }
          return checked.has(String(r[col.id]));
        });
      }
    }

    if (sortKey) {
      const key = sortKey;
      const order = sortOrder === "asc" ? 1 : -1;
      rows.sort((a, b) => {
        const av = a[key];
        const bv = b[key];

        if (typeof av === "number" && typeof bv === "number") {
          return (av - bv) * order;
        }

        const aStr = Array.isArray(av) ? av.join(", ") : String(av);
        const bStr = Array.isArray(bv) ? bv.join(", ") : String(bv);

        return aStr.localeCompare(bStr) * order;
      });
    }

    return rows;
  });

  function toggleRow(index: number, event?: MouseEvent) {
    if (selectable === "none") return;

    const next = new Set(selectedRows);
    const ctrl = event?.ctrlKey || event?.metaKey;
    const shift = event?.shiftKey;

    if (selectable === "single") {
      if (next.has(index)) {
        next.clear();
      } else {
        next.clear();
        next.add(index);
      }
    } else {
      if (shift && lastSelectedIndex !== null) {
        const fromRow = Math.min(lastSelectedIndex, index);
        const toRow = Math.max(lastSelectedIndex, index);
        for (let i = fromRow; i <= toRow; i++) {
          next.add(i);
        }
      } else if (ctrl) {
        next.has(index) ? next.delete(index) : next.add(index);
        lastSelectedIndex = index;
      } else {
        next.clear();
        next.add(index);
        lastSelectedIndex = index;
      }
    }

    selectedRows = next;
    selected = processedData.filter((_, i) => next.has(i));
    onselectionchange?.(selected);
  }

  function toggleAllRows() {
    if (selectedRows.size === processedData.length) {
      selectedRows = new Set();
    } else {
      selectedRows = new Set(processedData.map((_, i) => i));
    }

    selected = processedData.filter((_, i) => selectedRows.has(i));
    onselectionchange?.(selected);
  }

  function onScroll(e: Event) {
    scrollTop = (e.target as HTMLDivElement).scrollTop;
  }

  let totalRows = $derived(processedData.length);
  const startIndex = $derived(
    Math.max(0, Math.floor(scrollTop / rowHeight) - overscan),
  );
  const visibleCount = $derived(
    Math.ceil(viewportHeight / rowHeight) + overscan * 2,
  );
  const endIndex = $derived(Math.min(totalRows, startIndex + visibleCount));
  const visibleRows = $derived(
    processedData
      .slice(startIndex, endIndex)
      .map((record, i) => ({ record, index: startIndex + i })),
  );
  const topSpacerHeight = $derived(startIndex * rowHeight);
  const bottomSpacerHeight = $derived((totalRows - endIndex) * rowHeight);
  const colCount = $derived(columns.length + (selectable !== "none" ? 1 : 0));

  $effect(() => {
    processedData;
    selectedRows = new Set();
    selected = [];
    lastSelectedIndex = null;
  });

  onMount(() => {
    const updateRootFontSize = () => {
      rootFontSize = parseFloat(
        getComputedStyle(document.documentElement).fontSize,
      );
    };
    updateRootFontSize();
    window.addEventListener("resize", updateRootFontSize);
    return () => window.removeEventListener("resize", updateRootFontSize);
  });
</script>

<svelte:window onclick={closeFilter} />

<div class="table-wrap" bind:clientHeight={viewportHeight} onscroll={onScroll}>
  <table>
    <thead>
      <tr>
        {#if selectable === "multi"}
          <th class="select-col">
            <input
              type="checkbox"
              checked={processedData.length > 0 &&
                selectedRows.size === processedData.length}
              indeterminate={selectedRows.size > 0 &&
                selectedRows.size < processedData.length}
              onchange={toggleAllRows}
            />
          </th>
        {:else if selectable === "single"}
          <th class="select-col"></th>
        {/if}
        {#each columns as c}
          <th>
            <div class="th-inner">
              <span class={{ "filter-active": isFilterActive(c.id) }}>
                {c.label}
              </span>
              {#if c.filterable}
                <div class="filter-wrap">
                  <ButtonIcon
                    onclick={(e) => {
                      e.stopPropagation();
                      openFilter = openFilter === c.id ? null : c.id;
                    }}><FilterOutlineIcon height="1rem" /></ButtonIcon
                  >
                  {#if openFilter === c.id}
                    <div
                      class="filter-dropdown"
                      role="presentation"
                      onclick={(e) => e.stopPropagation()}
                      onkeydown={() => {}}
                    >
                      <Input
                        type="text"
                        placeholder="Search"
                        bind:value={filterSearch[c.id]}
                      />
                      <ul>
                        <li>
                          <label>
                            <input
                              type="checkbox"
                              checked={isAllChecked(c.id)}
                              onchange={() => toggleAll(c.id)}
                            />
                            Select all
                          </label>
                        </li>
                        {#each columnValues[c.id].filter((v) => !filterSearch[c.id] || v
                              .toLowerCase()
                              .includes(filterSearch[c.id].toLowerCase())) as value}
                          <li>
                            <label>
                              <input
                                type="checkbox"
                                checked={getChecked(c.id).has(value)}
                                onchange={() => toggleValue(c.id, value)}
                              />
                              {value}
                            </label>
                          </li>
                        {/each}
                      </ul>
                    </div>
                  {/if}
                </div>
              {/if}
              {#if c.sortable}
                <button class="sort" onclick={() => toggleSort(c.id)}>
                  <span class="arrows">
                    <span
                      style="opacity: {sortKey === c.id && sortOrder === 'asc'
                        ? 1
                        : 0.3}">▲</span
                    >
                    <span
                      style="opacity: {sortKey === c.id && sortOrder === 'desc'
                        ? 1
                        : 0.3}">▼</span
                    >
                  </span>
                </button>
              {/if}
            </div>
          </th>
        {/each}
      </tr>
    </thead>
    <tbody>
      {#if topSpacerHeight > 0}
        <tr style="height: {topSpacerHeight}px;" aria-hidden="true">
          <td colspan={colCount}></td>
        </tr>
      {/if}
      {#each visibleRows as { record, index } (index)}
        <tr
          style="height: {rowHeightRem}rem;"
          class={{
            selected: selectedRows.has(index),
            selectable: selectable !== "none",
          }}
          onclick={(e) => toggleRow(index, e)}
        >
          {#if selectable === "multi"}
            <td class="select-col">
              <input
                type="checkbox"
                checked={selectedRows.has(index)}
                onclick={(e) => {
                  e.stopPropagation();
                  e.preventDefault();
                }}
              />
            </td>
          {:else if selectable === "single"}
            <td class="select-col">
              <input
                type="radio"
                checked={selectedRows.has(index)}
                onclick={(e) => e.stopPropagation()}
              />
            </td>
          {/if}
          {#each columns as c}
            <td>{record[c.id]}</td>
          {/each}
        </tr>
      {/each}
      {#if bottomSpacerHeight > 0}
        <tr style="height: {bottomSpacerHeight}px;" aria-hidden="true">
          <td colspan={colCount}></td>
        </tr>
      {/if}
    </tbody>
  </table>
</div>

<style>
  .table-wrap {
    overflow: auto;
    width: 100%;
    height: 100%;
  }

  table {
    width: max-content;
    min-width: 100%;
    border-collapse: collapse;
    font-size: var(--text-sm);
  }

  th {
    position: sticky;
    top: 0;
    background-color: oklch(var(--color-primary));
    z-index: 1;
  }

  tr.selectable {
    cursor: pointer;
  }

  tr.selectable:hover td {
    background: oklch(var(--color-secondary-accent) / 0.1);
  }

  tr.selected td {
    background: oklch(var(--color-secondary-accent));
  }

  .th-inner {
    display: flex;
    align-items: center;
    gap: var(--size-xs);
  }

  .filter-wrap {
    position: relative;
    display: inline-flex;
    align-items: center;
  }

  .filter-dropdown {
    position: absolute;
    top: 100%;
    left: 0;
    z-index: 1;
    min-width: 10rem;
    padding: var(--size-sm);
    margin-top: var(--size-md);
    background: oklch(var(--color-primary-accent));
    border-radius: var(--size-md);
  }

  .filter-active {
    color: oklch(var(--color-secondary));
  }

  ul {
    list-style: none;
    margin: 0;
    padding: 0;
    max-height: 10rem;
    overflow-y: auto;
  }

  li label {
    display: flex;
    align-items: center;
    gap: var(--size-sm);
    padding: var(--size-sm);
    border-radius: var(--size-md);
    cursor: pointer;
    font-size: var(--text-sm);
  }

  li label:hover {
    background: oklch(var(--color-text) / 0.08);
  }

  .sort {
    background: none;
    border: none;
    color: oklch(var(--color-text));
    cursor: pointer;
  }

  .arrows {
    display: inline-flex;
    flex-direction: column;
    font-size: var(--text-3xs);
    vertical-align: middle;
  }
</style>
