<script>
  import { onMount, tick } from "svelte";

  let { items = [], row_height = 92, overscan = 8, render_key = (item, idx) => idx, row } = $props();

  let container = $state(null);
  let scroll_top = $state(0);
  let height = $state(600);

  const measure = () => {
    if (!container) return;
    height = container.clientHeight || 600;
  };

  const on_scroll = () => {
    scroll_top = container ? container.scrollTop : 0;
  };

  let total = $derived(items.length);
  let start = $derived(Math.max(0, Math.floor(scroll_top / row_height) - overscan));
  let visible = $derived(Math.ceil(height / row_height) + overscan * 2);
  let end = $derived(Math.min(total, start + visible));
  let slice = $derived(items.slice(start, end));

  let pad_top = $derived(start * row_height);
  let pad_bottom = $derived(Math.max(0, (total - end) * row_height));

  $effect(() => {
    if (!container) return;
    const max_scroll = Math.max(0, total * row_height - height);
    if (scroll_top > max_scroll) {
      scroll_top = max_scroll;
      container.scrollTop = max_scroll;
    }
  });

  onMount(async () => {
    await tick();
    measure();
  });
</script>

<svelte:window onresize={measure} />

<div bind:this={container} class="h-full overflow-auto" onscroll={on_scroll}>
  <div style="padding-top:{pad_top}px; padding-bottom:{pad_bottom}px;">
    {#each slice as item, i (render_key(item, start + i))}
      <div style="height:{row_height}px;">
        {@render row(item, start + i)}
      </div>
    {/each}
  </div>
</div>
