<script lang="ts">
  import { type Snippet } from "svelte";

  interface Props {
    id: string;
    children: Snippet;
    header: Snippet;
  }

  let { id, children, header }: Props = $props();
</script>

<li>
  <input {id} class="collapsible-input" type="checkbox" />
  <label for={id} class="collapsible-label">
    <span class="arrow"></span>
    {@render header()}
  </label>
  <ul class="collapsible-list">
    {@render children()}
  </ul>
</li>

<style>
  :root {
    --arrow-size: 0.4rem;
    --arrow-gap: 0.5rem;
  }

  ul {
    list-style: none;
  }

  .collapsible-label {
    position: relative;
    display: inline-flex;
    gap: var(--arrow-gap);
    align-items: center;
    cursor: pointer;
    user-select: none;
  }

  .arrow {
    width: calc(var(--arrow-size) * 2);
    height: calc(var(--arrow-size) * 2);
    display: inline-flex;
    align-items: center;
    justify-content: center;

    &::before {
      content: "";
      width: var(--arrow-size);
      height: var(--arrow-size);
      border-right: 1px solid oklch(var(--color-text));
      border-bottom: 1px solid oklch(var(--color-text));
      transform: rotate(-45deg);
      transition: transform var(--duration-normal);
    }
  }

  .collapsible-list {
    display: none;
    margin-left: var(--arrow-size);
    padding-left: var(--arrow-gap);
    border-left: 1px solid oklch(var(--color-secondary));
  }

  .collapsible-input {
    position: absolute;
    opacity: 0;
    pointer-events: none;

    &:checked {
      & ~ .collapsible-label .arrow::before {
        transform: rotate(45deg);
      }

      & ~ .collapsible-list {
        display: block;
      }
    }
  }
</style>
