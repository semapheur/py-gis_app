<script lang="ts">
  interface Tab<T = string> {
    name: string;
    value: T;
  }

  interface Props {
    tabs: readonly Tab[];
    selected: string;
  }

  let { tabs, selected = $bindable() }: Props = $props();
</script>

<nav class="tabs">
  {#each tabs as tab}
    <button
      class:selected={selected === tab.value}
      onclick={() => (selected = tab.value)}
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
    }
  }
</style>
