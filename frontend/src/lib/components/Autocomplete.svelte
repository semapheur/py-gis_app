<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import Input from "$lib/components/Input.svelte";
  import { type SelectOption } from "$lib/utils/types";

  interface Props {
    value?: SelectOption;
    placeholder?: string;
    fetchOptions: (query: string) => SelectOption[];
  }

  let { value = $bindable(), placeholder, fetchOptions }: Props = $props();

  let query = $state<string>("");
  let options = $state<SelectOption[]>([]);
  let open = $state<boolean>(false);

  let container: HTMLDivElement;
  let timeout: ReturnType<typeof setTimeout>;

  $effect(() => {
    clearTimeout(timeout);

    if (query.length < 2) {
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
    value = option;
    query = option.label;
    open = false;
  }

  function handlePointerDown(e: PointerEvent) {
    const path = e.composedPath();

    if (path.includes(container)) {
      return;
    }

    open = false;

    if (!value || query !== value.label) {
      query = "";
      value = null;
    }
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === "Escape") {
      open = false;
    }
  }

  onMount(() => {
    document.addEventListener("pointerdown", handlePointerDown);
    document.addEventListener("keydown", handleKeydown);
  });

  onDestroy(() => {
    document.removeEventListener("pointerdown", handlePointerDown);
    document.removeEventListener("keydown", handleKeydown);
  });
</script>

<div class="autocomplete" bind:this={container}>
  <Input
    value={query}
    {placeholder}
    oninput={(v) => (query = v)}
    onfocus={() => (open = true)}
  />

  {#if open && options.length}
    <ul class="dropdown">
      {#each options as option}
        <li onpointerdown={() => select(option)}>
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
    z-index: 10;
    background: rgb(var(--color-accent));
  }

  li {
    padding: var(--size-md);
    cursor: pointer;
  }
</style>
