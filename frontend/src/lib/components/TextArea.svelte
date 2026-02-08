<script lang="ts">
  import TextEditor from "$lib/components/TextEditor.svelte";
  import Window from "$lib/components/Window.svelte";

  type Resize =
    | "none"
    | "both"
    | "horizontal"
    | "vertical"
    | "block"
    | "inline";

  interface Props {
    value?: string | null;
    placeholder?: string;
    required?: boolean;
    rows?: number;
    resize?: Resize;
    oninput?: (value: string) => void;
  }

  let {
    value = null,
    placeholder = "",
    required = false,
    rows = 4,
    resize = "none",
    oninput,
  }: Props = $props();

  let editorTitle = $derived(`Edit: ${placeholder}`);
  let openEditor = $state<boolean>(false);

  let internal = $state(value ?? "");

  $effect(() => {
    internal = value ?? "";
  });

  const uid = $props.id();
</script>

<div class="text-area">
  <textarea
    id={uid}
    {placeholder}
    bind:value={internal}
    {required}
    {rows}
    style:resize
    oninput={(e) => oninput?.(e.currentTarget.value)}
  ></textarea>

  <button
    class="editor-button"
    title="Open in editor"
    onclick={() => (openEditor = true)}
  >
    ✎
  </button>

  {#if placeholder}
    <label for={uid}>{placeholder}</label>
  {/if}
</div>

{#if openEditor}
  <Window bind:open={openEditor} title={editorTitle}>
    <TextEditor bind:value={internal} />
  </Window>
{/if}

<style>
  :root {
    --top-float: 0rem;
  }

  .text-area {
    position: relative;
    display: flex;
    flex-direction: column;
  }

  .editor-button {
    position: absolute;
    right: 0;
    bottom: 0;
    font-size: var(--text-2xs);
  }

  label {
    position: absolute;
    left: var(--size-md);
    font-size: var(--text-2xs);
    top: var(--top-float);
    transform: translateY(-50%);
    transition: all 0.15s ease;
    text-shadow: var(--text-shadow);
    pointer-events: none;
  }

  textarea {
    width: 100%;
    padding: var(--size-sm);

    &::placeholder {
      color: transparent;
    }

    &:placeholder-shown + label {
      font-size: inherit;
      background-color: transparent;
      transform: translateY(0);
    }

    &:focus + label {
      font-size: var(--text-2xs);
      top: var(--top-float);
      transform: translateY(-50%);
      text-shadow: var(--text-shadow);
    }
  }
</style>
