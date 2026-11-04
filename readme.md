# UK Bills Dashboard

Svelte dashboard for the full historical collection of bills published by the UK Parliament Bills API. This includes Acts and unsuccessful proposals, government bills and private members’ bills; it is not a list of policies attributable to one prime minister.

Run `npm run dev` to view the app and `npm run build` to build it.

## Editions and archives

The original dataset (downloaded 2 January 2026) and original built app are preserved in `archives/starmer-2026-01-02/`. Its manifest records SHA-256 checksums. Use the dashboard edition selector to browse the original data. The archive includes historical bills predating Starmer.

The current edition is a working snapshot for year-end 2026, with capture and latest-update dates shown in the app. Burnham became prime minister on 20 July 2026 ([GOV.UK](https://www.gov.uk/government/people/andy-burnham)). This context does not establish who introduced any individual bill.

## Refresh

Install Python's `requests` package, then run `npm run refresh` and `npm run build`. Run this again after 31 December 2026 for the final year-end edition. A refresh does not schedule future runs or deploy the app.

The refresh archives the current data if needed, fetches the live index (without cached index pages), and refreshes bill details when Parliament's `lastUpdate` changes. It stages JSON, CSV, simplified bills, statistics, sponsor metadata and topics before replacing current data. Incomplete or duplicate downloads abort without replacing dashboard data. Keep the application stopped while publishing the generated files, then rebuild.

Topic tags are editorial: existing tags are retained by bill ID; new IDs use the keyword rules in `src/refresh.py`, with multiple topics allowed and unmatched bills assigned to Other. Topic names/counts are not official parliamentary classifications. Sponsor metadata reflects what the Bills API reports, not a separately verified current member register.

The editorial shortlist is in `public/reports/` and linked from the current edition. It is a dated, sourced opinion document, not an automatically updated ranking. `npm run report` reproduces the 4 November edition from the current raw data. The generator refuses a different capture date so a future refresh cannot silently relabel unreviewed editorial material. Review its selection, wording, status checks and date before regenerating for a later snapshot.
