<script lang="ts" generics="T = string">
  interface Tab {
    name: string;
    value: T;
  }

  interface Props {
    tabs: readonly Tab[];
    selected: T;
    onselect?: (value: T) => void;
  }

  let { tabs, selected = $bindable(), onselect }: Props = $props();

  function handleSelect(value: T) {
    selected = value;
    onselect?.(value);
  }
</script>

<nav class="tabs">
  {#each tabs as tab}
    <button
      class={{ selected: selected === tab.value }}
      onclick={() => onselect(tab.value)}
    >
      {tab.name}
    </button>
  {/each}
</nav>

<style>
  .tabs {
    display: flex;
    gap: var(--size-lg);
  }

  button {
    all: unset;
    font-size: var(--text-sm);

    &.selected {
      font-weight: var(--font-bold);
      border-bottom: 1px solid oklch(var(--color-secondary));
    }

    &:not(.selected):hover {
      color: oklch(var(--color-secondary));
      cursor: pointer;
    }
  }
</style>
