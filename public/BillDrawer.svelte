<script>
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
    "bg-neutral-900/5 text-neutral-700 border border-neutral-900/10 " +
    "dark:bg-white/6 dark:text-neutral-100 dark:border-white/12";

  const party_style = (party) => {
    const p = normalize(party);

    if (p.includes("labour"))
      return (
        "bg-rose-600/15 text-rose-700 border border-rose-600/20 " +
        "dark:bg-rose-500/22 dark:text-rose-100 dark:border-rose-300/25"
      );

    if (p.includes("conservative"))
      return (
        "bg-sky-600/15 text-sky-700 border border-sky-600/20 " +
        "dark:bg-sky-500/22 dark:text-sky-100 dark:border-sky-300/25"
      );

    if (p.includes("liberal democrat"))
      return (
        "bg-amber-500/18 text-amber-800 border border-amber-500/25 " +
        "dark:bg-amber-300/22 dark:text-amber-100 dark:border-amber-200/25"
      );

    if (p === "green party" || p.includes("green"))
      return (
        "bg-emerald-600/15 text-emerald-800 border border-emerald-600/20 " +
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
        "dark:bg-emerald-400/22 dark:text-emerald-100 dark:border-emerald-200/25"
      );

    if (p.includes("reform"))
      return (
        "bg-cyan-600/14 text-cyan-900 border border-cyan-600/18 " +
        "dark:bg-cyan-400/22 dark:text-cyan-100 dark:border-cyan-200/25"
      );

    return pill_neutral();
  };

  const house_icon = (h) => (h === "Commons" ? "mdi:account-group-outline" : "mdi:crown-outline");
</script>

{#if open && bill}
  <div class="fixed inset-0 z-50">
    <button class="absolute inset-0 bg-black/60" on:click={on_close} aria-label="Close"></button>

    <div class="absolute left-0 right-0 bottom-0 sm:bottom-auto sm:top-20 sm:left-6 sm:right-6 lg:left-8 lg:right-8">
      <div
        class="rounded-t-2xl sm:rounded-2xl border border-neutral-900/10 dark:border-white/10
               bg-white dark:bg-[#0B0B10] shadow-soft dark:shadow-softDark overflow-hidden"
      >
        <div class="p-5 sm:p-6 flex items-start justify-between gap-4 border-b border-neutral-200 dark:border-white/10">
          <div class="min-w-0">
            <div class="flex flex-wrap items-center gap-2 text-xs text-neutral-600 dark:text-neutral-400">
              <span class={`inline-flex items-center gap-1 px-2.5 py-1.5 rounded-xl text-xs ${pill_neutral()}`}>
                <span class="iconify text-[14px]" data-icon={house_icon(bill.house)}></span>
                {bill.house}
              </span>

              <span class={`inline-flex items-center gap-1 px-2.5 py-1.5 rounded-xl text-xs ${party_style(bill.party)}`}>
                <span class="iconify text-[14px]" data-icon="mdi:flag-variant-outline"></span>
                {bill.party || "—"}
              </span>

              <span class={`inline-flex items-center gap-1 px-2.5 py-1.5 rounded-xl text-xs ${pill_neutral()}`}>
                <span class="iconify text-[14px]" data-icon="mdi:map-marker-outline"></span>
                {bill.constituency || "—"}
              </span>

              <span class="text-neutral-500">#{bill.bill_id}</span>
            </div>

            <h3 class="mt-8 font-serif text-4xl sm:text-4xl font-black leading-snug text-neutral-900 dark:text-neutral-50">
              {bill.short_title}
            </h3>
          </div>

          <button
            class="shrink-0 inline-flex items-center gap-2 px-3 py-2 rounded-xl border
                   border-neutral-900/10 dark:border-white/10
                   bg-neutral-900/5 dark:bg-white/6
                   hover:bg-neutral-900/8 dark:hover:bg-white/10
                   text-neutral-800 dark:text-neutral-100 transition"
            on:click={on_close}
          >
            <span class="iconify text-[18px]" data-icon="mdi:close"></span>
            <span class="hidden sm:inline text-sm">Close</span>
          </button>
        </div>

        <div class="p-5 sm:p-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div class="lg:col-span-2">
            <div class="text-[22px] sm:text-[22px] text-neutral-800 dark:text-neutral-200 leading-relaxed">
              {bill.long_title}
            </div>

            <div class="mt-6 flex flex-wrap gap-2">
              <a
                class="inline-flex items-center gap-2 px-3 py-2 rounded-xl border border-neutral-200 dark:border-white/10
                       bg-white hover:bg-neutral-100 dark:bg-white/5 dark:hover:bg-white/10 transition text-sm text-neutral-900 dark:text-neutral-100"
                href={bill_link(bill.bill_id)}
                target="_blank"
                rel="noreferrer"
              >
                <span class="iconify text-[18px]" data-icon="mdi:link-variant"></span>
                Bill page
              </a>

              <a
                class="inline-flex items-center gap-2 px-3 py-2 rounded-xl border border-neutral-200 dark:border-white/10
                       bg-white hover:bg-neutral-100 dark:bg-white/5 dark:hover:bg-white/10 transition text-sm text-neutral-900 dark:text-neutral-100"
                href={bill_link(bill.bill_id, "/news")}
                target="_blank"
                rel="noreferrer"
              >
                <span class="iconify text-[18px]" data-icon="mdi:newspaper-variant-outline"></span>
                News
              </a>

              <a
                class="inline-flex items-center gap-2 px-3 py-2 rounded-xl border border-neutral-200 dark:border-white/10
                       bg-white hover:bg-neutral-100 dark:bg-white/5 dark:hover:bg-white/10 transition text-sm text-neutral-900 dark:text-neutral-100"
                href={bill_link(bill.bill_id, "/stages")}
                target="_blank"
                rel="noreferrer"
              >
                <span class="iconify text-[18px]" data-icon="mdi:progress-clock"></span>
                Stages
              </a>

              <a
                class="inline-flex items-center gap-2 px-3 py-2 rounded-xl border border-neutral-200 dark:border-white/10
                       bg-white hover:bg-neutral-100 dark:bg-white/5 dark:hover:bg-white/10 transition text-sm text-neutral-900 dark:text-neutral-100"
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
                <span
                  class="iconify text-[18px] text-neutral-500 dark:text-neutral-400"
                  data-icon="mdi:account-tie-outline"
                ></span>
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
                    <div class="mt-1 text-sm text-neutral-700 dark:text-neutral-300 truncate flex items-center gap-2">
                      <span class="iconify text-[16px]" data-icon="mdi:flag-variant-outline"></span>
                      {sponsor(bill).party}
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
{/if}
