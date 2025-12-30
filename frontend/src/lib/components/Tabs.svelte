<script lang="ts">
  interface Tab<T = string> {
    name: string;
    value: T;
  }

  interface Props<T = string> {
    tabs: readonly Tab<T>[];
    selected: T;
    onselect: (value: T) => void;
  }

  let { tabs, selected, onselect }: Props = $props();
</script>

<nav class="tabs">
  {#each tabs as tab}
    <button
      class:selected={selected === tab.value}
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
    }

    &:not(.selected):hover {
      color: rgb(var(--color-secondary));
      cursor: pointer;
    }
  }
</style>
