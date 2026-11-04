import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHandler, simplify, statistics} from './backend.js';

const indexBill = (id, update = '2026-11-04T12:00:00') => ({billId: id, shortTitle: `Bill ${id}`, originatingHouse: 'Commons', currentHouse: 'Commons', lastUpdate: update, billTypeId: 8, introducedSessionId: 40, isAct: false, currentStage: {description: '2nd reading'}});
const detailBill = id => ({...indexBill(id), longTitle: 'A Bill about schools and children.', sponsors: [{member: {memberId: 1, name: 'A Member', party: 'Labour', memberFrom: 'Example', memberPhoto: 'photo', memberPage: 'page'}}]});

function fixture({count = 17} = {}) {
  const files = new Map([
    ['bills-seed/bills.json', JSON.stringify({items: [{bill_id: 100, short_title: 'Seed bill', detail_ok: 1, last_update: '2025-01-01'}]})],
    ['bills-seed/topics.json', JSON.stringify({data: []})],
    ['index.html', '<html>experiment</html>'],
  ]);
  let calls = 0, fail = () => false;
  const handler = createHandler({
    env: name => ({BUNNY_STORAGE_ZONE: 'experiment', BUNNY_STORAGE_KEY: 'private-key', BILLS_ADMIN_TOKEN: 'admin-secret'}[name]),
    now: () => new Date('2026-11-04T12:00:00Z'),
    fetchImpl: async (url, init = {}) => {
      calls++;
      if (fail(url, init)) return new Response('Injected failure', {status: 503});
      const u = new URL(url);
      if (u.hostname === 'storage.bunnycdn.com') {
        assert.equal(init.headers.AccessKey, 'private-key');
        const key = u.pathname.replace('/experiment/bills-experiment/', '');
        if (init.method === 'PUT') {files.set(key, init.body); return new Response('{}', {status: 201});}
        return files.has(key) ? new Response(files.get(key)) : new Response('', {status: 404});
      }
      assert.equal(u.hostname, 'bills-api.parliament.uk');
      if (u.search) return Response.json({items: Array.from({length: count}, (_, i) => indexBill(i + 1)), totalResults: count});
      return Response.json(detailBill(Number(u.pathname.split('/').at(-1))));
    },
  });
  const request = (path, method = 'GET', auth = true) => handler(new Request(`https://test.bunny.run${path}`, {method, headers: auth ? {Authorization: 'Bearer admin-secret'} : {}}));
  const step = async () => {calls = 0; const r = await request('/admin/refresh', 'POST'); assert.ok(calls <= 50, `Too many subrequests: ${calls}`); return r;};
  return {files, handler, request, step, fail: fn => {fail = fn;}};
}

test('unauthorized refresh cannot write; private storage paths are not served', async () => {
  const f = fixture();
  assert.equal((await f.request('/admin/refresh', 'POST', false)).status, 401);
  assert.equal(f.files.has('__bills/checkpoint.json'), false);
  for (const path of ['/__bills/checkpoint.json', '/bills-seed/bills.json', '/.env', '/%2e%2e/.env']) assert.equal((await f.request(path)).status, 404);
});

test('batched crawl publishes a complete snapshot, serves it and gates the next week', async () => {
  const f = fixture(); let result;
  for (let i = 0; i < 15; i++) {const r = await f.step(); assert.equal(r.status, 200); result = await r.json(); if (result.status === 'done') break;}
  assert.equal(result.status, 'done');
  const manifest = await (await f.request('/api/current')).json();
  assert.equal(manifest.count, 17);
  const published = JSON.parse(f.files.get(`bills-snapshots/${manifest.snapshot}/bills.json`));
  assert.equal(published.items.length, 17);
  assert.ok(published.items.every(b => b.detail_ok === 1 && b.sponsors[0].member.member_id === 1));
  const topics = JSON.parse(f.files.get(`bills-snapshots/${manifest.snapshot}/topics.json`));
  assert.ok(topics.data.find(t => t.name === 'Education and skills').bills.length === 17);
  assert.equal((await f.request(new URL(manifest.urls['bills_simplified.json']).pathname)).status, 200);
  assert.equal((await (await f.step()).json()).status, 'not_due');
  assert.equal(await (await f.request('/')).text(), '<html>experiment</html>');
});

test('an upstream failure leaves the batch retryable and does not publish partial data', async () => {
  const f = fixture(); await f.step(); await f.step();
  const before = f.files.get('__bills/checkpoint.json');
  f.fail(url => url.endsWith('/Bills/3'));
  assert.equal((await f.step()).status, 503);
  assert.equal(f.files.get('__bills/checkpoint.json'), before);
  assert.equal(f.files.has('bills-current.json'), false);
  f.fail(() => false);
  assert.equal((await f.step()).status, 200);
});

