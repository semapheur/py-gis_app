<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import Input from "$lib/components/Input.svelte";
  import { type SelectOption } from "$lib/utils/types";
  import { createDebouncedSearch } from "$lib/contexts/debounce.svelte";

  interface Props {
    selected?: SelectOption[];
    placeholder?: string;
    fetchOptions: (query: string) => SelectOption[] | Promise<SelectOption[]>;
    onchange?: (value: SelectOption[]) => void;
    excludeValues?: SelectOption["value"][];
  }

  let {
    selected = $bindable([]),
    placeholder,
    fetchOptions,
    onchange,
    excludeValues = [],
  }: Props = $props();

  let container: HTMLDivElement;

  const exclude = $derived([...selected.map((o) => o.value), ...excludeValues]);

  const search = createDebouncedSearch(fetchOptions, () => exclude);

  function select(option: SelectOption) {
    selected = [...selected, option];
    onchange?.(selected);
    search.query = "";
    search.open = false;
  }

  function removeOption(value: SelectOption["value"], e: Event) {
    e.stopPropagation();
    selected = selected.filter((o) => o.value !== value);
    onchange?.(selected);
  }

  function clearAll(e: Event) {
    e.stopPropagation();
    selected = [];
    onchange?.(selected);
  }

  function onblur() {
    setTimeout(() => {
      search.open = false;
    }, 150);
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === "Escape") {
      search.open = false;
    }
    if (e.key === "Backspace" && search.query === "" && selected.length) {
      selected = selected.slice(0, -1);
      onchange?.(selected);
    }
  }

  onMount(() => {
    document.addEventListener("keydown", handleKeydown);
  });
  onDestroy(() => {
    document.removeEventListener("keydown", handleKeydown);
  });
</script>

<div class="multi-autocomplete" bind:this={container}>
  <div class="ma-control">
    {#if selected.length}
      <div class="ma-tags">
        {#each selected as option}
          <span class="ma-tag">
            {option.label}
            <button
              type="button"
              class="ma-tag-remove"
              onclick={(e) => removeOption(option.value, e)}
              aria-label={`Remove ${option.label}`}>×</button
            >
          </span>
        {/each}
      </div>
    {/if}

    <Input
      bind:value={search.query}
      placeholder={selected.length ? "" : placeholder}
      {onblur}
    />

    {#if selected.length}
      <button
        type="button"
        class="ma-clear"
        onclick={clearAll}
        aria-label="Clear all">×</button
      >
    {/if}
  </div>

  {#if search.open && search.options?.length}
    <ul class="dropdown">
      {#each search.options as option}
        <li
          onpointerdown={(e) => {
            e.stopPropagation();
            select(option);
          }}
        >
          {option.label}
        </li>
      {/each}
    </ul>
  {/if}
</div>

<style>
  .multi-autocomplete {
    position: relative;
  }

  .ma-control {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: var(--size-sm);
    padding: var(--size-sm) var(--size-md);
    border: 1px solid oklch(var(--color-secondary));
    border-radius: var(--size-sm);
    background: oklch(var(--color-primary-accent));
  }

  .ma-control :global(input) {
    flex: 1;
    min-width: 4rem;
    border: none;
    background: transparent;
  }

  .ma-tags {
    display: flex;
    flex-wrap: wrap;
    gap: var(--size-sm);
  }

  .ma-tag {
    display: flex;
    align-items: center;
    gap: var(--size-sm);
    background: oklch(var(--color-primary));
    color: oklch(var(--color-text));
    padding: var(--size-xs) var(--size-sm);
    border-radius: var(--size-sm);
    font-size: var(--text-xs);
    white-space: nowrap;
  }

  .ma-tag-remove {
    border: none;
    background: none;
    color: oklch(var(--color-secondary));
    cursor: pointer;
    font-size: var(--text-sm);
    line-height: 1;
    padding: 0 var(--size-sm);
    border-radius: 50%;
  }

  .ma-tag-remove:hover {
    background: oklch(var(--color-secondary-accent));
  }

  .ma-clear {
    border: none;
    background: none;
    color: oklch(var(--color-text));
    cursor: pointer;
    font-size: var(--text-sm);
    line-height: 1;
    padding: 0 var(--size-xs);
    flex-shrink: 0;
  }

  .ma-clear:hover {
    color: oklch(var(--color-negative));
  }

  .dropdown {
    list-style: none;
    position: absolute;
    width: 100%;
    max-height: calc(10 * var(--text-xs));
    margin: 0;
    padding: 0;
    overflow-y: scroll;
    z-index: 10;
    background: oklch(var(--color-secondary-accent));
  }

  li {
    padding: 0 var(--size-md);
    cursor: pointer;
    font-size: var(--text-xs);
  }
</style>
