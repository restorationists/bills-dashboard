/**
 * One-file Bunny Standalone Edge Script. No Python, build server, or containers.
 * POST /admin/refresh advances ONE durable batch; repeat until done/not_due.
 * A single serialized caller must drive batches (see weekly workflow).
 * Required secrets: BUNNY_STORAGE_KEY, BILLS_ADMIN_TOKEN.
 * Required variables: BUNNY_STORAGE_ZONE; optional BUNNY_STORAGE_HOST,
 * BILLS_STORAGE_PREFIX. Upload dist/ and bills-seed/{bills,topics}.json first.
 */
const API = 'https://bills-api.parliament.uk/api/v1/Bills';
const WEEK = 7 * 24 * 60 * 60 * 1000;
const FILES = ['bills.json', 'bills.csv', 'bills_simplified.json', 'bills_simplified.csv', 'members.json', 'statistics.json', 'topics.json', 'edition.json'];
const RULES = {
  'Health and social care': 'health|\\bhospitals?\\b|medical|cancer|care service|\\bnhs\\b',
  'Constitution, elections and rights': 'constitution|election|parliament|house of lords|human rights|representation of the people',
  'Business, work and employment': 'employment|worker|business|commercial|trade union',
  'Housing and planning': 'housing|homes|planning|leasehold|building safety|cladding|renters',
  'Economy and taxation': 'finance|tax|levy|treasury|sovereign grant',
  'Transport and roads': 'transport|railway|highway|road|aviation|parking|vehicle',
  'Family, children and equality': 'children|child|family|equality|parental',
  'Energy and utilities': 'energy|electricity|gas supply|water supply|utilities',
  'Education and skills': 'education|school|skills|university',
  'Justice and courts': 'court|tribunal|justice|sentencing|prison',
  'Environment and climate': 'environment|climate|pollution|recycling|biodiversity',
  'International and trade': 'international|trade agreement|export|import',
  'Policing and public safety': 'police|policing|crime|terrorism|public safety',
  'Local government and communities': 'local government|local authorit|community|communities',
  'Social welfare and benefits': 'social security|benefit|pension|welfare payment',
  'Digital, data and AI': 'digital|data|artificial intelligence|software|cyber|online',
  'Immigration and citizenship': 'immigration|asylum|citizenship|nationality',
  'Culture, sport and media': 'culture|sport|media|broadcast|football',
  'Defence and armed forces': 'defence|armed forces|military|submarine',
  'Agriculture, food and fisheries': 'agriculture|food|fisher|farm',
  'Science and research': 'science|research|space',
  'Animals and animal welfare': '\\banimal\\w*|\\breindeer\\b|\\bdogs?\\b|\\bcats?\\b|\\bferrets?\\b',
  'Fire and emergency services': 'fire service|fire and rescue|emergency service',
};
const normalize = s => String(s || '').trim().toLowerCase().replace(/\s+/g, ' ');
const snakeKey = s => s.replace(/(.)([A-Z][a-z]+)/g, '$1_$2').replace(/([a-z0-9])([A-Z])/g, '$1_$2').replaceAll('-', '_').toLowerCase();
const snake = v => Array.isArray(v) ? v.map(snake) : v && typeof v === 'object' ? Object.fromEntries(Object.entries(v).map(([k, x]) => [snakeKey(k), snake(x)])) : v;
const json = (value, status = 200) => Response.json(value, {status, headers: {'Cache-Control': 'no-store', 'Access-Control-Allow-Origin': '*'}});

export function simplify(items) {
  const groups = new Map();
  for (const b of items) {
    const key = normalize(b.short_title);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(b);
  }
  return [...groups.values()].map(group => {
    group.sort((a, b) => a.bill_id - b.bill_id);
    const b = group.at(-1), m = b.sponsors?.find(s => s.member)?.member || {};
    return {bill_id: b.bill_id, house: b.originating_house || '', short_title: b.short_title || '', long_title: b.long_title || '',
      member_id: m.member_id ?? null, member_name: m.name ?? null, party: m.party ?? null, constituency: m.member_from ?? null,
      related: group.slice(0, -1).map(b => b.bill_id)};
  }).sort((a, b) => b.bill_id - a.bill_id);
}

