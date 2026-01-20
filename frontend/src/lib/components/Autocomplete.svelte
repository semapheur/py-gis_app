<script lang="ts">
  interface Option<T = string> {
    label: string;
    value: T;
  }

  interface Props {
    value: Option;
    fetchOptions: (query: string) => Option[];
  }

  let { value = $bindable(), fetchOptions }: Props = $props();

  let query = $state<string>("");
  let options = $state<Option[]>([]);
  let open = $state<boolean>(false);

  $effect(() => {
    if (query.length < 2) {
      options = [];
      return;
    }

    options = fetchOptions(query);
    open = true;
  });

  function select(option: Option) {
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
  <input
    type="text"
    bind:value={query}
    onfocus={() => (open = true)}
    {onblur}
    autocomplete="off"
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
    position: absolute;
    width: 100%;
    z-index: 10;
  }

  li {
    padding: var(--size-md);
    cursor: pointer;
  }
</style>