test('a failed snapshot upload leaves the old pointer intact and can resume', async () => {
  const f = fixture({count: 1});
  const old = JSON.stringify({snapshot: '2026-10-20T12-00-00.000Z', downloaded_at: '2026-10-20T12:00:00Z'});
  f.files.set('bills-current.json', old);
  f.files.set('bills-snapshots/2026-10-20T12-00-00.000Z/bills.json', f.files.get('bills-seed/bills.json'));
  f.files.set('bills-snapshots/2026-10-20T12-00-00.000Z/topics.json', f.files.get('bills-seed/topics.json'));
  await f.step(); await f.step(); await f.step();
  f.fail((url, init) => init.method === 'PUT' && url.endsWith('/statistics.json'));
  assert.equal((await f.step()).status, 503);
  assert.equal(f.files.get('bills-current.json'), old);
  f.fail(() => false);
  assert.equal((await (await f.step()).json()).phase, 'publish');
  assert.equal(f.files.get('bills-current.json'), old);
  assert.equal((await (await f.step()).json()).status, 'done');
  assert.notEqual(f.files.get('bills-current.json'), old);
});

test('publication interrupted after pointer write retries without rewriting visible snapshot files', async () => {
  const f = fixture({count: 1});
  for (let i = 0; i < 4; i++) await f.step();
  f.fail((url, init) => init.method === 'PUT' && url.endsWith('/__bills/checkpoint.json'));
  assert.equal((await f.step()).status, 503);
  const manifest = f.files.get('bills-current.json');
  const snapshot = new Map([...f.files].filter(([k]) => k.startsWith('bills-snapshots/')));
  f.fail((url, init) => {assert.ok(!(init.method === 'PUT' && url.includes('/bills-snapshots/')), 'Visible snapshot was rewritten'); return false;});
  assert.equal((await (await f.step()).json()).status, 'done');
  assert.equal(f.files.get('bills-current.json'), manifest);
  assert.deepEqual(new Map([...f.files].filter(([k]) => k.startsWith('bills-snapshots/'))), snapshot);
});

test('JS full-corpus deduplication and statistics agree with the Python edition', async () => {
  const load = async name => JSON.parse(await readFile(new URL(`../data/${name}.json`, import.meta.url)));
  const [raw, expectedBills, expectedStats] = await Promise.all(['bills','bills_simplified','statistics'].map(load));
  assert.deepEqual(simplify(raw.items), expectedBills.items);
  const actual = statistics(raw.items, 'test');
  assert.deepEqual(actual.overall, expectedStats.overall);
  const orderless = rows => Object.fromEntries(rows.map(r => [r.key, r.count]));
  for (const key of Object.keys(expectedStats).filter(k => k.startsWith('bills_by_') && k !== 'bills_by_member_from_sponsors')) assert.deepEqual(orderless(actual[key]), orderless(expectedStats[key]), key);
  assert.deepEqual(actual.bills_by_member_from_sponsors, expectedStats.bills_by_member_from_sponsors);
  assert.deepEqual(actual.distributions, expectedStats.distributions);
});

test('the full real corpus can rebuild through Storage without refetching unchanged bills', async t => {
  const rawText = await readFile(new URL('../data/bills.json', import.meta.url), 'utf8');
  const raw = JSON.parse(rawText);
  const files = new Map([
    ['bills-seed/bills.json', rawText],
    ['bills-seed/topics.json', await readFile(new URL('../data/topics.json', import.meta.url), 'utf8')],
  ]);
  let calls = 0, maxCalls = 0, detailCalls = 0, maxDuration = 0;
  const handler = createHandler({
    env: name => ({BUNNY_STORAGE_ZONE: 'test', BUNNY_STORAGE_KEY: 'key', BILLS_ADMIN_TOKEN: 'secret'}[name]),
    now: () => new Date('2026-11-04T12:00:00Z'),
    fetchImpl: async (url, init) => {
      calls++;
      const u = new URL(url);
      if (u.hostname === 'storage.bunnycdn.com') {
        const key = u.pathname.replace('/test/bills-experiment/', '');
        if (init.method === 'PUT') {files.set(key, init.body); return new Response('{}', {status: 201});}
        return files.has(key) ? new Response(files.get(key)) : new Response('', {status: 404});
      }
      if (!u.search) {detailCalls++; throw new Error('Unchanged bill was fetched again');}
      const skip = Number(u.searchParams.get('Skip'));
      return Response.json({totalResults: raw.count, items: raw.items.slice(skip, skip + 200).map(b => ({billId: b.bill_id, lastUpdate: b.last_update}))});
    },
  });
  let result;
  for (let i = 0; i < 35; i++) {
    calls = 0;
    const start = performance.now();
    const response = await handler(new Request('https://test.bunny.run/admin/refresh', {method: 'POST', headers: {Authorization: 'Bearer secret'}}));
    assert.equal(response.status, 200);
    result = await response.json();
    maxCalls = Math.max(maxCalls, calls); maxDuration = Math.max(maxDuration, performance.now() - start);
    if (result.status === 'done') break;
  }
  assert.equal(result.status, 'done'); assert.equal(detailCalls, 0); assert.ok(maxCalls <= 50);
  const m = JSON.parse(files.get('bills-current.json'));
  assert.equal(m.count, raw.count); assert.equal(m.distinct_titles, 3287);
  assert.equal(JSON.parse(files.get(`bills-snapshots/${m.snapshot}/statistics.json`)).overall.detail_failures, 0);
  t.diagnostic(`Full corpus: maximum ${maxCalls} subrequests per batch, ${Math.round(maxDuration)}ms local batch time`);
});