export function statistics(items, at) {
  const counters = {}, parties = new Map(), members = new Map(), orgs = new Map();
  const add = (name, key) => { const c = counters[name] ||= new Map(); key = String(key ?? '').trim(); c.set(key, (c.get(key) || 0) + 1); };
  const set = (map, key, id) => { if (!map.has(key)) map.set(key, new Set()); map.get(key).add(id); };
  const top = (map, n = 1000) => [...(map || new Map())].map(([key, count]) => ({key, count})).sort((a,b) => b.count - a.count).slice(0, n);
  const overall = {unique_bills: new Set(items.map(b => b.bill_id)).size, records_in_file: items.length, detail_failures: 0,
    missing_long_title: 0, missing_sponsors: 0, missing_current_stage: 0, is_act_true: 0, withdrawn_non_null: 0, defeated_true: 0};
  for (const b of items) {
    add('originating_house', b.originating_house); add('current_house', b.current_house);
    if (b.bill_type_id != null) add('bill_type_id', b.bill_type_id);
    if (b.introduced_session_id != null) add('introduced_session_id', b.introduced_session_id);
    if (b.current_stage) add('current_stage_description', b.current_stage.description); else overall.missing_current_stage++;
    if (/^\d{4}-\d{2}-\d{2}/.test(b.last_update || '')) {add('year_last_update', b.last_update.slice(0, 4)); add('year_month_last_update', b.last_update.slice(0, 7));}
    if (!String(b.long_title || '').trim()) overall.missing_long_title++;
    if (b.detail_ok === 0) overall.detail_failures++;
    if (b.is_act === true) overall.is_act_true++;
    if (b.bill_withdrawn != null) overall.withdrawn_non_null++;
    if (b.is_defeated === true) overall.defeated_true++;
    const sponsors = Array.isArray(b.sponsors) ? b.sponsors : [];
    if (!sponsors.length) overall.missing_sponsors++;
    add('sponsor_total', sponsors.length);
    let memberCount = 0;
    for (const s of sponsors) {
      const m = s.member;
      if (m?.member_id != null) {
        memberCount++; set(members, `${m.member_id}|${String(m.name || '').trim()}`, b.bill_id);
        if (m.party?.trim()) set(parties, m.party.trim(), b.bill_id);
      }
      if (s.organisation?.name?.trim()) set(orgs, s.organisation.name.trim(), b.bill_id);
    }
    add('sponsor_member', memberCount);
  }
  const counts = m => new Map([...m].map(([k, v]) => [k, v.size]));
  const out = {generated_at: at, source: 'bills.json', overall};
  for (const name of ['originating_house','current_house','bill_type_id','introduced_session_id','current_stage_description','year_last_update','year_month_last_update']) out[`bills_by_${name}`] = top(counters[name]);
  out.bills_by_party_from_sponsors = top(counts(parties), 50);
  out.bills_by_member_from_sponsors = top(counts(members), 50).map(({key, count}) => {const [id, ...name] = key.split('|'); return {member_id: Number(id), name: name.join('|'), bill_count: count};});
  out.bills_by_sponsor_organisation = top(counts(orgs), 50);
  const numericTop = name => top(counters[name]).map(row => ({...row, key: Number(row.key)}));
  out.distributions = {sponsor_member_count_per_bill: numericTop('sponsor_member'), sponsor_total_count_per_bill: numericTop('sponsor_total')};
  return out;
}

function memberData(items) {
  const members = new Map();
  for (const b of items) for (const s of b.sponsors || []) {
    const m = s.member;
    if (m?.member_id == null) continue;
    const candidate = {member_id: m.member_id, name: m.name, party: m.party, photo: m.member_photo, page: m.member_page, constituency: m.member_from};
    const previous = members.get(m.member_id) || {};
    for (const [key, val] of Object.entries(candidate)) if (val != null && (previous[key] == null || String(val).trim().length > String(previous[key]).trim().length)) previous[key] = val;
    members.set(m.member_id, previous);
  }
  return {data: [...members.values()].sort((a, b) => (a.name || '').localeCompare(b.name || ''))};
}

