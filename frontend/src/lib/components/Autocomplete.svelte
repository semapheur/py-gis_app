<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import Input from "$lib/components/Input.svelte";
  import { type SelectOption } from "$lib/utils/types";

  interface Props {
    value?: SelectOption | null;
    placeholder?: string;
    fetchOptions: (query: string) => SelectOption[];
    onchange?: (value: SelectOption | null) => void;
  }

  let { value = null, placeholder, fetchOptions, onchange }: Props = $props();

  let query = $state<string>("");
  let options = $state<SelectOption[]>([]);
  let open = $state<boolean>(false);

  let container: HTMLDivElement;
  let timeout: ReturnType<typeof setTimeout>;

  $effect(() => {
    query = value?.label ?? "";
  });

  $effect(() => {
    clearTimeout(timeout);

    if (!query || query.length < 2) {
      options = [];
      open = false;
      return;
    }

    timeout = setTimeout(async () => {
      options = await fetchOptions(query);
      open = true;
    }, 200);
  });

  function select(option: SelectOption) {
    onchange?.(option);
    open = false;
  }

  function clear() {
    onchange?.(null);
    open = false;
  }

  function handlePointerDown(e: PointerEvent) {
    if (container.contains(e.target as Node)) return;

    open = false;

    if (!value || query !== value.label) {
      query = "";
      value = null;
    }
  }

  function onblur() {
    setTimeout(() => {
      open = false;
      if (!value || query !== value.label) {
        query = "";
        value = null;
      }
    }, 150);
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === "Escape") {
      open = false;
    }
  }

  onMount(() => {
    document.addEventListener("keydown", handleKeydown);
  });

  onDestroy(() => {
    document.removeEventListener("keydown", handleKeydown);
  });
</script>

<div class="autocomplete" bind:this={container}>
  <Input
    value={query}
    {placeholder}
    oninput={(v) => {
      query = v;
      onchange?.(null);
    }}
    {onblur}
  />

  {#if open && options?.length && !value}
    <ul class="dropdown">
      {#each options as option}
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
  .autocomplete {
    position: relative;
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
    background: rgb(var(--color-accent));
  }

  li {
    padding: 0 var(--size-md);
    cursor: pointer;
    font-size: var(--text-xs);
  }
</style>
