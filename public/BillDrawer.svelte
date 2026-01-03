<script>
  import { onDestroy } from "svelte";

  export let open = false;
  export let bill = null;
  export let members_by_id = {};
  export let bills_by_id = {};
  export let on_close = () => {};

  const sponsor = (b) => (b?.member_id ? members_by_id[b.member_id] : null);
  const related = (b) => (b?.related || []).map((id) => bills_by_id[id]).filter(Boolean);
  const bill_link = (id, suffix = "") => `https://bills.parliament.uk/bills/${id}${suffix}`;
  const normalize = (s) => (s || "").toLowerCase().trim();

  const pill_neutral = () =>
    "bg-neutral-200 text-neutral-900 border border-neutral-300 " +
    "dark:bg-white/10 dark:text-neutral-100 dark:border-white/15";

  const party_style = (party) => {
    const p = normalize(party);

    if (p.includes("labour"))
      return (
        "bg-rose-600/15 text-rose-800 border border-rose-600/20 " +
        "dark:bg-rose-500/22 dark:text-rose-100 dark:border-rose-300/25"
      );

    if (p.includes("conservative"))
      return (
        "bg-sky-600/15 text-sky-800 border border-sky-600/20 " +
        "dark:bg-sky-500/22 dark:text-sky-100 dark:border-sky-300/25"
      );

    if (p.includes("liberal democrat"))
      return (
        "bg-amber-500/18 text-amber-900 border border-amber-500/25 " +
        "dark:bg-amber-300/22 dark:text-amber-100 dark:border-amber-200/25"
      );

    if (p === "green party" || p.includes("green"))
      return (
        "bg-emerald-600/15 text-emerald-900 border border-emerald-600/20 " +
        "dark:bg-emerald-500/22 dark:text-emerald-100 dark:border-emerald-300/25"
      );

    if (p.includes("snp") || p.includes("scottish national"))
      return (
        "bg-yellow-400/25 text-yellow-900 border border-yellow-400/30 " +
        "dark:bg-yellow-300/22 dark:text-yellow-50 dark:border-yellow-200/25"
      );

    if (p.includes("plaid"))
      return (
        "bg-emerald-700/12 text-emerald-900 border border-emerald-700/18 " +
        "dark:bg-emerald-900/40 dark:text-emerald-100 dark:border-emerald-700/40"
      );

    if (p.includes("reform"))
      return (
        "bg-cyan-600/14 text-cyan-900 border border-cyan-600/18 " +
        "dark:bg-cyan-400/22 dark:text-cyan-100 dark:border-cyan-200/25"
      );

    return pill_neutral();
  };

  const house_icon = (h) => (h === "Commons" ? "mdi:account-group-outline" : "mdi:crown-outline");

  const lock_scroll = () => {
    const body = document.body;
    const prev_overflow = body.style.overflow;
    const prev_padding = body.style.paddingRight;

    const scrollbar = window.innerWidth - document.documentElement.clientWidth;
    body.style.overflow = "hidden";
    if (scrollbar > 0) body.style.paddingRight = `${scrollbar}px`;

    return () => {
      body.style.overflow = prev_overflow;
      body.style.paddingRight = prev_padding;
    };
  };

  let unlock = null;

  $: if (open && bill && typeof window !== "undefined") {
    if (!unlock) unlock = lock_scroll();
  } else {
    if (unlock) {
      unlock();
      unlock = null;
    }
  }

  const on_key = (e) => {
    if (!open) return;
    if (e.key === "Escape") on_close();
  };

  onDestroy(() => {
    if (unlock) unlock();
  });
</script>

