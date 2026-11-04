# Optional Bunny Edge Scripting experiment

This is an independent test of the dashboard on Bunny **Standalone Edge Scripting**. The existing Python scripts, data, archives, `npm run refresh`, and normal `npm run build` remain the default. Nothing is deployed or scheduled merely by adding these files.

All backend logic lives in [`backend.js`](backend.js). It fetches Parliament's API, saves a checkpoint after each batch, rebuilds JSON/CSV, and serves the compiled dashboard and completed snapshots from Bunny Storage. It does not invoke Python, run Vite inside the edge runtime, or require a container. The frontend is compiled once; weekly refreshes rebuild its data.

## Prepare a separate test deployment

1. Run `npm run test:bunny` and `npm run build:bunny`. The test frontend goes to `dist-bunny/`; the normal `dist/` output remains separate.
2. Use a separate experimental Storage zone, or the default `bills-experiment/` prefix within a zone. Keep the production site's files and domain untouched.
3. Upload the **contents** of `dist-bunny/` beneath that prefix. Also upload `data/bills.json` as `bills-experiment/bills-seed/bills.json` and `data/topics.json` as `bills-experiment/bills-seed/topics.json`. These seed the JS cache and preserve existing editorial topic tags. Rebuilding the frontend later does not require replacing the seeds.
4. Create a **Standalone** script, paste `backend.js` into its editor, and configure its variables/secrets below. Use its separate `bunny.run` URL for the experiment.
5. Publish the script. Before its first successful refresh, the test frontend falls back to its bundled dataset and explains that live data is unavailable.

Required variables:

- `BUNNY_STORAGE_ZONE`: the zone name.
- `BUNNY_STORAGE_HOST`: the primary region's HTTP Storage endpoint, for example `storage.bunnycdn.com` or `uk.storage.bunnycdn.com`. Defaults to Frankfurt.
- `BILLS_STORAGE_PREFIX`: defaults to `bills-experiment`. Upload frontend and seeds under this same prefix. It must be nonempty; the script does not write at the storage-zone root.

Required **secrets**, entered only in Bunny's script settings:

- `BUNNY_STORAGE_KEY`: the Storage zone password, not the global Bunny API key.
- `BILLS_ADMIN_TOKEN`: a long random token protecting the refresh endpoints.

The GitHub PAT is not needed by the deployed backend. No secrets belong in the frontend, source code, seed files, or URLs.

## Run the experiment

An authenticated `POST /admin/refresh` advances one batch and returns `running`, `done`, or `not_due`. A caller must repeat requests serially until the job completes. An ordinary request will start another refresh only after seven days; `?force=1` bypasses that cooldown for an explicit test or weekly scheduled run.

`GET /admin/status` reports the saved phase/cursor. `POST /admin/restart` discards the current checkpoint, allowing a fresh index crawl; completed snapshots remain intact. All admin requests require `Authorization: Bearer <BILLS_ADMIN_TOKEN>`. Use restart only with the driver stopped.

The optional workflow `.github/workflows/bunny-experiment.yml` is just the caller: the scrape and data generation run entirely in the single edge JS file. Configure repository Actions secrets `BILLS_SCRIPT_URL` (the script's HTTPS origin) and `BILLS_ADMIN_TOKEN` (matching Bunny). Run it manually with **Actions → Bunny scripting experiment → Run workflow**. For unattended weekly runs, set the repository variable `BILLS_EDGE_EXPERIMENT_ENABLED` to `true`. Scheduled runs are otherwise disabled. GitHub scheduled workflows run from the repository's default branch; merging this optional workflow there is necessary for the schedule. The weekly trigger uses `force=1` so minor scheduling delays do not accidentally skip a week because of the cooldown.

The workflow serializes jobs and retries failed batches. The Storage API is not a distributed locking service, and the in-script `busy` flag covers only one isolate. **Use one driver at a time**; do not run manual refresh requests while the workflow is active. If a runner stops, the next run resumes from the saved checkpoint. Do not enable the weekly workflow until the test URL, Storage and credentials have been configured and a manual run succeeds.

## Data publication and limits

The script indexes 200 bills per batch and fetches at most eight changed bill details in parallel. Unchanged bills are reused only when Parliament's update timestamp matches the cached detail. A failed batch keeps the previous checkpoint. The full current corpus can rebuild with at most 11 outgoing requests in a local mocked run, below Bunny's documented 50-request limit.

The build phase uploads all eight generated files under a new `bills-snapshots/<id>/` directory. It then saves a publication checkpoint. A separate batch switches `bills-current.json` last. Retrying an interrupted publication does not rewrite a snapshot that readers can already see. Previous snapshots remain available as archives; no retention cleanup runs automatically. `/api/current` is uncached and supplies versioned data URLs; each page uses one manifest so tabs share the same edition.

The JS rebuild uses the same normalized-title deduplication and statistics as Python. It preserves previous topic tags and classifies new IDs with the same keyword rules. Raw JS snapshots omit the unused legacy title-MD5 field. The original Starmer archive stays bundled and browsable. The dated editorial report stays editorial; refreshes do not automatically rewrite its claims.

This remains a prototype until tested on Bunny. Local tests cover the real 4,072-record corpus, parity with Python, authorization, the subrequest budget, upstream/upload failures, and interrupted publication. Passing Node tests with a 128 MB V8 heap is useful evidence, but does not prove Bunny's 128 MB active-memory limit or runtime behavior. Slow Storage or Parliament requests can still exhaust an invocation's response window; retrying resumes its checkpoint. If Parliament's index total changes mid-crawl, restart rather than publish a mixed index.

Sources: [Bunny execution limits](https://bunny.net/docs/scripting/limits), [runtime](https://bunny.net/docs/scripting/runtime), [temporary in-memory file system](https://bunny.net/docs/scripting/node-fs), [Storage HTTP API](https://bunny.net/docs/storage/http), [standalone setup](https://bunny.net/docs/scripting/quickstart). No native cron facility is assumed.
