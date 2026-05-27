"""
Targeted scraper: search PartSelect for specific part types and add them to catalog.json.
Picks the top-rated result for each search term.

Usage:
    cd /Users/shuchang/Desktop/Instalily/scraper
    source ../backend/.venv/bin/activate
    python scrape_targets.py
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

TARGETS = [
    ("Refrigerator compressor start relay",    "Refrigerator"),
    ("Refrigerator temperature control thermostat", "Refrigerator"),
    ("Refrigerator thermistor",                "Refrigerator"),
    ("Refrigerator damper control assembly",   "Refrigerator"),
    ("Refrigerator defrost heater",            "Refrigerator"),
    ("Refrigerator defrost thermostat",        "Refrigerator"),
    ("Refrigerator main control board",        "Refrigerator"),
    ("Refrigerator water dispenser actuator",  "Refrigerator"),
    ("Refrigerator LED light module",          "Refrigerator"),
    ("Dishwasher wash pump motor assembly",    "Dishwasher"),
    ("Dishwasher water inlet valve",           "Dishwasher"),
]

# Pick at most this many parts per search term
MAX_PER_TERM = 3


async def search_part_urls(page, query: str) -> list[str]:
    """Return PS part page URLs from a PartSelect keyword search."""
    url = f"{BASE}/search/?searchterm={query.replace(' ', '+')}"
    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(2000)
    html = await page.content()
    if "Access Denied" in html:
        print(f"  BLOCKED on search: {url}")
        return []
    soup_import = __import__("bs4", fromlist=["BeautifulSoup"]).BeautifulSoup
    soup = soup_import(html, "html.parser")
    seen, urls = set(), []
    for a in soup.find_all("a", href=re.compile(r"/PS\d+")):
        href = a["href"].split("?")[0].split("#")[0]
        ps = re.search(r"PS\d+", href)
        if ps and ps.group() not in seen:
            seen.add(ps.group())
            urls.append(BASE + href if href.startswith("/") else href)
        if len(urls) >= MAX_PER_TERM:
            break
    return urls


async def main():
    catalog = json.loads(OUT.read_text())
    existing_ps = {p["ps_number"] for p in catalog}
    added = 0

    async with __import__("playwright.async_api", fromlist=["async_playwright"]).async_playwright() as pw:
        browser, ctx = await new_browser(pw)
        page = await ctx.new_page()

        for query, appliance in TARGETS:
            print(f"\n[SEARCH] {query}")
            urls = await search_part_urls(page, query)
            print(f"  Found {len(urls)} candidate URL(s)")

            found_for_term = 0
            for url in urls:
                ps = re.search(r"PS\d+", url)
                if not ps:
                    continue
                ps_num = ps.group()
                if ps_num in existing_ps:
                    print(f"  SKIP {ps_num} (already in catalog)")
                    found_for_term += 1
                    break  # already covered, move on

                print(f"  Scraping {ps_num} ...")
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    await page.wait_for_timeout(1500)
                    html = await page.content()
                    part = parse_part(html, url, appliance)
                    if part:
                        catalog.append(part)
                        existing_ps.add(part["ps_number"])
                        added += 1
                        found_for_term += 1
                        print(f"  ✓ {part['name']!r}  ${part['price']}  ★{part['rating']} ({part['review_count']} reviews)")
                        break  # one good result is enough per term
                    else:
                        print(f"  ✗ parse failed")
                except Exception as e:
                    print(f"  ✗ error: {e}")
                await __import__("asyncio").sleep(1.5)

        await browser.close()

    OUT.write_text(json.dumps(catalog, indent=2, ensure_ascii=False))
    print(f"\nDone. Added {added} new parts. Catalog now has {len(catalog)} parts.")


if __name__ == "__main__":
    asyncio.run(main())
