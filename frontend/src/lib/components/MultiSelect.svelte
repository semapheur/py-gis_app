<script lang="ts" generics="T = string">
  import type { SelectOption } from "$lib/utils/types";

  interface Props {
    options: SelectOption<T>[];
    selected: Array<T>;
    placeholder: string;
    label?: string;
    disabled?: boolean;
    searchable?: boolean;
    maxVisible?: number;
  }

  let {
    options,
    selected = $bindable([]),
    placeholder,
    label,
    disabled = false,
    searchable = true,
    maxVisible = 3,
  }: Props = $props();

  let open = $state<boolean>(false);
  let query = $state<string>("");
  let containerEl = $state<HTMLDivElement | null>(null);
  let activeIndex = $state<number>(-1);

  const filteredOptions = $derived(
    query.trim() === ""
      ? options
      : options.filter((o) =>
          o.label.toLowerCase().includes(query.trim().toLocaleLowerCase()),
        ),
  );

  const selectedSet = $derived(new Set(selected));

  function toggleOption(value: T) {
    if (selectedSet.has(value)) {
      selected = selected.filter((v) => v !== value);
    } else {
      selected = [...selected, value];
    }
  }

  function removeOption(value: T, e: Event) {
    e.stopPropagation();
    selected = selected.filter((v) => v !== value);
  }

  function clearAll(e: Event) {
    e.stopPropagation();
    selected = [];
    query = "";
  }

  function toggleOpen() {
    if (disabled) return;
    open = !open;
    if (open) activeIndex = 0;
  }

  function closeDropdown() {
    open = false;
    query = "";
    activeIndex = -1;
  }

  function handleKeydown(e: KeyboardEvent) {
    if (disabled) return;

    if (e.key === "Enter" || e.key === " ") {
      if (!open) {
        e.preventDefault();
        toggleOpen();
        return;
      }
      if (e.key === " " && document.activeElement?.tagName === "INPUT") return;
    }

    if (!open) {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        toggleOpen();
      }
      return;
    }

    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        activeIndex = Math.min(activeIndex + 1, filteredOptions.length - 1);
        break;
      case "ArrowUp":
        e.preventDefault();
        activeIndex = Math.max(activeIndex - 1, 0);
        break;
      case "Enter":
        e.preventDefault();
        if (filteredOptions[activeIndex]) {
          toggleOption(filteredOptions[activeIndex].value);
        }
        break;
      case "Escape":
        e.preventDefault();
        closeDropdown();
        break;
      case "Tab":
        closeDropdown();
        break;
    }
  }

  function handleClickOutside(e: MouseEvent) {
    if (containerEl && !containerEl.contains(e.target)) {
      closeDropdown();
    }
  }

  $effect(() => {
    if (open) {
      document.addEventListener("click", handleClickOutside);
      return () => document.removeEventListener("click", handleClickOutside);
    }
  });

  const selectedLabels = $derived(
    options.filter((o) => selectedSet.has(o.value)).map((o) => o.label),
  );
</script>

