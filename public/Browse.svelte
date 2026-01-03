<script>
  import { onMount, onDestroy } from "svelte";
  import BillDrawer from "./BillDrawer.svelte";
  import VirtualList from "./VirtualList.svelte";

  import bills_url from "./bills_simplified.json?url";
  import members_url from "./members.json?url";

  let loading = true;
  let error = "";

  let bills = [];
  let members_by_id = {};
  let bills_by_id = {};

  let q = "";
  let selected = null;
  let drawer_open = false;

  let row_height = 118;
  let mq = null;
  let mq_handler = null;

  const normalize = (s) => (s || "").toLowerCase().trim();

  const party_meta = (party) => {
    const p = normalize(party);

    if (p.includes("labour"))
      return {
        hex: "#ff2b5c",
        pill:
          "bg-rose-50 text-rose-800 ring-rose-200 " +
          "dark:bg-rose-500/20 dark:text-rose-100 dark:ring-rose-300/30"
      };

    if (p.includes("conservative"))
      return {
        hex: "#39a7ff",
        pill:
          "bg-sky-50 text-sky-800 ring-sky-200 " +
          "dark:bg-sky-500/20 dark:text-sky-100 dark:ring-sky-300/30"
      };

    if (p.includes("liberal democrat"))
      return {
        hex: "#ffd24a",
        pill:
          "bg-amber-50 text-amber-900 ring-amber-200 " +
          "dark:bg-amber-300/25 dark:text-amber-100 dark:ring-amber-200/30"
      };

    if (p === "green party" || p.includes("green"))
      return {
        hex: "#2ee6a6",
        pill:
          "bg-emerald-50 text-emerald-900 ring-emerald-200 " +
          "dark:bg-emerald-400/16 dark:text-emerald-100 dark:ring-emerald-200/25"
      };

    if (p.includes("snp") || p.includes("scottish national"))
      return {
        hex: "#ffe86b",
        pill:
          "bg-yellow-50 text-yellow-900 ring-yellow-200 " +
          "dark:bg-yellow-300/20 dark:text-yellow-50 dark:ring-yellow-200/30"
      };

    if (p.includes("plaid"))
      return {
        hex: "#5fe28a",
        pill:
          "bg-emerald-50 text-emerald-900 ring-emerald-200 " +
          "dark:bg-emerald-900/40 dark:text-emerald-100 dark:ring-emerald-700/40"
      };

    if (p.includes("reform"))
      return {
        hex: "#47fff3",
        pill:
          "bg-cyan-50 text-cyan-900 ring-cyan-200 " +
          "dark:bg-cyan-400/18 dark:text-cyan-100 dark:ring-cyan-200/25"
      };

    // IMPORTANT: unknown party must never render as white-on-white.
    // Use a dark grey pill in both themes.
    return {
      hex: "#a3a3a3",
      pill:
        "bg-neutral-200 text-neutral-900 ring-neutral-300 " +
        "dark:bg-white/10 dark:text-neutral-100 dark:ring-white/15"
    };
  };

  const open_bill = (b) => {
    selected = b;
    drawer_open = true;
  };

  const close_bill = () => {
    drawer_open = false;
    selected = null;
  };

  const matches = (b) => {
    const qq = normalize(q);
    if (!qq) return true;

    const hay = `${b.short_title || ""} ${b.long_title || ""} ${b.member_name || ""} ${b.constituency || ""} ${b.party || ""}`.toLowerCase();
    return hay.includes(qq);
  };

  $: qq = normalize(q);
  $: filtered = !qq
    ? bills
    : bills.filter((b) => {
        const hay = `${b.short_title || ""} ${b.long_title || ""} ${b.member_name || ""} ${b.constituency || ""} ${b.party || ""}`
          .toLowerCase();
        return hay.includes(qq);
      });


  onMount(async () => {
    mq = window.matchMedia("(min-width: 640px)");
    const apply_row_height = () => {
      row_height = mq.matches ? 118 : 92;
    };
    apply_row_height();

    mq_handler = () => apply_row_height();
    if (mq.addEventListener) mq.addEventListener("change", mq_handler);
    else mq.addListener(mq_handler);

    try {
      const [br, mr] = await Promise.all([
        fetch(bills_url, { cache: "force-cache" }),
        fetch(members_url, { cache: "force-cache" })
      ]);

      const bjson = await br.json();
      const mjson = await mr.json();

      bills = (bjson.items || [])
        .slice()
        .sort((a, b) => (a.short_title || "").localeCompare(b.short_title || ""));

      bills_by_id = Object.fromEntries(bills.map((b) => [b.bill_id, b]));
      members_by_id = Object.fromEntries((mjson.data || []).map((m) => [m.member_id, m]));

      loading = false;
    } catch (e) {
      loading = false;
      error = e?.message || "Failed to load browse data.";
    }
  });

  onDestroy(() => {
    if (!mq || !mq_handler) return;
    if (mq.removeEventListener) mq.removeEventListener("change", mq_handler);
    else mq.removeListener(mq_handler);
  });
</script>

