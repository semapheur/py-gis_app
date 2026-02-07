<script lang="ts">
  import { untrack } from "svelte";
  import { EditorState, Compartment } from "@codemirror/state";
  import {
    EditorView,
    ViewUpdate,
    drawSelection,
    keymap,
    lineNumbers,
  } from "@codemirror/view";
  import { defaultKeymap, history, historyKeymap } from "@codemirror/commands";
  import { searchKeymap, highlightSelectionMatches } from "@codemirror/search";
  import { vim } from "@replit/codemirror-vim";

  //type VimModes = "NORMAL" | "INSERT" | "VISUAL";

  interface Props {
    value: string;
  }

  let { value = $bindable() }: Props = $props();
  let internalValue = $state<string>(value);
  let vimMode = $state<boolean>(false);
  let wrapText = $state<boolean>(true);
  //let currentVimStatus = $state<VimModes>("NORMAL");

  let view: EditorView | null = null;

  const keymapConfig = new Compartment();
  const lineNumberConfig = new Compartment();
  const wrapConfig = new Compartment();

  function getKeymapExtensions(isVim: boolean) {
    if (isVim) {
      return vim();
    }

    return keymap.of([...defaultKeymap, ...historyKeymap, ...searchKeymap]);
  }

  function relativeLineNumberFormatter(lineNo: number, state: EditorState) {
    const cursorLine = state.doc.lineAt(state.selection.main.head).number;

    if (lineNo === cursorLine) return String(lineNo);
    return String(Math.abs(lineNo - cursorLine));
  }

  function relativeLineNumbers() {
    return lineNumbers({
      formatNumber: relativeLineNumberFormatter,
    });
  }

  function absoluteLineNumbers() {
    return lineNumbers();
  }

  function createUpdateListener() {
    return EditorView.updateListener.of((viewUpdate: ViewUpdate) => {
      if (viewUpdate.docChanged) {
        const newValue = viewUpdate.state.doc.toString();
        internalValue = newValue;
        value = newValue;
      }

      if (viewUpdate.selectionSet && vimMode) {
        viewUpdate.view.dispatch({
          effects: lineNumberConfig.reconfigure(relativeLineNumbers()),
        });
      }
    });
  }

  function attachEditor(element: HTMLElement) {
    const initialValue = untrack(() => value);

    const state = EditorState.create({
      doc: initialValue,
      extensions: [
        EditorState.allowMultipleSelections.of(true),
        history(),
        drawSelection(),
        highlightSelectionMatches(),
        keymapConfig.of(getKeymapExtensions(vimMode)),
        lineNumberConfig.of(
          vimMode ? relativeLineNumbers() : absoluteLineNumbers(),
        ),
        wrapConfig.of(wrapText ? EditorView.lineWrapping : []),
        createUpdateListener(),
      ],
    });

    view = new EditorView({
      parent: element,
      state,
    });

    return () => {
      view?.destroy();
    };
  }

  $effect(() => {
    if (!view) return;
    if (value === internalValue) return;

    const doc = view.state.doc.toString();
    if (doc !== value) {
      view.dispatch({
        changes: { from: 0, to: doc.length, insert: value },
      });
    }
    internalValue = value;
  });

  $effect(() => {
    if (!view) return;

    view.dispatch({
      effects: [
        keymapConfig.reconfigure(getKeymapExtensions(vimMode)),
        lineNumberConfig.reconfigure(
          vimMode ? relativeLineNumbers() : absoluteLineNumbers(),
        ),
        wrapConfig.reconfigure(wrapText ? EditorView.lineWrappoing : []),
      ],
    });
  });
</script>

<div class="editor-container">
  <div class="editor" {@attach attachEditor}></div>

  <div class="status-bar" class:vim-active={vimMode}>
    <div class="status-left">
      <label class="label">
        <input bind:checked={wrapText} type="checkbox" />
        Wrap text
      </label>
      <label class="label">
        <input bind:checked={vimMode} type="checkbox" />
        Vim mode
      </label>
    </div>
  </div>
</div>

<style>
  .editor-container {
    display: grid;
    grid-template-rows: 1fr auto;
    width: 100%;
    height: 100%;
    min-height: 0;
  }

  .editor {
    min-height: 0;
    height: 100%;
    overflow: hidden;

    & :global(.cm-editor) {
      height: 100%;
    }

    & :global(.cm-scroller) {
      height: 100%;
      max-height: 100%;
      overflow: auto;
    }
  }

  .status-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: oklch(var(--color-accent));
    flex-shrink: 0;
  }

  .label {
    font-size: var(--text-sm);
  }
</style>
