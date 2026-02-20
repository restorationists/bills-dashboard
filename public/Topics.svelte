<script>
  import { onMount } from "svelte";
  import VirtualList from "./VirtualList.svelte";
  import BillDrawer from "./BillDrawer.svelte";

  import topics_url from "./topics.json?url";
  import bills_url from "./bills_simplified.json?url";
  import members_url from "./members.json?url";

  let loading = $state(true);
  let error = $state("");

  let topics = $state([]);
  let bills_by_id = $state({});
  let members_by_id = $state({});

  let active_slug = $state("");
  let topic_q = $state("");

  let selected = $state(null);
  let drawer_open = $state(false);

  let row_height = $state(118);
  let mq = null;
  let mq_handler = null;

  const normalize = (s) => (s || "").toLowerCase().trim();

  const open_bill = (b) => {
    selected = b;
    drawer_open = true;
  };

  const close_bill = () => {
    drawer_open = false;
    selected = null;
  };

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

    return {
      hex: "#a3a3a3",
      pill:
        "bg-neutral-200 text-neutral-900 ring-neutral-300 " +
        "dark:bg-white/10 dark:text-neutral-100 dark:ring-white/15"
    };
  };

  let active = $derived(topics.find((t) => t.slug === active_slug) || topics[0] || null);

  let active_bills = $derived(
    (active?.bills || [])
      .map((id) => bills_by_id[id])
      .filter(Boolean)
      .filter((b) => {
        const qq = normalize(topic_q);
        if (!qq) return true;
        const hay = `${b.short_title || ""} ${b.member_name || ""} ${b.constituency || ""} ${b.party || ""}`.toLowerCase();
        return hay.includes(qq);
      })
  );

  const on_keydown = (e) => {
    if (e.key !== "Escape") return;
    if (drawer_open) close_bill();
  };

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
      const [tr, br, mr] = await Promise.all([
        fetch(topics_url, { cache: "force-cache" }),
        fetch(bills_url, { cache: "force-cache" }),
        fetch(members_url, { cache: "force-cache" })
      ]);

      const tjson = await tr.json();
      const bjson = await br.json();
      const mjson = await mr.json();

      topics = (tjson.data || []).slice().sort((a, b) => a.name.localeCompare(b.name));
      bills_by_id = Object.fromEntries((bjson.items || []).map((b) => [b.bill_id, b]));
      members_by_id = Object.fromEntries((mjson.data || []).map((m) => [m.member_id, m]));

      active_slug = topics[0]?.slug || "";
      loading = false;
    } catch (e) {
      loading = false;
      error = e?.message || "Failed to load topics.";
    }
  });
</script>

<svelte:window onkeydown={on_keydown} />

