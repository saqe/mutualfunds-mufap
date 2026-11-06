# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A scheduled scraper, not an application. GitHub Actions fetch pages from MUFAP (mutual fund NAVs) and PSX (stock screener, ETF quotes), turn them into cleaned HTML tables, and commit the results back to `main` under `files/`. There is no test suite, linter, or build step, and no requirements file. Dependencies (`ai-cloudscraper`, `beautifulsoup4`) are installed inline in the workflows.

## Commands

Run from the repo root, since the parsers use relative paths.

```sh
pip install ai-cloudscraper beautifulsoup4

# Fetch a page: pretty-printed HTML goes to stdout, retry logs to stderr
python cloudflare-scraper.py "https://dps.psx.com.pk/screener" > files/psx.html

# Clean the screener table: reads files/psx.html, writes files/psx-table.html
python parse-psx.py [--limit N] [--html-output PATH]

# Summarise one ETF quote page into a one-row table
python parse-psx-ticker.py files/etfs/MZNPETF.html files/etfs/MZNPETF-table.html
```

## Architecture

Pipeline: `cloudflare-scraper.py` (fetch) → raw `files/*.html` → parser → `files/*-table.html`. The workflows in `.github/workflows/` chain these steps.

- **`cloudflare-scraper.py`** uses `cloudscraper` to get past Cloudflare and prints prettified HTML to stdout.
  - It retries up to 5 times with exponential backoff on connection errors and on HTTP 403, 404, 408, 429 and 5xx. The sites fail transiently (dropped connections, spurious 403/404), so keep 403 and 404 in the retry list.
  - Workflows redirect stdout into `files/`. A failed fetch exits non-zero, so the job stops before the commit step.
- **`parse-psx.py`** works on the screener table (`#screenerTable`).
  - It keeps only the columns in `HTML_COLUMNS`, matched by each `th`'s `data-name`.
  - It prefers each cell's `data-order` attribute, which holds the raw numeric value, over the display text.
  - It strips all attributes and unwraps `thead`/`tbody`.
- **`parse-psx-ticker.py`** builds a one-row table from an ETF quote page, with the ticker taken from the input filename stem. The `HEADERS` tuple is meant to match the screener table's columns. Metrics the ETF pages don't provide (market cap, 1-year change, dividend yield) are written as `N/A`.
- Both parsers raise `FileNotFoundError` or `ValueError` and exit 1 on a missing file or missing markup. That failure is the signal that PSX changed its HTML.

## Workflows

- **`psx.yml`** (`psx-daily-multiple`) runs four times each weekday (04:30, 06:30, 08:30 and 10:30 UTC). It fetches the screener plus the `MZNPETF` and `JSMFETF` ETF pages, runs both parsers, and pushes to `main`.
- **`mufap.yml`** (`mufap-daily`) runs weekdays at 14:30 UTC and only fetches the raw `files/mufap.html`. There is no parser for it.
- Both workflows commit as `scraping-bot` and push straight to `main`, and only commit when `files/` has changed. Each step has `timeout-minutes: 5`, sized to cover the scraper's retries, so raise it if you lengthen the backoff.
- **`retry.yml`** (`retry-failed-scrape`) watches both workflows via `workflow_run`. On failure it waits 60s and re-runs the failed jobs, up to 3 attempts in total. A re-run gets a fresh runner, so it may get a different IP. It only fires from the default branch.
- To add an ETF, add a fetch step and a parse step to `psx.yml` and create the output under `files/etfs/`.
- Committed files under `files/` are workflow output. Don't hand-edit them.
