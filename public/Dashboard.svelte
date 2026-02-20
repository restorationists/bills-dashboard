<script>
  import { onMount, onDestroy } from "svelte";
  import Chart from "chart.js/auto";

  import stats_url from "./statistics.json?url";
  import bills_url from "./bills_simplified.json?url";

  let loading = $state(true);
  let error = $state("");
  let stats = $state(null);
  let bills = $state([]);

  let el_mp = $state();
  let el_party = $state();
  let el_house = $state();
  let el_stage = $state();
  let c_mp, c_party, c_house, c_stage;
  let theme_observer = null;

  const normalize = (s) => (s || "").toLowerCase().trim();
  const is_dark = () => document.documentElement.classList.contains("dark");

  const party_hex = (party) => {
    const p = normalize(party);
    if (p.includes("labour")) return "#E4003B";
    if (p.includes("conservative")) return "#0087DC";
    if (p.includes("liberal democrat")) return "#FAA61A";
    if (p.includes("green")) return "#6AB023";
    if (p.includes("snp") || p.includes("scottish national")) return "#FDF38E";
    if (p.includes("plaid")) return "#3F8428";
    if (p.includes("reform")) return "#12B6CF";
    return "#9CA3AF";
  };

  const count_by = (arr, key_fn) => {
    const m = new Map();
    for (const x of arr) {
      const k = key_fn(x);
      if (!k) continue;
      m.set(k, (m.get(k) || 0) + 1);
    }
    return [...m.entries()].map(([key, count]) => ({ key, count }));
  };

  const top_n = (arr, n) => [...arr].sort((a, b) => b.count - a.count).slice(0, n);

  const destroy_all = () => {
    for (const c of [c_mp, c_party, c_house, c_stage]) c?.destroy();
    c_mp = c_party = c_house = c_stage = null;
  };

  const apply_chart_defaults = () => {
    const dark = is_dark();

    Chart.defaults.color = dark ? "#E5E7EB" : "#374151";
    Chart.defaults.borderColor = dark ? "rgba(255,255,255,0.12)" : "rgba(0,0,0,0.08)";

    Chart.defaults.plugins.legend.labels.color = Chart.defaults.color;

    Chart.defaults.plugins.tooltip.backgroundColor = dark
      ? "rgba(10,10,14,0.95)"
      : "rgba(255,255,255,0.98)";

    Chart.defaults.plugins.tooltip.titleColor = Chart.defaults.color;
    Chart.defaults.plugins.tooltip.bodyColor = Chart.defaults.color;
  };

  const build = () => {
    if (!stats || !bills.length) return;
    if (!el_mp || !el_party || !el_house || !el_stage) return;

    destroy_all();
    apply_chart_defaults();

    const prolific = top_n(count_by(bills, (b) => b.member_name), 12);
    const by_party = top_n(count_by(bills, (b) => b.party || "—"), 10);

    const by_house = stats.bills_by_originating_house || [];
    const by_stage = top_n(stats.bills_by_current_stage_description || [], 12);

    const dark = is_dark();

    c_mp = new Chart(el_mp, {
      type: "bar",
      data: {
        labels: prolific.map((x) => x.key),
        datasets: [
          {
            data: prolific.map((x) => x.count),
            backgroundColor: dark ? "#E4003B88" : "#E4003BCC",
            borderColor: "#E4003B",
            borderWidth: 1
          }
        ]
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: {
            beginAtZero: true,
            grid: { color: dark ? "rgba(255,255,255,0.10)" : "rgba(0,0,0,0.08)" }
          },
          y: {
            grid: { display: false }
          }
        }
      }
    });

    c_party = new Chart(el_party, {
      type: "bar",
      data: {
        labels: by_party.map((x) => x.key),
        datasets: [
          {
            data: by_party.map((x) => x.count),
            backgroundColor: by_party.map((x) => party_hex(x.key)),
            borderWidth: 0
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: {
            beginAtZero: true,
            grid: { color: dark ? "rgba(255,255,255,0.10)" : "rgba(0,0,0,0.08)" }
          },
          x: {
            grid: { display: false }
          }
        }
      }
    });

    c_house = new Chart(el_house, {
      type: "doughnut",
      data: {
        labels: by_house.map((x) => x.key),
        datasets: [
          {
            data: by_house.map((x) => x.count),
            backgroundColor: ["#0087DC", "#6AB023", "#FAA61A"],
            borderColor: dark ? "#0B0B10" : "#FFFFFF",
            borderWidth: 2
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "70%",
        plugins: { legend: { position: "bottom" } }
      }
    });

    c_stage = new Chart(el_stage, {
      type: "bar",
      data: {
        labels: by_stage.map((x) => x.key),
        datasets: [
          {
            data: by_stage.map((x) => x.count),
            backgroundColor: dark ? "#12B6CF66" : "#12B6CFCC",
            borderColor: "#12B6CF",
            borderWidth: 1
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: {
            beginAtZero: true,
            grid: { color: dark ? "rgba(255,255,255,0.10)" : "rgba(0,0,0,0.08)" }
          },
          x: {
            grid: { display: false }
          }
        }
      }
    });
  };

  onMount(async () => {
    try {
      const [sr, br] = await Promise.all([fetch(stats_url), fetch(bills_url)]);
      stats = await sr.json();
      bills = (await br.json()).items || [];
      loading = false;

      requestAnimationFrame(() => build());

      theme_observer = new MutationObserver(() => {
        requestAnimationFrame(() => build());
      });
      theme_observer.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ["class"]
      });
    } catch (e) {
      loading = false;
      error = e?.message || "Failed to load dashboard data.";
    }
  });

  onDestroy(() => {
    theme_observer?.disconnect();
    destroy_all();
  });
</script>

<section class="w-full">
  <div class="mb-8">
    <h1 class="font-serif text-5xl sm:text-6xl font-black tracking-tight text-neutral-900 dark:text-neutral-50">
      Bills In The UK Parliament
    </h1>
    <p class="mt-3 text-[15px] sm:text-[16px] text-neutral-700 dark:text-neutral-300 max-w-3xl">
      If we can do this for free in a few hours, why can't an organisation with taxpayer funds do it?
    </p>
  </div>

  {#if loading}
    <div class="rounded border border-neutral-200 dark:border-white/10 bg-neutral-100 dark:bg-white/5 p-6 text-neutral-700 dark:text-neutral-300">
      Loading dashboard…
    </div>
  {:else if error}
    <div class="rounded border border-rose-300 dark:border-rose-400/30 bg-rose-50 dark:bg-rose-500/10 p-6 text-rose-800 dark:text-rose-200">
      {error}
    </div>
  {:else}
    <div class="grid grid-cols-1 xl:grid-cols-2 gap-4">
      <div class="rounded border border-neutral-200 dark:border-white/10 bg-neutral-50 dark:bg-white/5 p-5 overflow-hidden">
        <div class="flex items-center justify-between">
          <div class="font-serif text-2xl font-bold text-neutral-900 dark:text-neutral-50">Most Prolific MPs</div>
          <span class="iconify text-[20px] text-neutral-500 dark:text-neutral-400" data-icon="mdi:account-star-outline"></span>
        </div>
        <div class="mt-4 h-[380px]">
          <canvas bind:this={el_mp}></canvas>
        </div>
      </div>

      <div class="rounded border border-neutral-200 dark:border-white/10 bg-neutral-100 dark:bg-white/5 p-5 overflow-hidden">
        <div class="flex items-center justify-between">
          <div class="font-serif text-2xl font-bold text-neutral-900 dark:text-neutral-50">Bills by Party</div>
          <span class="iconify text-[20px] text-neutral-500 dark:text-neutral-400" data-icon="mdi:flag-variant-outline"></span>
        </div>
        <div class="mt-4 h-[380px]">
          <canvas bind:this={el_party}></canvas>
        </div>
      </div>

      <div class="rounded border border-neutral-200 dark:border-white/10 bg-neutral-100 dark:bg-white/5 p-5 overflow-hidden">
        <div class="flex items-center justify-between">
          <div class="font-serif text-2xl font-bold text-neutral-900 dark:text-neutral-50">Originating House</div>
          <span class="iconify text-[20px] text-neutral-500 dark:text-neutral-400" data-icon="mdi:bank-outline"></span>
        </div>
        <div class="mt-4 h-[300px]">
          <canvas bind:this={el_house}></canvas>
        </div>
      </div>

      <div class="rounded border border-neutral-200 dark:border-white/10 bg-neutral-100 dark:bg-white/5 p-5 overflow-hidden">
        <div class="flex items-center justify-between">
          <div class="font-serif text-2xl font-bold text-neutral-900 dark:text-neutral-50">Current Stage (Top 12)</div>
          <span class="iconify text-[20px] text-neutral-500 dark:text-neutral-400" data-icon="mdi:progress-clock"></span>
        </div>
        <div class="mt-4 h-[300px]">
          <canvas bind:this={el_stage}></canvas>
        </div>
      </div>
    </div>
  {/if}
</section>
