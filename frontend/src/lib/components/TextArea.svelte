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
    label?: string;
    required?: boolean;
    rows?: number;
    resize?: Resize;
    oninput?: (value: string) => void;
  }

  let {
    value = null,
    label = "",
    required = false,
    rows = 4,
    resize = "none",
    oninput,
  }: Props = $props();

  let placeholder = $derived(label);
  let editorTitle = $derived(`Edit: ${label}`);
  let openEditor = $state<boolean>(false);
  const uid = $props.id();
</script>

<div class="container">
  <textarea
    id={uid}
    {placeholder}
    bind:value
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

  {#if label}
    <label for={uid}>{label}</label>
  {/if}
</div>

{#if openEditor}
  <Window bind:open={openEditor} title={editorTitle}>
    <TextEditor bind:value />
  </Window>
{/if}

<style>
  :root {
    --top-float: 0rem;
  }

  .container {
    position: relative;
    display: flex;
    flex-direction: column;
    margin-top: var(--text-2xs);
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
    background-color: white;
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
      background-color: white;
    }
  }
</style>