function topicData(bills, previous) {
  const ids = new Set(bills.map(b => b.bill_id)), assigned = new Set();
  const topics = new Map((previous?.data || []).map(t => [t.name, {...t, bills: t.bills.filter(id => ids.has(id))}]));
  for (const name of [...Object.keys(RULES), 'Other']) if (!topics.has(name)) topics.set(name, {name, slug: name.toLowerCase().replaceAll(',', '').replace(/\s+/g, '-'), bills: []});
  for (const t of topics.values()) for (const id of t.bills) assigned.add(id);
  for (const b of bills) if (!assigned.has(b.bill_id)) {
    const names = Object.entries(RULES).filter(([, pattern]) => new RegExp(pattern, 'i').test(`${b.short_title} ${b.long_title}`)).map(([name]) => name);
    for (const name of names.length ? names : ['Other']) topics.get(name).bills.push(b.bill_id);
  }
  for (const t of topics.values()) {t.bills = [...new Set(t.bills)].sort((a,b) => b-a); t.count = t.bills.length;}
  return {method: 'Previous editorial tags retained by bill ID; new IDs use title and long-title keyword matching. Multiple topics allowed.', data: [...topics.values()]};
}

function csv(rows, raw = false) {
  const flatten = (v, prefix = '', out = {}) => {
    if (Array.isArray(v)) out[prefix] = JSON.stringify(v);
    else if (v && typeof v === 'object') for (const [k, x] of Object.entries(v)) flatten(x, prefix ? `${prefix}__${k}` : k, out);
    else out[prefix] = v;
    return out;
  };
  const columns = [...new Set(rows.flatMap(row => Object.keys(raw ? flatten(row) : row)))];
  if (raw) columns.push('raw_json');
  const cell = v => {if (v == null) return ''; const text = typeof v === 'object' ? JSON.stringify(v) : String(v); return /[",\r\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;};
  return columns.join(',') + '\n' + rows.map(row => {const flat = raw ? {...flatten(row), raw_json: JSON.stringify(row)} : row; return columns.map(k => cell(flat[k])).join(',');}).join('\n') + '\n';
}

export function createHandler({env = name => globalThis.Deno?.env.get(name) ?? globalThis.process?.env[name], fetchImpl = fetch, now = () => new Date()} = {}) {
  let busy = false; // Isolate guard only. Storage has no distributed lock: use one driver.
  const getEnv = name => {const v = env(name); if (!v) throw new Error(`Missing configuration: ${name}`); return v;};
  const prefix = () => {
    const p = env('BILLS_STORAGE_PREFIX') || 'bills-experiment';
    if (!/^[\w-]+(?:\/[\w-]+)*$/.test(p)) throw new Error('Invalid experimental storage prefix');
    return p;
  };
  const storageURL = path => {
    const host = env('BUNNY_STORAGE_HOST') || 'storage.bunnycdn.com';
    if (!/^(?:[a-z]{2,3}\.)?storage\.bunnycdn\.com$/.test(host)) throw new Error('Invalid storage host');
    return `https://${host}/` + [getEnv('BUNNY_STORAGE_ZONE'), prefix(), path].filter(Boolean).join('/').split('/').map(encodeURIComponent).join('/');
  };
  // No automatic retries: an unsuccessful invocation is retried from its checkpoint.
  // Eight bill fetches + checkpoint/storage work stay far below 50 subrequests.
  const storage = async (path, method = 'GET', body) => {
    const response = await fetchImpl(storageURL(path), {method, headers: {AccessKey: getEnv('BUNNY_STORAGE_KEY'), 'Content-Type': path.endsWith('.csv') ? 'text/csv' : 'application/octet-stream'}, body, redirect: 'error', signal: AbortSignal.timeout(40_000)});
    if (response.status === 404 && method === 'GET') return null;
    if (!response.ok) throw new Error(`Storage ${method} failed (${response.status})`);
    return response;
  };
  const read = async path => {const r = await storage(path); return r ? r.json() : null;};
  const write = async (path, value) => {const r = await storage(path, 'PUT', typeof value === 'string' ? value : JSON.stringify(value)); await r.arrayBuffer();};
  const parliament = async url => {
    const r = await fetchImpl(url, {headers: {Accept: 'application/json', 'User-Agent': 'bills-dashboard-bunny/1.0'}, signal: AbortSignal.timeout(25_000)});
    if (!r.ok) throw new Error(`Parliament API failed (${r.status})`);
    return r.json();
  };
  const progress = s => ({status: s.phase === 'done' ? 'done' : 'running', phase: s.phase, snapshot: s.id, indexed: s.index?.length || 0, total: s.total, fetched: Object.keys(s.details || {}).length, pending: s.pending?.length || 0, cursor: s.cursor || 0});

  async function advance(force = false) {
    const current = await read('bills-current.json');
    let state = await read('__bills/checkpoint.json');
    if (!state || state.phase === 'done') {
      if (!force && current && now().getTime() - Date.parse(current.downloaded_at) < WEEK) return {status: 'not_due', next_due: new Date(Date.parse(current.downloaded_at) + WEEK).toISOString()};
      const basePath = current ? `bills-snapshots/${current.snapshot}` : 'bills-seed';
      const base = await read(`${basePath}/bills.json`);
      if (!base?.items?.length) throw new Error('Upload bills-seed/bills.json before first refresh');
      const topics = await read(`${basePath}/topics.json`);
      state = {id: now().toISOString().replaceAll(':', '-'), started_at: now().toISOString(), phase: 'index', base, topics, index: [], details: {}, cursor: 0};
    } else if (state.phase === 'index') {
      const page = await parliament(`${API}?CurrentHouse=All&OriginatingHouse=All&Skip=${state.index.length}&Take=200`);
      if (!Array.isArray(page.items) || !Number.isInteger(page.totalResults) || page.totalResults < 1) throw new Error('Invalid Parliament index response');
      if (state.total != null && state.total !== page.totalResults) throw new Error('Index total changed during crawl; restart the job');
      state.total = page.totalResults;
      if (!page.items.length && state.index.length < state.total) throw new Error('Incomplete index page');
      state.index.push(...page.items);
      if (state.index.length >= state.total) {
        if (state.index.length !== state.total || new Set(state.index.map(b => b.billId)).size !== state.total) throw new Error('Incomplete or duplicate index; restart the job');
        const old = new Map(state.base.items.map(b => [b.bill_id, b]));
        state.pending = state.index.filter(b => !b.lastUpdate || old.get(b.billId)?.last_update !== b.lastUpdate || old.get(b.billId)?.detail_ok !== 1).map(b => b.billId);
        state.phase = 'details';
      }
    } else if (state.phase === 'details') {
      // Parallel fetches must all settle before the response/checkpoint is written.
      const results = await Promise.allSettled(state.pending.slice(state.cursor, state.cursor + 8).map(async id => {
        const b = await parliament(`${API}/${id}`);
        if (b.billId !== id || !('longTitle' in b) || !Array.isArray(b.sponsors)) throw new Error('Incomplete bill detail response');
        return [id, snake(b)];
      }));
      const failure = results.find(r => r.status === 'rejected');
      if (failure) throw failure.reason;
      for (const r of results) state.details[r.value[0]] = r.value[1];
      state.cursor += results.length;
      if (state.cursor >= state.pending.length) state.phase = 'build';
    } else if (state.phase === 'build') {
      const old = new Map(state.base.items.map(b => [b.bill_id, b]));
      const seen = new Set();
      const items = state.index.map(index => {
        const detail = state.details[index.billId] || old.get(index.billId);
        if (!detail || (detail.detail_ok !== undefined && detail.detail_ok !== 1)) throw new Error('Missing bill details; refusing publication');
        const b = {...snake(index), ...detail, detail_ok: 1};
        delete b.short_title_md5; // Deduplication uses the normalized title directly.
        const key = normalize(b.short_title); b.duplicated = seen.has(key) ? 1 : 0; seen.add(key);
        return b;
      });
      if (items.length !== state.total) throw new Error('Bill count mismatch');
      const at = now().toISOString(), bills = simplify(items);
      const latest = items.reduce((a,b) => a > (b.last_update || '') ? a : b.last_update, '');
      const edition = {label: 'Parliament — weekly snapshot', downloaded_at: at, latest_bill_update: latest,
        scope: 'Full historical API corpus; includes Acts, backbench bills and earlier governments',
        coverage_note: `Snapshot completed ${at.slice(0,10)}; latest bill update ${latest.slice(0,10)}. Refreshed weekly; not all bills are government proposals.`};
      const manifest = {snapshot: state.id, downloaded_at: at, count: items.length, distinct_titles: bills.length, edition};
      const dir = `bills-snapshots/${state.id}`;
      // Publish all immutable snapshot files first. Old snapshots remain archives.
      await write(`${dir}/bills.json`, {downloaded_at: at, count: items.length, index_endpoint: API, items});
      await write(`${dir}/bills.csv`, csv(items, true));
      await write(`${dir}/bills_simplified.json`, {generated_at: at, source: 'bills.json', count: bills.length, items: bills});
      await write(`${dir}/bills_simplified.csv`, csv(bills));
      await write(`${dir}/members.json`, memberData(items));
      await write(`${dir}/statistics.json`, statistics(items, at));
      await write(`${dir}/topics.json`, topicData(bills, state.topics));
      await write(`${dir}/edition.json`, edition);
      // Checkpoint before publication. A retry never rewrites a visible snapshot.
      state = {id: state.id, phase: 'publish', total: items.length, manifest};
    } else if (state.phase === 'publish') {
      if (current?.snapshot !== state.id) await write('bills-current.json', state.manifest);
      state = {id: state.id, phase: 'done', total: state.total, finished_at: state.manifest.downloaded_at};
    }
    await write('__bills/checkpoint.json', state);
    return progress(state);
  }

  return async request => {
    const url = new URL(request.url), path = url.pathname;
    try {
      if (path.startsWith('/admin/')) {
        if (request.headers.get('Authorization') !== `Bearer ${getEnv('BILLS_ADMIN_TOKEN')}`) return json({error: 'Unauthorized'}, 401);
        if (path === '/admin/status' && request.method === 'GET') {const s = await read('__bills/checkpoint.json'); return json(s ? progress(s) : {status: 'not_started'});}
        if (path === '/admin/restart' && request.method === 'POST') {
          if (busy) return json({error: 'A batch is already running in this isolate'}, 409);
          busy = true;
          try {await write('__bills/checkpoint.json', null); return json({status: 'reset', message: 'Next refresh starts a new job; completed snapshots are retained.'});} finally {busy = false;}
        }
        if (path !== '/admin/refresh' || request.method !== 'POST') return json({error: 'Not found'}, 404);
        if (busy) return json({error: 'A batch is already running in this isolate'}, 409);
        busy = true;
        try {return json(await advance(url.searchParams.get('force') === '1'));} finally {busy = false;}
      }
      if (!['GET','HEAD'].includes(request.method)) return json({error: 'Method not allowed'}, 405);
      if (path === '/api/current') {
        const m = await read('bills-current.json');
        if (!m) return json({error: 'No live snapshot published yet; use bundled data'}, 404);
        return json({...m, urls: Object.fromEntries(FILES.map(f => [f, `${url.origin}/api/snapshots/${m.snapshot}/${f}`]))});
      }
      const match = path.match(/^\/api\/snapshots\/([\dTZ.-]+)\/([a-z_.]+)$/);
      if (match && FILES.includes(match[2])) {
        const r = await storage(`bills-snapshots/${match[1]}/${match[2]}`);
        if (!r) return json({error: 'Snapshot not found'}, 404);
        return new Response(request.method === 'HEAD' ? null : r.body, {headers: {'Content-Type': match[2].endsWith('.json') ? 'application/json' : 'text/csv', 'Cache-Control': 'public, max-age=604800, immutable', 'Access-Control-Allow-Origin': '*'}});
      }
      // Serve the already-built Svelte app and its public assets from Storage.
      const file = path === '/' ? 'index.html' : path.slice(1);
      if (file.includes('..') || file.includes('%') || file.includes('\\') || !/^(?:index\.html|assets\/[\w.-]+|reports\/[\w.-]+|[\w-]+\.(?:png|ico|svg|webmanifest))$/.test(file)) return json({error: 'Not found'}, 404);
      const r = await storage(file);
      if (!r) return json({error: 'File not found; upload dist/ to Storage'}, 404);
      const ext = file.split('.').at(-1), types = {html: 'text/html; charset=utf-8', js: 'text/javascript', css: 'text/css', json: 'application/json', png: 'image/png', svg: 'image/svg+xml', ico: 'image/x-icon', md: 'text/markdown', webmanifest: 'application/manifest+json'};
      return new Response(request.method === 'HEAD' ? null : r.body, {headers: {'Content-Type': types[ext] || 'application/octet-stream', 'Cache-Control': file.startsWith('assets/') ? 'public, max-age=31536000, immutable' : 'no-cache'}});
    } catch (error) {
      // Do not return upstream URLs, tokens or bodies in a public response.
      console.error('Bills backend:', error.name, error.message);
      return json({error: 'Refresh or storage request failed. The last completed snapshot remains available. Retry the same batch or inspect script logs.'}, 503);
    }
  };
}

if (globalThis.Deno) {
  const BunnySDK = await import('npm:@bunny.net/edgescript-sdk@0.12.1');
  BunnySDK.net.http.serve(createHandler());
}
