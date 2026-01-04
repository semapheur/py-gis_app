<script lang="ts">
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
  let vimMode = $state(false);
  //let currentVimStatus = $state<VimModes>("NORMAL");

  let view: EditorView | null = null;
  const keymapConfig = new Compartment();
  const lineNumberConfig = new Compartment();

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
      if (viewUpdate.selectionSet && vimMode) {
        viewUpdate.view.dispatch({
          effects: lineNumberConfig.reconfigure(relativeLineNumbers()),
        });
      }
    });
  }

  function attachEditor(element: HTMLElement) {
    const state = EditorState.create({
      doc: value,
      extensions: [
        EditorState.allowMultipleSelections.of(true),
        history(),
        drawSelection(),
        highlightSelectionMatches(),
        keymapConfig.of(getKeymapExtensions(vimMode)),
        lineNumberConfig.of(
          vimMode ? relativeLineNumbers() : absoluteLineNumbers(),
        ),
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

    view.dispatch({
      effects: [
        keymapConfig.reconfigure(getKeymapExtensions(vimMode)),
        lineNumberConfig.reconfigure(
          vimMode ? relativeLineNumbers() : absoluteLineNumbers(),
        ),
      ],
    });
  });
</script>

<div class="editor-container">
  <div class="editor" {@attach attachEditor}></div>

  <div class="status-bar" class:vim-active={vimMode}>
    <div class="status-left">
      <label>
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
  }

  .status-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: rgb(var(--color-accent));
  }
</style>
