<script lang="ts">
  import { type AngleRange } from "$lib/utils/types";
  import { tick } from "svelte";

  interface Props {
    selectedRange: AngleRange | null;
    placeholder: string;
    min: number;
    max: number;
    step: number;
    separator?: string;
    formatValue?: (value: number) => string;
  }

  let {
    selectedRange = $bindable(),
    placeholder,
    min,
    max,
    step,
    separator = "-",
    formatValue,
  }: Props = $props();

  let activeSlot = $state<0 | 1 | null>(null);
  let containerEl = $state<HTMLDivElement | null>(null);
  let startInputEl = $state<HTMLInputElement | null>(null);
  let endInputEl = $state<HTMLInputElement | null>(null);

  let minCh = $derived(
    Math.max(placeholder.length, 2 * max.toString().length + separator.length),
  );

  function clamp(value: number) {
    return Math.min(max, Math.max(min, value));
  }

  function getDisplayValue(value: number, isFocused: boolean) {
    if (isFocused) return value.toString();
    return formatValue ? formatValue(value) : value.toString();
  }

  function handleKeyDown(e: KeyboardEvent) {
    if (activeSlot === null || selectedRange === null) return;

    const target = e.target as HTMLInputElement;

    switch (e.key) {
      case "ArrowLeft":
        if (target.selectionStart === 0) {
          e.preventDefault();
          activeSlot = 0;
          startInputEl?.focus();
        }
        break;
      case "ArrowRight":
        if (target.selectionStart === target.value.length) {
          e.preventDefault();
          activeSlot = 1;
          endInputEl?.focus();
        }
        break;
      case "ArrowUp":
        e.preventDefault();
        if (activeSlot === 0 && startInputEl) {
          const next = clamp(selectedRange.start + step);
          if (next <= selectedRange.end)
            selectedRange = { ...selectedRange, start: next };
        } else if (activeSlot === 1 && endInputEl) {
          const next = clamp(selectedRange.end + step);
          selectedRange = {
            ...selectedRange,
            end: next,
          };
        }
        break;
      case "ArrowDown":
        e.preventDefault();
        if (activeSlot === 0 && startInputEl) {
          const next = clamp(selectedRange.start - step);
          selectedRange = {
            ...selectedRange,
            start: next,
          };
        } else if (activeSlot === 1 && endInputEl) {
          const next = clamp(selectedRange.end - step);
          if (next >= selectedRange.start)
            selectedRange = { ...selectedRange, end: next };
        }
        break;
      case "Escape":
        selectedRange = null;
        activeSlot = null;
        break;
      case "Enter":
        target.blur();
        break;
    }
  }

  function handleBlur(e: FocusEvent) {
    const related = e.relatedTarget as Node | null;
    if (!containerEl?.contains(related)) {
      activeSlot = null;
    }
  }

  async function initializeRange() {
    if (selectedRange === null) {
      selectedRange = { start: min, end: max };
      activeSlot = 0;
      await tick();
      startInputEl?.focus();
    }
  }

  function handleStartChange(e: Event) {
    if (selectedRange === null) return;

    const target = e.target as HTMLInputElement;
    const sanitized = target.value.replace(/[^0-9.-]/g, "");
    let value = parseFloat(sanitized);

    if (isNaN(value)) {
      target.value = getDisplayValue(selectedRange.start, false);
      return;
    }

    value = clamp(value);
    if (value > selectedRange.end) value = selectedRange.end;

    selectedRange = { ...selectedRange, start: value };
  }

  function handleEndChange(e: Event) {
    if (selectedRange === null) return;

    const target = e.target as HTMLInputElement;
    const sanitized = target.value.replace(/[^0-9.-]/g, "");
    let value = parseFloat(sanitized);

    if (isNaN(value)) {
      target.value = getDisplayValue(selectedRange.end, false);
      return;
    }

    value = clamp(value);
    if (value < selectedRange.start) value = selectedRange.start;

    selectedRange = { ...selectedRange, end: value };
  }
</script>

<div
  class={[
    "range-input",
    { "has-value": selectedRange !== null, focused: activeSlot !== null },
  ]}
  onclick={initializeRange}
  onfocus={initializeRange}
  tabindex={selectedRange === null ? 0 : -1}
>
  <div
    bind:this={containerEl}
    class={["number-slots", { active: activeSlot !== null }]}
    role="group"
    onkeydown={handleKeyDown}
    onfocusout={handleBlur}
    style="width: {minCh}ch;"
  >
    {#if selectedRange !== null}
      <input
        bind:this={startInputEl}
        type="text"
        inputmode="decimal"
        class={["slot", "start", { active: activeSlot === 0 }]}
        value={getDisplayValue(selectedRange.start, activeSlot === 0)}
        onchange={handleStartChange}
        onfocus={() => (activeSlot = 0)}
        onclick={(e) => e.stopPropagation()}
      />
      <span class="separator">{separator}</span>
      <input
        bind:this={endInputEl}
        type="text"
        inputmode="decimal"
        class={["slot", "end", { active: activeSlot === 1 }]}
        value={getDisplayValue(selectedRange.end, activeSlot === 1)}
        onchange={handleEndChange}
        onfocus={() => (activeSlot = 1)}
        onclick={(e) => e.stopPropagation()}
      />
    {/if}
  </div>
  <label class="placeholder">{placeholder}</label>
</div>

<style>
  .range-input {
    display: flex;
    align-items: center;
    position: relative;
    height: var(--input-height);
    padding: 0 var(--size-sm);
    background-color: oklch(var(--color-primary-accent));
    border: 1px solid oklch(var(--color-secondary));
    border-radius: var(--size-sm);
  }

  .range-input:focus-within {
    border: 1px solid oklch(var(--color-text));
  }

  .number-slots {
    display: flex;
    gap: var(--size-lg);
    justify-content: center;
    width: 100%;
  }

  .slot {
    all: unset;
    display: inline-block;
    flex: 1;
    min-width: 0;
  }

  .slot.start {
    text-align: right;
  }

  .slot.end {
    text-align: left;
  }

  .placeholder {
    position: absolute;
    left: var(--size-sm);
    top: 50%;
    font-size: 1rem;
    color: oklch(var(--color-text));
    pointer-events: none;
    transform: translateY(-50%);
    transition: all 0.15s ease;
  }

  .range-input.focused .placeholder,
  .range-input.has-value .placeholder {
    top: 0;
    font-size: var(--text-2xs);
    text-shadow: var(--text-shadow);
    transform: translateY(-50%);
  }
</style>
