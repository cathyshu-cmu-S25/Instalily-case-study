# Scraper (production ingestion path)

This directory documents the production data pipeline — not run during the demo.

In production, a scraper would:
1. Crawl PartSelect.com product pages and repair guides.
2. Parse part metadata into the `catalog.json` schema.
3. Parse repair guides into the `repair_guides.json` schema.
4. Embed guides via `text-embedding-3-small` and upsert into pgvector.

For the demo, `backend/data/catalog.json` and `repair_guides.json` are curated
by hand and loaded directly.
