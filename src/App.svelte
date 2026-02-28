<script>
  import { onMount, onDestroy } from "svelte";
  import Dashboard from "./Dashboard.svelte";
  import Browse from "./Browse.svelte";
  import Topics from "./Topics.svelte";

  let tab = $state("dashboard");

  const tabs = [
    { id: "dashboard", label: "Overview", icon: "mdi:chart-box-outline" },
    { id: "browse", label: "Browse Bills", icon: "mdi:magnify" },
    { id: "topics", label: "Legislation Topics", icon: "mdi:tag-multiple-outline" }
  ];

  let theme = $state("light");
  let mq = null;
  let mq_handler = null;

  const read_theme = () => {
    try {
      return localStorage.getItem("theme") || "";
    } catch {
      return "";
    }
  };

  const write_theme = (mode) => {
    try {
      localStorage.setItem("theme", mode);
    } catch {}
  };

  const apply_theme = (mode) => {
    const root = document.documentElement;

    if (mode === "dark") root.classList.add("dark");
    else root.classList.remove("dark");

    root.style.colorScheme = mode;
  };

  let is_dark = $derived(theme === "dark");
  let theme_label = $derived(is_dark ? "Light" : "Dark");
  let theme_icon = $derived(is_dark ? "mdi:weather-sunny" : "mdi:weather-night");
  let logo_src = $derived(is_dark ? "/restorationist-logo-dark.png" : "/restorationist-logo-light.png");

  const set_theme = (mode) => {
    theme = mode;
    apply_theme(mode);
    write_theme(mode);
  };

  const toggle_theme = () => {
    set_theme(is_dark ? "light" : "dark");
  };

  onMount(() => {
    const stored = read_theme();
    mq = window.matchMedia("(prefers-color-scheme: dark)");

    const system = mq.matches ? "dark" : "light";
    theme = stored || system;
    apply_theme(theme);

    mq_handler = (e) => {
      const has_saved = !!read_theme();
      if (has_saved) return;
      theme = e.matches ? "dark" : "light";
      apply_theme(theme);
    };

    if (mq.addEventListener) mq.addEventListener("change", mq_handler);
    else mq.addListener(mq_handler);
  });

  onDestroy(() => {
    if (!mq || !mq_handler) return;
    if (mq.removeEventListener) mq.removeEventListener("change", mq_handler);
    else mq.removeListener(mq_handler);
  });
</script>

<div class="min-h-full flex flex-col bg-white text-neutral-900 dark:bg-[#070A12] dark:text-neutral-100 font-sans">
  <header class="sticky top-0 z-40 backdrop-blur bg-white/80 dark:bg-[#070A12]/75 border-b border-neutral-200/70 dark:border-white/10">
    <div class="w-full px-4 sm:px-6 lg:px-8 py-3 flex items-center gap-3">
      <a href="/" class="flex items-center gap-3 min-w-[48px]" aria-label="Home">
        <img
          src={logo_src}
          alt="The Restorationist"
          class="h-30 w-auto select-none"
          decoding="async"
          loading="eager"
        />
      </a>

      <div class="flex-1">
        <div class="flex items-center justify-center">
          <nav class="flex items-center gap-1 rounded p-1 bg-neutral-100/70 dark:bg-white/5 border border-neutral-200/60 dark:border-white/10">
            {#each tabs as t}
              <button
                type="button"
                class="px-3 py-2 rounded text-sm font-medium transition
                  {tab === t.id
                    ? 'bg-white dark:bg-white/10 shadow-soft dark:shadow-soft-dark'
                    : 'hover:bg-white/60 dark:hover:bg-white/7'}"
                onclick={() => (tab = t.id)}
                aria-current={tab === t.id ? "page" : undefined}
              >
                <span class="inline-flex items-center gap-2">
                  <span class="iconify text-[18px]" data-icon={t.icon}></span>
                  <span class="hidden sm:inline">{t.label}</span>
                </span>
              </button>
            {/each}
          </nav>
        </div>
      </div>

      <div class="flex items-center justify-end gap-2 min-w-[48px]">
        <button
          type="button"
          class="inline-flex items-center gap-2 px-3 py-2 rounded border border-neutral-200/70 dark:border-white/10
                 bg-white/70 dark:bg-white/5 hover:bg-white dark:hover:bg-white/10 transition"
          onclick={toggle_theme}
          title="Toggle theme"
        >
          <span class="iconify text-[18px]" data-icon={theme_icon}></span>
          <span class="hidden md:inline text-sm">{theme_label}</span>
        </button>
      </div>
    </div>
  </header>

  <main class="flex-1 w-full px-4 sm:px-6 lg:px-8 py-6 pb-24">
    {#if tab === "dashboard"}
      <Dashboard />
    {:else if tab === "browse"}
      <Browse />
    {:else if tab === "topics"}
      <Topics />
    {/if}
  </main>

  <footer class="fixed bottom-0 left-0 right-0 z-30 border-t border-neutral-200/70 dark:border-white/10 backdrop-blur bg-white/80 dark:bg-[#070A12]/75">
    <div class="w-full px-4 sm:px-6 lg:px-8 py-3 flex items-center justify-between text-xs text-neutral-600 dark:text-neutral-300">
      <div class="flex items-center gap-2">
        <span class="iconify text-[16px]" data-icon="mdi:creative-commons"></span>
        <span>
          <a
            href="https://creativecommons.org/licenses/by/4.0/deed.en"
            target="_blank"
            rel="noreferrer"
            class="hover:underline"
          >
            CC BY 4.0 Attribution
          </a>
        </span>
      </div>
      <div class="flex items-center gap-4">
        <a class="hover:underline" href="https://restoremag.com" target="_blank" rel="noreferrer">Restorationist&trade;</a>
        <a class="hover:underline" href="https://github.com/restorationists/bills-dashboard" target="_blank" rel="noreferrer">GitHub</a>
      </div>
    </div>
  </footer>
</div>
