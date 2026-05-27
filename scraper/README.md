# Scraper

Playwright-based scrapers for building and maintaining `backend/data/catalog.json`.

All scrapers must be run from the `backend` virtualenv:

```bash
cd /path/to/project/backend
source .venv/bin/activate
```

---

## Scripts

### `scraper.py` — full catalog build

Crawls PartSelect category pages (Refrigerator + Dishwasher, 40+ brand variants)
and scrapes each part page. Produces or updates `backend/data/catalog.json`.

```bash
python ../scraper/scraper.py            # default cap: 200 new parts
python ../scraper/scraper.py --max 400  # raise the cap
```

Uses Playwright with `headless=False` and anti-bot headers to bypass Akamai
bot protection. Rate: ~1.5 s between page loads.

---

### `scrape_model.py` — model-specific page

Scrapes all parts listed on a specific model's PartSelect page
(e.g. `partselect.com/Models/WDT780SAEM1/Parts/`).

- Patches `compatible_models` for parts already in the catalog.
- Adds genuinely new parts to the catalog.

```bash
python ../scraper/scrape_model.py WDT780SAEM1 Dishwasher
python ../scraper/scrape_model.py ED5FVGXWS05 Refrigerator
```

Use this when a specific model number needs to be fully covered (e.g. after adding
it as a demo or test case).

---

### `scrape_targets.py` — targeted part-type search

Searches PartSelect for specific part type keywords and adds the top result for
each term to the catalog. Useful for filling gaps identified in repair guides.

Edit the `TARGETS` list at the top of the file, then run:

```bash
python ../scraper/scrape_targets.py
```

---

## Catalog schema (one part object)

```json
{
  "ps_number": "PS11752778",
  "manufacturer_number": "WPW10321304",
  "url": "https://www.partselect.com/PS11752778-...",
  "name": "Refrigerator Door Shelf Bin",
  "appliance_type": "Refrigerator",
  "price": 47.40,
  "in_stock": true,
  "brands": ["Whirlpool", "KitchenAid", "Maytag"],
  "fixes_symptoms": ["Ice maker not making ice", "Door won't close"],
  "compatible_models": ["ED5FVGXWS05", "WRX988SIBM00"],
  "replaces_parts": ["AP6019471", "W10321304"],
  "install": {
    "difficulty": "Easy",
    "time": "15 min",
    "tools": [],
    "steps": ["Align the bin with the door rails", "Snap into place"]
  },
  "rating": 4.85,
  "review_count": 351
}
```

## Notes

- The scraper captures up to 30 `compatible_models` per part. Use `scrape_model.py`
  to ensure a specific model number appears in the right parts' lists.
- `parse_part()` in `scraper.py` can be imported by the other scripts — no duplication.
- In production, these scrapers would run on a schedule and upsert into a PostgreSQL
  catalog; the `DataProvider` ABC in `backend/data/provider.py` makes that swap trivial.