<section class="w-full font-[Merriweather]">
  <div class="mb-6">
    <h2 class="font-serif text-4xl sm:text-5xl font-black tracking-tight text-neutral-900 dark:text-neutral-50">
      What Are They Passing Bills About?
    </h2>
    <p class="mt-2 text-[15px] sm:text-[16px] text-neutral-600 dark:text-neutral-300">
      Why can't Parliament group its legislation into subject areas and ideology?
    </p>
  </div>

  {#if loading}
    <div class="rounded border border-neutral-200 bg-white p-6 text-neutral-700 dark:border-white/10 dark:bg-white/[0.04] dark:text-neutral-300">
      Loading topics…
    </div>
  {:else if error}
    <div class="rounded border border-rose-300 bg-rose-50 p-6 text-rose-800 dark:border-rose-400/20 dark:bg-rose-500/10 dark:text-rose-200">
      {error}
    </div>
  {:else}
    <div class="grid grid-cols-1 lg:grid-cols-[360px_1fr] gap-4">
      <aside class="hidden lg:block rounded border border-neutral-200 bg-white shadow-sm overflow-hidden dark:border-white/10 dark:bg-white/[0.04] dark:shadow-soft-dark">
        <div class="p-4 border-b border-neutral-200 flex items-center justify-between dark:border-white/10">
          <div class="font-semibold text-neutral-900 dark:text-neutral-100">Topics</div>
          <span class="iconify text-[18px] text-neutral-500 dark:text-neutral-400" data-icon="mdi:tag-multiple-outline"></span>
        </div>

        <div class="h-[70vh] overflow-auto">
          {#each topics as t}
            <button
              type="button"
              class={`w-full text-left px-4 py-3 border-b transition
                      border-neutral-100 hover:bg-neutral-50
                      dark:border-white/5 dark:hover:bg-white/[0.06]
                      ${t.slug === active_slug ? "bg-neutral-50 dark:bg-white/[0.08]" : ""}`}
              onclick={() => (active_slug = t.slug)}
            >
              <div class="flex items-center justify-between gap-3">
                <div class="min-w-0">
                  <div class="font-semibold truncate text-neutral-900 dark:text-neutral-100">{t.name}</div>
                  <div class="text-xs truncate text-neutral-500 dark:text-neutral-500">{t.slug}</div>
                </div>
                <div class="shrink-0 text-sm text-neutral-700 dark:text-neutral-300">{t.count}</div>
              </div>
            </button>
          {/each}
        </div>
      </aside>

      <main class="rounded border border-neutral-200 bg-white shadow-sm overflow-hidden dark:border-white/10 dark:bg-[#0A0C12] dark:shadow-soft-dark">
        <div class="p-4 sm:p-5 border-b border-neutral-200 dark:border-white/10">
          <div class="lg:hidden">
            <label class="block text-xs uppercase tracking-wide text-neutral-500 dark:text-neutral-400 mb-2">
              Topic
            </label>

            <div class="relative">
              <span
                class="iconify absolute left-4 top-1/2 -translate-y-1/2 text-[18px] text-neutral-500 dark:text-neutral-400"
                data-icon="mdi:tag-outline"
              ></span>

              <select
                class="w-full appearance-none pl-11 pr-10 py-3 rounded-lg
                       bg-white border border-neutral-200
                       text-[15px] text-neutral-900
                       focus:outline-none focus:ring-2 focus:ring-cyan-500/20 focus:border-cyan-400/40
                       dark:bg-black/40 dark:border-white/10 dark:text-neutral-100
                       dark:focus:ring-cyan-300/25 dark:focus:border-cyan-300/30"
                bind:value={active_slug}
              >
                {#each topics as t}
                <option value={t.slug}>
                  {t.name.length > 42 ? t.name.slice(0, 42) + "…" : t.name} ({t.count})
                </option>
                {/each}
              </select>

              <span
                class="iconify absolute right-3 top-1/2 -translate-y-1/2 text-[20px] text-neutral-400"
                data-icon="mdi:chevron-down"
              ></span>
            </div>
          </div>

          <div class="hidden lg:block">
            <div class="text-xs uppercase tracking-wide text-neutral-500">Selected topic</div>
            <div class="mt-1 font-serif text-2xl sm:text-3xl font-black text-neutral-900 dark:text-neutral-50">
              {active?.name || "—"}
            </div>
          </div>

          <div class="mt-4 relative">
            <span
              class="iconify absolute left-4 top-1/2 -translate-y-1/2 text-[20px] text-neutral-500 dark:text-neutral-400"
              data-icon="mdi:magnify"
            ></span>
            <input
              class="w-full pl-12 pr-4 py-3 rounded-lg
                     bg-white border border-neutral-200
                     text-[15px] sm:text-[16px] text-neutral-900 placeholder:text-neutral-400
                     focus:outline-none focus:ring-2 focus:ring-cyan-500/20 focus:border-cyan-400/40
                     dark:bg-black/40 dark:border-white/10 dark:text-neutral-100 dark:placeholder:text-neutral-500
                     dark:focus:ring-cyan-300/25 dark:focus:border-cyan-300/30"
              placeholder="Filter bills within this topic…"
              bind:value={topic_q}
            />
          </div>

          <div class="mt-3 text-xs text-neutral-500 dark:text-neutral-400">
            Showing <span class="font-semibold text-neutral-800 dark:text-neutral-200">{active_bills.length}</span>
          </div>
        </div>

        <div class="h-[64vh]">
          <VirtualList items={active_bills} row_height={row_height} render_key={(b) => b.bill_id}>
            {#snippet row(item)}
              <div class="px-0 sm:px-6 h-full">
                <button
                  type="button"
                  class="relative w-full h-full text-left flex items-center gap-2 sm:gap-5 rounded
                         px-2 sm:px-4 py-2 sm:py-0
                         transition border border-transparent
                         hover:bg-black/5 dark:hover:bg-white/[0.02]
                         hover:border-neutral-300 dark:hover:border-white/10"
                  onclick={() => open_bill(item)}
                >
                  <div class="shrink-0">
                    <div
                      class="h-8 w-8 sm:h-12 sm:w-12 rounded border border-neutral-200 bg-white
                             dark:border-white/10 dark:bg-white/[0.05]
                             flex items-center justify-center"
                    >
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

                    <span
                      class={`mt-1 inline-flex sm:hidden items-center
                              px-2.5 py-1.5 rounded-lg text-[11px] leading-none ring-1
                              ${party_meta(item.party).pill}`}
                      title={item.party || "—"}
                    >
                      <span class="max-w-[210px] truncate">{item.party || "Independent / Unknown"}</span>
                    </span>
                  </div>

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
            {/snippet}
          </VirtualList>
        </div>
      </main>
    </div>

    <BillDrawer
      open={drawer_open}
      bill={selected}
      members_by_id={members_by_id}
      bills_by_id={bills_by_id}
      on_close={close_bill}
    />
  {/if}
</section>
