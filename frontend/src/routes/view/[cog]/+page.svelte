<script lang="ts">
  import { page } from "$app/state";
  import ImageViewer from "$lib/components/ImageViewer.svelte";

  const fileName = page.params.cog;
</script>

<ImageViewer {fileName} />
