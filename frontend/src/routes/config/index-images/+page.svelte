<script lang="ts">
  import Button from "$lib/components/Button.svelte";
  import type { PageData } from "./$types";
  import { toast } from "$lib/stores/toast.svelte";
  import { formatDatetime } from "$lib/utils/date";
  import LinkButton from "$lib/components/LinkButton.svelte";

  interface CatalogData {
    id: string;
    name: string;
    path: string;
    indexed_images: number;
    last_indexed: number | null;
  }

  interface IndexProgress {
    current: number;
    total: number;
    filename: string;
    percent: number;
  }

  let { data }: { data: PageData } = $props();

  let indexingCatalogs = $state<Record<string, string>>({});
  let progressMap = $state<Record<string, IndexProgress | null>>({});
  let indexingMap = $state<Record<string, boolean>>({});

  async function indexCatalog(id: string, name: string) {
    indexingCatalogs[id] = name;
    indexingMap[id] = true;
    progressMap[id] = null;

    const response = await fetch("/api/index-catalog", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id }),
    });

    if (!response.ok) {
      toast.error(`Failed to index images for catalog '${id}'`);
      indexingMap[id] = false;
      return;
    }

    const reader = response.body
      ?.pipeThrough(new TextDecoderStream())
      .getReader();
    let buffer = "";

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += value;
        const parts = buffer.split("\n\n");
        buffer = parts.pop() ?? "";

        for (const part of parts) {
          const eventLine = part.match(/^event:\s*(.+)$/m)?.[1];
          const dataLine = part.match(/^data:\s*(.+)$/m)?.[1];

          if (!dataLine) continue;

          const payload = JSON.parse(dataLine);

          if (eventLine === "progress") {
            progressMap[id] = payload as IndexProgress;
          } else if (eventLine === "done") {
            progressMap[id] = null;
            indexingMap[id] = false;
            toast.success(`Indexing complete for catalog '${id}'`);
          } else if (eventLine === "error") {
            progressMap[id] = null;
            indexingMap[id] = false;
            toast.error(`Error indexing catalog '${id}': ${payload.message}`);
          }
        }
      }
    } finally {
      reader?.releaseLock();
      indexingMap[id] = false;
      delete indexingCatalogs.id;
    }
  }

  function formatOptionalDatetime(value: number | null) {
    return value != null ? formatDatetime(value) : "";
  }
</script>

<div class="container">
  <div class="toolbar">
    <Button>Index all</Button>
    <LinkButton href="edit-catalogs">Edit catalog</LinkButton>
  </div>
  <table>
    <thead>
      <tr>
        <th>Index</th>
        <th>Catalog</th>
        <th>Path</th>
        <th>Indexed images</th>
        <th>Last indexed</th>
      </tr>
    </thead>
    <tbody
      >{#each data.catalogs as catalog}
        {@const c = catalog as CatalogData}
        {@const indexing = indexingMap[c.id]}
        <tr>
          <td
            ><Button
              onclick={() => indexCatalog(c.id, c.name)}
              disabled={indexing}>{indexing ? "Indexing..." : "Index"}</Button
            ></td
          >
          <td>{c.name}</td>
          <td>{c.path}</td>
          <td> {c.indexed_images}</td>
          <td>{formatOptionalDatetime(c.last_indexed)}</td>
        </tr>
      {/each}
    </tbody>
  </table>
  <div class="footer">
    {#each Object.entries(indexingCatalogs) as [id, name]}
      {@const progress = progressMap[id]}

      {#if progress}
        <span>{`Indexing ${name}`}</span>
        <progress value={progress.percent} max="100"></progress>
        <div>{progress.current} / {progress.total}</div>
        <span class="filename">{progress.filename}</span>
      {/if}
    {/each}
  </div>
</div>

<style>
  .toolbar {
    display: flex;
    gap: var(--size-md);
  }

  table {
    height: fit-content;
    width: 100%;
    text-align: center;
  }

  progress {
    width: 100%;
  }

  .filename {
    font-size: var(--font-sm);
    text-overflow: ellipsis;
    white-space: nowrap;
  }
</style>
