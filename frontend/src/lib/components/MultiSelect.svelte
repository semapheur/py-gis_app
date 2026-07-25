<script lang="ts" generics="T = string">
  import Input from "$lib/components/Input.svelte";
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
  let dropdownEl = $state<HTMLDivElement | null>(null);
  let activeIndex = $state<number>(-1);
  let dropUp = $state<boolean>(false);

  const DROPDOWN_MAX_HEIGHT = 300;

  function updatePlacement() {
    if (!containerEl) return;

    const rect = containerEl.getBoundingClientRect();
    const spaceBelow = window.innerHeight - rect.bottom;
    const spaceAbove = rect.top;

    if (spaceBelow < DROPDOWN_MAX_HEIGHT && spaceAbove > spaceBelow) {
      dropUp = true;
    } else {
      dropUp = false;
    }
  }

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

  $effect(() => {
    if (!open || !containerEl || !dropdownEl) return;

    const recompute = () => {
      const rect = containerEl.getBoundingClientRect();
      const dropdownHeight = dropdownEl.offsetHeight;
      const spaceBelow = window.innerHeight - rect.bottom;
      const spaceAbove = rect.top;

      dropUp = spaceBelow < dropdownHeight && spaceAbove > spaceBelow;
    };

    recompute();
    window.addEventListener("scroll", recompute, true);
    window.addEventListener("resize", recompute);
    return () => {
      window.removeEventListener("scroll", recompute, true);
      window.removeEventListener("resize", recompute);
    };
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
    <div
      bind:this={dropdownEl}
      class={["ms-dropdown", { "drop-up": dropUp }]}
      role="listbox"
    >
      {#if searchable}
        <Input
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
    width: 100%;
    max-width: 400px;
  }

  .ms-label {
    display: block;
    margin-bottom: 6px;
    font-weight: 500;
    color: oklch(var(--color-text));
  }

  .ms-control {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--size-sm);
    min-height: 1rem;
    padding: var(--size-sm) var(--size-md);
    border: 1px solid oklch(var(--color-secondary));
    border-radius: var(--size-md);
    background: oklch(var(--color-primary-accent));
    cursor: pointer;
    transition:
      border-color 0.15s ease,
      box-shadow 0.15s ease;
  }

  .ms-control:hover:not(.disabled) {
    border-color: oklch(var(--color-secondary-accent));
  }

  .ms-control.open {
    border-color: oklch(var(--color-secondary));
    box-shadow: 0 0 0 3px oklch(var(--color-secondary-accent));
  }

  .ms-control.disabled {
    background: oklch(var(--color-primary-accent) / 0.5);
    cursor: not-allowed;
  }

  .ms-tags {
    display: flex;
    flex-wrap: wrap;
    gap: var(--size-sm);
    flex: 1;
    min-width: 0;
  }

  .ms-placeholder {
    color: oklch(var(--color-text) / 0.5);
  }

  .ms-tag {
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

  .ms-tag-count {
    background: oklch(var(--color-primary));
    color: oklch(var(--color-text));
  }

  .ms-tag-remove {
    border: none;
    background: none;
    color: oklch(var(--color-secondary));
    cursor: pointer;
    font-size: var(--text-sm);
    line-height: 1;
    padding: 0 var(--size-sm);
    border-radius: 50%;
  }

  .ms-tag-remove:hover {
    background: oklch(var(--color-secondary-accent));
  }

  .ms-actions {
    display: flex;
    align-items: center;
    gap: var(--size-sm);
    flex-shrink: 0;
  }

  .ms-clear {
    border: none;
    background: none;
    color: oklch(var(--color-text));
    cursor: pointer;
    font-size: var(--text-sm);
    line-height: 1;
    padding: 0 var(--size-xs);
  }

  .ms-clear:hover {
    color: oklch(var(--color-negative));
  }

  .ms-arrow {
    color: oklch(var(--color-text));
    font-size: var(--text-md);
    transition: transform 0.15s ease;
  }

  .ms-arrow.open {
    transform: rotate(180deg);
  }

  .ms-dropdown {
    position: absolute;
    top: calc(100% + 0.5rem);
    left: 0;
    right: 0;
    padding: var(--size-sm);
    background: oklch(var(--color-primary-accent));
    border: 1px solid oklch(var(--color-secondary));
    border-radius: var(--size-md);
    z-index: 1;
    overflow: hidden;
  }

  .ms-dropdown.drop-up {
    top: auto;
    bottom: calc(100% + 0.5rem);
  }

  .ms-options {
    max-height: 220px;
    overflow-y: auto;
    padding: var(--size-sm);
  }

  .ms-option {
    display: flex;
    align-items: center;
    gap: var(--size-md);
    width: 100%;
    box-sizing: border-box;
    padding: var(--size-sm);
    border: none;
    background: none;
    text-align: left;
    cursor: pointer;
    border-radius: 6px;
    font-size: 14px;
    color: oklch(var(--color-text));
  }

  .ms-option.active {
    background: oklch(var(--color-primary));
  }

  .ms-option.selected {
    color: oklch(var(--color-secondary));
    font-weight: var(--font-bold);
  }

  .ms-checkbox {
    width: var(--text-sm);
    height: var(--text-sm);
    border: 1px solid oklch(var(--color-secondary));
    border-radius: var(--size-sm);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: var(--text-sm);
    flex-shrink: 0;
    color: oklch(var(--color-text));
    background: transparent;
  }

  .ms-option.selected .ms-checkbox {
    background: oklch(var(--color-secondary));
    border-color: oklch(var(--color-secondary));
  }

  .ms-empty {
    padding: var(--size-sm);
    text-align: center;
    color: oklch(var(--color-text));
    font-size: var(--text-sm);
  }
</style>