<!-- MUST be top-level (not inside {#if}) -->
<svelte:window on:keydown={on_key} />

{#if open && bill}
  <div class="fixed inset-0 z-50" role="dialog" aria-modal="true" aria-label="Bill details">
    <!-- Backdrop clickable -->
    <button
      type="button"
      class="absolute inset-0 bg-black/60"
      on:click={on_close}
      aria-label="Close"
    ></button>

    <!-- Panel: full screen on mobile; centered sheet on >= sm -->
    <div class="absolute inset-0 sm:inset-auto sm:left-6 sm:right-6 sm:top-20 sm:bottom-auto lg:left-8 lg:right-8">
      <div
        class="h-full sm:h-auto sm:max-h-[calc(100vh-6rem)]
               rounded-none sm:rounded-2xl
               border border-neutral-900/10 dark:border-white/10
               bg-white dark:bg-[#0B0B10]
               shadow-soft dark:shadow-softDark
               overflow-hidden"
      >
        <!-- Header (sticky on mobile so Close is always visible) -->
        <div
          class="sticky top-0 z-10
                 p-4 sm:p-6
                 flex items-start justify-between gap-4
                 border-b border-neutral-200 dark:border-white/10
                 bg-white/95 dark:bg-[#0B0B10]/95 backdrop-blur"
        >
          <div class="min-w-0">
            <div class="flex flex-wrap items-center gap-2 text-xs text-neutral-600 dark:text-neutral-400">
              <span class={`inline-flex items-center gap-1 px-2.5 py-1.5 rounded-xl text-xs ${pill_neutral()}`}>
                <span class="iconify text-[14px]" data-icon={house_icon(bill.house)}></span>
                {bill.house}
              </span>

              <!-- NO flag icon -->
              <span class={`inline-flex items-center gap-1 px-2.5 py-1.5 rounded-xl text-xs ${party_style(bill.party)}`}>
                {bill.party || "Independent / Unknown"}
              </span>

              <span class={`inline-flex items-center gap-1 px-2.5 py-1.5 rounded-xl text-xs ${pill_neutral()}`}>
                <span class="iconify text-[14px]" data-icon="mdi:map-marker-outline"></span>
                {bill.constituency || "—"}
              </span>

              <span class="text-neutral-500">#{bill.bill_id}</span>
            </div>

            <h3 class="mt-3 sm:mt-6 font-serif text-3xl sm:text-4xl font-black leading-snug text-neutral-900 dark:text-neutral-50">
              {bill.short_title}
            </h3>
          </div>

          <!-- Close always visible, top-right -->
          <button
            type="button"
            class="shrink-0 inline-flex items-center justify-center gap-2
                   px-3 py-2 rounded-xl border
                   border-neutral-900/10 dark:border-white/10
                   bg-neutral-900/5 dark:bg-white/10
                   hover:bg-neutral-900/8 dark:hover:bg-white/15
                   text-neutral-800 dark:text-neutral-100 transition"
            on:click={on_close}
            aria-label="Close panel"
          >
            <span class="iconify text-[18px]" data-icon="mdi:close"></span>
            <span class="hidden sm:inline text-sm">Close</span>
          </button>
        </div>

        <!-- Body scrolls (not the page) -->
        <div class="h-[calc(100vh-92px)] sm:h-auto sm:max-h-[calc(100vh-6rem-96px)] overflow-auto">
          <div class="p-5 sm:p-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div class="lg:col-span-2">
              <div class="text-[20px] sm:text-[22px] text-neutral-800 dark:text-neutral-200 leading-relaxed">
                {bill.long_title}
              </div>

              <div class="mt-6 flex flex-wrap gap-2">
                <a
                  class="inline-flex items-center gap-2 px-3 py-2 rounded-xl border border-neutral-200 dark:border-white/10
                         bg-white hover:bg-neutral-100 dark:bg-white/5 dark:hover:bg-white/10 transition text-sm
                         text-neutral-900 dark:text-neutral-100"
                  href={bill_link(bill.bill_id)}
                  target="_blank"
                  rel="noreferrer"
                >
                  <span class="iconify text-[18px]" data-icon="mdi:link-variant"></span>
                  Bill page
                </a>

                <a
                  class="inline-flex items-center gap-2 px-3 py-2 rounded-xl border border-neutral-200 dark:border-white/10
                         bg-white hover:bg-neutral-100 dark:bg-white/5 dark:hover:bg-white/10 transition text-sm
                         text-neutral-900 dark:text-neutral-100"
                  href={bill_link(bill.bill_id, "/news")}
                  target="_blank"
                  rel="noreferrer"
                >
                  <span class="iconify text-[18px]" data-icon="mdi:newspaper-variant-outline"></span>
                  News
                </a>

                <a
                  class="inline-flex items-center gap-2 px-3 py-2 rounded-xl border border-neutral-200 dark:border-white/10
                         bg-white hover:bg-neutral-100 dark:bg-white/5 dark:hover:bg-white/10 transition text-sm
                         text-neutral-900 dark:text-neutral-100"
                  href={bill_link(bill.bill_id, "/stages")}
                  target="_blank"
                  rel="noreferrer"
                >
                  <span class="iconify text-[18px]" data-icon="mdi:progress-clock"></span>
                  Stages
                </a>

                <a
                  class="inline-flex items-center gap-2 px-3 py-2 rounded-xl border border-neutral-200 dark:border-white/10
                         bg-white hover:bg-neutral-100 dark:bg-white/5 dark:hover:bg-white/10 transition text-sm
                         text-neutral-900 dark:text-neutral-100"
                  href={bill_link(bill.bill_id, "/publications")}
                  target="_blank"
                  rel="noreferrer"
                >
                  <span class="iconify text-[18px]" data-icon="mdi:file-multiple-outline"></span>
                  Publications
                </a>
              </div>

              {#if related(bill).length}
                <div class="mt-10">
                  <div class="flex items-center justify-between">
                    <div class="text-xs uppercase tracking-wide text-neutral-500 dark:text-neutral-500">Related bills</div>
                    <span class="iconify text-[18px] text-neutral-500 dark:text-neutral-400" data-icon="mdi:link-box-variant-outline"></span>
                  </div>

                  <div class="mt-3 space-y-2">
                    {#each related(bill) as r}
                      <a
                        class="block rounded-xl p-4 border border-neutral-200 dark:border-white/10
                               bg-white hover:bg-neutral-100 dark:bg-white/5 dark:hover:bg-white/10 transition"
                        href={bill_link(r.bill_id)}
                        target="_blank"
                        rel="noreferrer"
                      >
                        <div class="font-semibold text-neutral-900 dark:text-neutral-50">{r.short_title}</div>
                        <div class="mt-1 text-sm text-neutral-700 dark:text-neutral-300 line-clamp-2">{r.long_title}</div>
                      </a>
                    {/each}
                  </div>
                </div>
              {/if}
            </div>

            <div>
              <div class="rounded-2xl p-5 border border-neutral-200 dark:border-white/10 bg-neutral-100 dark:bg-white/5">
                <div class="flex items-center justify-between">
                  <div class="text-xs uppercase tracking-wide text-neutral-500 dark:text-neutral-500">Sponsor</div>
                  <span class="iconify text-[18px] text-neutral-500 dark:text-neutral-400" data-icon="mdi:account-tie-outline"></span>
                </div>

                {#if sponsor(bill)}
                  <div class="mt-4 flex items-center gap-3">
                    <img
                      src={sponsor(bill).photo}
                      alt={sponsor(bill).name}
                      class="h-16 w-16 rounded-xl object-cover border border-neutral-200 dark:border-white/10"
                      loading="lazy"
                    />
                    <div class="min-w-0">
                      <div class="font-bold truncate text-[17px] text-neutral-900 dark:text-neutral-50">
                        {sponsor(bill).name}
                      </div>
                      <div class="mt-1 text-sm text-neutral-700 dark:text-neutral-300 truncate">
                        {sponsor(bill).party || "Independent / Unknown"}
                      </div>
                    </div>
                  </div>

                  <a
                    class="mt-4 inline-flex items-center gap-2 text-sm text-neutral-900 dark:text-neutral-200 hover:underline"
                    href={sponsor(bill).page}
                    target="_blank"
                    rel="noreferrer"
                  >
                    <span class="iconify text-[18px]" data-icon="mdi:open-in-new"></span>
                    Member page
                  </a>
                {:else}
                  <div class="mt-3 text-sm text-neutral-700 dark:text-neutral-300">No sponsor data.</div>
                {/if}

                <div class="mt-6 pt-5 border-t border-neutral-200 dark:border-white/10">
                  <div class="text-xs uppercase tracking-wide text-neutral-500 dark:text-neutral-500">Bill ID</div>
                  <div class="mt-2 font-mono text-sm text-neutral-900 dark:text-neutral-200">{bill.bill_id}</div>
                </div>
              </div>

              <div class="mt-4 text-xs text-neutral-600 dark:text-neutral-500 flex items-start gap-2">
                <span class="iconify text-[16px] mt-[2px]" data-icon="mdi:information-outline"></span>
                <span>Tip: fast UI = virtual scrolling + lightweight dataset + minimal DOM.</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
{/if}
