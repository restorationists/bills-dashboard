<script>
  import { onMount, tick } from "svelte";

  export let items = [];
  export let row_height = 92;
  export let overscan = 8;

  export let render_key = (item, idx) => idx;

  let container;
  let scroll_top = 0;
  let height = 600;

  const measure = () => {
    if (!container) return;
    height = container.clientHeight || 600;
  };

  const on_scroll = () => {
    scroll_top = container ? container.scrollTop : 0;
  };

  const on_resize = () => {
    measure();
  };

  $: total = items.length;
  $: start = Math.max(0, Math.floor(scroll_top / row_height) - overscan);
  $: visible = Math.ceil(height / row_height) + overscan * 2;
  $: end = Math.min(total, start + visible);
  $: slice = items.slice(start, end);

  $: pad_top = start * row_height;
  $: pad_bottom = Math.max(0, (total - end) * row_height);

  // When items change (filter), keep scroll position sane
  $: if (container) {
    // if we've scrolled past new end, clamp
    const max_scroll = Math.max(0, total * row_height - height);
    if (scroll_top > max_scroll) {
      scroll_top = max_scroll;
      container.scrollTop = max_scroll;
    }
  }

  onMount(async () => {
    await tick();
    measure();
  });
</script>

<svelte:window on:resize={on_resize} />

<div bind:this={container} class="h-full overflow-auto" on:scroll={on_scroll}>
  <div style="padding-top:{pad_top}px; padding-bottom:{pad_bottom}px;">
    {#each slice as item, i (render_key(item, start + i))}
      <div style="height:{row_height}px;">
        <slot name="row" item={item} index={start + i}></slot>
      </div>
    {/each}
  </div>
</div>