<section class="w-full font-[Merriweather]">
  <div class="mb-6">
    <h2 class="font-serif text-4xl sm:text-5xl font-black tracking-tight text-neutral-900 dark:text-neutral-50">
      Did You Vote For Any Of This?
    </h2>
    <p class="mt-2 text-[15px] sm:text-[16px] text-neutral-600 dark:text-neutral-300">
      Did your MP explain what they were submitting? Is your money being wasted?
    </p>
  </div>

  <div class="rounded-xl border border-neutral-200 bg-white p-4 sm:p-5 dark:border-white/10 dark:bg-[#0A0C12]">
    <div class="relative">
      <span
        class="iconify absolute left-4 top-1/2 -translate-y-1/2 text-[20px] text-neutral-500 dark:text-neutral-400"
        data-icon="mdi:magnify"
      ></span>
      <input
        class="w-full pl-12 pr-4 py-4 rounded-lg
               bg-white border border-neutral-200
               text-[16px] text-neutral-900 placeholder:text-neutral-400
               focus:outline-none focus:ring-2 focus:ring-cyan-500/20
               dark:bg-black/40 dark:border-white/10 dark:text-neutral-100 dark:placeholder:text-neutral-500
               dark:focus:ring-cyan-300/25"
        placeholder="Search title, sponsor, constituency, party…"
        bind:value={q}
      />
    </div>

    <div class="mt-3 flex items-center justify-between text-xs text-neutral-500 dark:text-neutral-400">
      <div class="flex items-center gap-2">
        <span class="iconify text-[16px]" data-icon="mdi:sort-alphabetical-ascending"></span>
        A–Z listing
      </div>
      {#if !loading && !error}
        <div>
          Showing <span class="font-semibold text-neutral-800 dark:text-neutral-200">{filtered.length}</span> / {bills.length}
        </div>
      {/if}
    </div>

    <div class="mt-4 h-[70vh] rounded-xl border border-neutral-200 bg-white overflow-hidden dark:border-white/10 dark:bg-[#0A0C12]">
      {#if loading}
        <div class="p-6 text-neutral-600 dark:text-neutral-300">Loading bills…</div>
      {:else if error}
        <div class="p-6 text-rose-700 dark:text-rose-200">{error}</div>
      {:else}
        <VirtualList items={filtered} row_height={row_height} render_key={(b) => b.bill_id}>
          <!-- tighter outer padding on mobile -->
          <div slot="row" let:item class="px-0 sm:px-6 h-full">
            <button
              class="relative w-full h-full text-left flex items-center gap-2 sm:gap-5 rounded-2xl
                     px-2 sm:px-4 py-2 sm:py-0
                     transition border border-transparent
                     hover:bg-black/5 dark:hover:bg-white/[0.02]
                     hover:border-neutral-300 dark:hover:border-white/10"
              on:click={() => open_bill(item)}
            >
              <div class="shrink-0">
                <!-- smaller icon block on mobile -->
                <div class="h-8 w-8 sm:h-12 sm:w-12 rounded-2xl border border-neutral-200 bg-white
                            dark:border-white/10 dark:bg-white/[0.05]
                            flex items-center justify-center">
                  <span
                    class="iconify text-[18px] sm:text-[24px]"
                    data-icon="mdi:file-document-outline"
                    style={`color:${party_meta(item.party).hex}`}
                  ></span>
                </div>
              </div>

              <div class="min-w-0 flex-1 pr-0 sm:pr-28">
                <div class="flex items-center gap-2 min-w-0">
                  <div class="truncate font-semibold text-[16px] sm:text-[19px] text-neutral-900 dark:text-neutral-50">
                    {item.short_title}
                  </div>
                  <span class="hidden sm:inline text-xs text-neutral-500 shrink-0">#{item.bill_id}</span>
                </div>

                <div class="mt-1 text-[12px] sm:text-[14px] text-neutral-600 dark:text-neutral-300 truncate">
                  {item.member_name || "—"} · {item.constituency || "—"} · {item.house}
                </div>

                <!-- mobile pill -->
                <span
                  class={`mt-1 inline-flex sm:hidden items-center
                          px-2.5 py-1.5 rounded-lg text-[11px] leading-none ring-1
                          ${party_meta(item.party).pill}`}
                  title={item.party || "—"}
                >
                  <span class="max-w-[210px] truncate">{item.party || "Independent / Unknown"}</span>
                </span>
              </div>

              <!-- desktop floating pill -->
              <span
                class={`hidden sm:inline absolute right-12 top-1/2 -translate-y-1/2
                        inline-flex items-center
                        px-3 py-2 rounded-lg text-xs leading-none ring-1
                        ${party_meta(item.party).pill}`}
                title={item.party || "—"}
              >
                <span class="max-w-[140px] truncate">{item.party || "Independent / Unknown"}</span>
              </span>

              <div class="hidden sm:block shrink-0 absolute right-3 top-1/2 -translate-y-1/2 text-neutral-400">
                <span class="iconify text-[26px]" data-icon="mdi:chevron-right"></span>
              </div>
            </button>
          </div>
        </VirtualList>
      {/if}
    </div>
  </div>

  <BillDrawer
    open={drawer_open}
    bill={selected}
    members_by_id={members_by_id}
    bills_by_id={bills_by_id}
    on_close={close_bill}
  />
</section>
