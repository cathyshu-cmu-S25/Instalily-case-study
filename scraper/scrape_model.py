"""
Scrape all parts for a specific model from PartSelect's model page.
Adds new parts to catalog and patches compatible_models for existing parts.

Usage:
    cd /Users/shuchang/Desktop/Instalily/scraper
    source ../backend/.venv/bin/activate
    python scrape_model.py WDT780SAEM1 Dishwasher
"""
import asyncio
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from scraper import new_browser, parse_part

BASE = "https://www.partselect.com"
OUT = Path(__file__).parent.parent / "backend" / "data" / "catalog.json"


async def collect_model_part_urls(page, model: str) -> list[str]:
    """Collect part URLs from the model's Parts page (handles pagination)."""
    urls = []
    seen = set()
    page_num = 1

    while True:
        url = f"{BASE}/Models/{model}/Parts/?start={(page_num - 1) * 20}"
        print(f"  Page {page_num}: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(2000)
        html = await page.content()

        if "Access Denied" in html[:500]:
            print("  BLOCKED")
            break

        new_count = 0
        for m in re.finditer(r'href="([^"]*PS\d+[^"]*)"', html):
            href = m.group(1).split("?")[0].split("#")[0]
            ps = re.search(r"PS\d+", href)
            if ps and ps.group() not in seen:
                seen.add(ps.group())
                full = BASE + href if href.startswith("/") else href
                urls.append(full)
                new_count += 1

        print(f"    Found {new_count} new PS links (total: {len(urls)})")

        # Stop if no new parts found on this page
        if new_count == 0:
            break

        # Check if there's a next page
        if f"start={page_num * 20}" not in html and "Next" not in html:
            break

        page_num += 1
        if page_num > 10:  # safety cap: 200 parts max
            break

        await asyncio.sleep(1.5)

    return urls


async def main(model: str, appliance_type: str):
    catalog = json.loads(OUT.read_text())
    existing_index: dict[str, int] = {p["ps_number"]: i for i, p in enumerate(catalog)}

    patched = 0
    added = 0

    async with __import__("playwright.async_api", fromlist=["async_playwright"]).async_playwright() as pw:
        browser, ctx = await new_browser(pw)
        page = await ctx.new_page()

        print(f"Collecting part URLs for model {model} ...")
        part_urls = await collect_model_part_urls(page, model)
        print(f"\nTotal parts found: {len(part_urls)}\n")

        for i, url in enumerate(part_urls):
            ps = re.search(r"PS\d+", url)
            if not ps:
                continue
            ps_num = ps.group()

            if ps_num in existing_index:
                # Patch compatible_models list if model not already there
                idx = existing_index[ps_num]
                models = catalog[idx].get("compatible_models", [])
                if model not in models:
                    models.append(model)
                    catalog[idx]["compatible_models"] = models
                    patched += 1
                    print(f"[{i+1}/{len(part_urls)}] PATCH  {ps_num} {catalog[idx]['name']}")
                else:
                    print(f"[{i+1}/{len(part_urls)}] SKIP   {ps_num} (already has model)")
                continue

            # New part — scrape it
            print(f"[{i+1}/{len(part_urls)}] SCRAPE {ps_num} ...")
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(1500)
                html = await page.content()
                part = parse_part(html, url, appliance_type)
                if part:
                    # Ensure the model is in compatible_models
                    if model not in part.get("compatible_models", []):
                        part.setdefault("compatible_models", []).append(model)
                    catalog.append(part)
                    existing_index[part["ps_number"]] = len(catalog) - 1
                    added += 1
                    print(f"  ✓ {part['name']!r}  ${part['price']}  ★{part['rating']} ({part['review_count']} reviews)")
                else:
                    print(f"  ✗ parse failed")
            except Exception as e:
                print(f"  ✗ error: {e}")
            await asyncio.sleep(1.5)

        await browser.close()

    OUT.write_text(json.dumps(catalog, indent=2, ensure_ascii=False))
    print(f"\nDone. Added {added} new parts, patched {patched} existing parts.")
    print(f"Catalog now has {len(catalog)} parts.")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python scrape_model.py <MODEL_NUMBER> <Appliance>")
        sys.exit(1)
    asyncio.run(main(sys.argv[1], sys.argv[2]))