<div class="multiselect" bind:this={containerEl}>
  {#if label}
    <label class="ms-label" for="ms-trigger">{label}</label>
  {/if}

  <div
    id="ms-trigger"
    class="ms-control"
    class:open
    class:disabled
    role="combobox"
    aria-expanded={open}
    aria-haspopup="listbox"
    tabindex={disabled ? -1 : 0}
    onclick={toggleOpen}
    onkeydown={handleKeydown}
  >
    <div class="ms-tags">
      {#if selected.length === 0}
        <span class="ms-placeholder">{placeholder}</span>
      {:else if selected.length <= maxVisible}
        {#each selectedLabels as text, i}
          <span class="ms-tag">
            {text}
            <button
              type="button"
              class="ms-tag-remove"
              onclick={(e) => removeOption(selected[i], e)}
              aria-label={`Remove ${text}`}>×</button
            >
          </span>
        {/each}
      {:else}
        <span class="ms-tag ms-tag-count">
          {selected.length} selected
        </span>
      {/if}
    </div>

    <div class="ms-actions">
      {#if selected.length > 0}
        <button
          type="button"
          class="ms-clear"
          onclick={clearAll}
          aria-label="Clear all">×</button
        >
      {/if}
      <span class="ms-arrow" class:open>▾</span>
    </div>
  </div>

  {#if open}
    <div class="ms-dropdown" role="listbox">
      {#if searchable}
        <input
          class="ms-search"
          type="text"
          bind:value={query}
          placeholder="Search..."
          onkeydown={handleKeydown}
          autofocus
        />
      {/if}

      <div class="ms-options">
        {#if filteredOptions.length === 0}
          <div class="ms-empty">No options found</div>
        {:else}
          {#each filteredOptions as option, i}
            <button
              type="button"
              class="ms-option"
              class:selected={selectedSet.has(option.value)}
              class:active={i === activeIndex}
              role="option"
              aria-selected={selectedSet.has(option.value)}
              onclick={() => toggleOption(option.value)}
              onmouseenter={() => (activeIndex = i)}
            >
              <span class="ms-checkbox">
                {#if selectedSet.has(option.value)}✓{/if}
              </span>
              {option.label}
            </button>
          {/each}
        {/if}
      </div>
    </div>
  {/if}
</div>

<style>
  .multiselect {
    position: relative;
    font-family:
      system-ui,
      -apple-system,
      sans-serif;
    font-size: 14px;
    width: 100%;
    max-width: 400px;
  }

  .ms-label {
    display: block;
    margin-bottom: 6px;
    font-weight: 500;
    color: #374151;
  }

  .ms-control {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    min-height: 40px;
    padding: 6px 10px;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    background: white;
    cursor: pointer;
    transition:
      border-color 0.15s ease,
      box-shadow 0.15s ease;
  }

  .ms-control:hover:not(.disabled) {
    border-color: #9ca3af;
  }

  .ms-control.open {
    border-color: #6366f1;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
  }

  .ms-control.disabled {
    background: #f3f4f6;
    cursor: not-allowed;
    opacity: 0.6;
  }

  .ms-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    flex: 1;
    min-width: 0;
  }

  .ms-placeholder {
    color: #9ca3af;
  }

  .ms-tag {
    display: flex;
    align-items: center;
    gap: 4px;
    background: #eef2ff;
    color: #4338ca;
    padding: 2px 6px 2px 8px;
    border-radius: 6px;
    font-size: 13px;
    white-space: nowrap;
  }

  .ms-tag-count {
    background: #f3f4f6;
    color: #374151;
  }

  .ms-tag-remove {
    border: none;
    background: none;
    color: #4338ca;
    cursor: pointer;
    font-size: 14px;
    line-height: 1;
    padding: 0 2px;
    border-radius: 3px;
  }

  .ms-tag-remove:hover {
    background: rgba(67, 56, 202, 0.15);
  }

  .ms-actions {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-shrink: 0;
  }

  .ms-clear {
    border: none;
    background: none;
    color: #9ca3af;
    cursor: pointer;
    font-size: 16px;
    line-height: 1;
    padding: 0 2px;
  }

  .ms-clear:hover {
    color: #4b5563;
  }

  .ms-arrow {
    color: #9ca3af;
    font-size: 12px;
    transition: transform 0.15s ease;
  }

  .ms-arrow.open {
    transform: rotate(180deg);
  }

  .ms-dropdown {
    position: absolute;
    top: calc(100% + 4px);
    left: 0;
    right: 0;
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
    z-index: 50;
    overflow: hidden;
  }

  .ms-search {
    width: 100%;
    box-sizing: border-box;
    padding: 8px 10px;
    border: none;
    border-bottom: 1px solid #e5e7eb;
    outline: none;
    font-size: 14px;
  }

  .ms-options {
    max-height: 220px;
    overflow-y: auto;
    padding: 4px;
  }

  .ms-option {
    display: flex;
    align-items: center;
    gap: 8px;
    width: 100%;
    box-sizing: border-box;
    padding: 8px 10px;
    border: none;
    background: none;
    text-align: left;
    cursor: pointer;
    border-radius: 6px;
    font-size: 14px;
    color: #1f2937;
  }

  .ms-option.active {
    background: #f3f4f6;
  }

  .ms-option.selected {
    color: #4338ca;
    font-weight: 500;
  }

  .ms-checkbox {
    width: 16px;
    height: 16px;
    border: 1px solid #d1d5db;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    flex-shrink: 0;
    color: white;
    background: transparent;
  }

  .ms-option.selected .ms-checkbox {
    background: #6366f1;
    border-color: #6366f1;
  }

  .ms-empty {
    padding: 16px;
    text-align: center;
    color: #9ca3af;
    font-size: 13px;
  }
</style>
