<script lang="ts">
  import Input from "$lib/components/Input.svelte";
  import Select from "$lib/components/Select.svelte";
  import TextArea from "$lib/components/TextArea.svelte";

  import {
    activityTypes,
    type ActivityData,
  } from "$lib/contexts/annotate.svelte";

  type ActivityPatch = Partial<ActivityData>;

  interface Props {
    value: ActivityData | ActivityPatch;
    onchange: (value: ActivityData | ActivityPatch) => void;
    onvalid?: (valid: boolean) => void;
    bulk?: boolean;
  }

  let { value, onchange, onvalid, bulk = false }: Props = $props();

  function update<K extends keyof ActivityData>(key: K, v: ActivityData[K]) {
    const next = { ...value, [key]: v };

    if (bulk && v === undefined) {
      delete (next as ActivityPatch)[key];
    }

    onchange(next);
    onvalid?.(isValid(next));
  }

  function isValid(v: ActivityData | ActivityPatch) {
    if (bulk) {
      return true;
    }

    const full = v as ActivityData;
    return Boolean(full.type);
  }
</script>

<form class="form">
  <Input
    label="Summary"
    value={value.summary}
    oninput={(v) => update("summary", v || (bulk ? undefined : v))}
  />
  <Select
    options={activityTypes}
    label="Confidence"
    value={value.type}
    onchange={(v) => update("type", v || (bulk ? undefined : v))}
  />
  <TextArea
    label="Observed activity"
    value={value.observed}
    onchange={(v) => update("observed", v || bulk ? undefined : v)}
  />
  <TextArea
    label="Comment"
    value={value.comment}
    onchange={(v) => update("observed", v || bulk ? undefined : v)}
  />
</form>
