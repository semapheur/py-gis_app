<script lang="ts">
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

  $effect(() => {
    if (query.length < 2) {
      options = [];
      return;
    }

    options = fetchOptions(query);
    open = true;
  });

  function select(option: SelectOption) {
    value = option;
    query = option.label;
    open = false;
  }

  function onblur() {
    if (!value || query !== value.label) {
      query = "";
      value = null;
    }
    open = false;
  }
</script>

<div class="autocomplete">
  <Input value={query} {placeholder} onfocus={() => (open = true)} {onblur} />

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
    position: absolute;
    width: 100%;
    z-index: 10;
  }

  li {
    padding: var(--size-md);
    cursor: pointer;
  }
</style>
