import type { SelectOption } from "$lib/utils/types";

export function createDebouncedSearch<T extends SelectOption>(
  fetchOptions: (query: string) => T[] | Promise<T[]>,
  excludeValues: () => T["value"][] = () => [],
) {
  let query = $state<string>("");
  let options = $state<T[]>([]);
  let open = $state<boolean>(false);
  let timeout: ReturnType<typeof setTimeout>;

  $effect(() => {
    clearTimeout(timeout);
    if (!query || query.length < 2) {
      options = [];
      open = false;
      return;
    }
    const currentQuery = query;
    timeout = setTimeout(async () => {
      const excluded = new Set(excludeValues());
      const results = await fetchOptions(currentQuery);
      options = excluded.size
        ? results.filter((o) => !excluded.has(o.value))
        : results;
      open = true;
    }, 200);

    return () => clearTimeout(timeout);
  });

  return {
    get query() {
      return query;
    },
    set query(v: string) {
      query = v;
    },
    get options() {
      return options;
    },
    get open() {
      return open;
    },
    set open(v: boolean) {
      open = v;
    },
  };
}
