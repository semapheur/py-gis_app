<script lang="ts">
  import Input from "$lib/components/Input.svelte";

  let bluf: string | null;
</script>

<form class="form">
  <Input label="BLUF" name="bluf" bind:value={bluf} />
</form>
