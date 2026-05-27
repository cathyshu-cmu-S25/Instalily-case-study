"""
PartSelect parts scraper.
Crawls Refrigerator and Dishwasher category pages, then scrapes each part page.
Outputs to backend/data/catalog.json.

Usage:
    cd backend && source .venv/bin/activate
    python ../scraper/scraper.py [--max 200]

Rate: ~1.5s between page loads. ~200 parts ≈ 10 minutes.
"""
import asyncio
import json
import re
import sys
import time
from pathlib import Path

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

BASE = "https://www.partselect.com"
OUT = Path(__file__).parent.parent / "backend" / "data" / "catalog.json"

CATEGORY_PAGES = [
    # Refrigerator — main + all brands
    f"{BASE}/Refrigerator-Parts.htm",
    f"{BASE}/Whirlpool-Refrigerator-Parts.htm",
    f"{BASE}/GE-Refrigerator-Parts.htm",
    f"{BASE}/Frigidaire-Refrigerator-Parts.htm",
    f"{BASE}/Samsung-Refrigerator-Parts.htm",
    f"{BASE}/LG-Refrigerator-Parts.htm",
    f"{BASE}/KitchenAid-Refrigerator-Parts.htm",
    f"{BASE}/Maytag-Refrigerator-Parts.htm",
    f"{BASE}/Kenmore-Refrigerator-Parts.htm",
    f"{BASE}/Amana-Refrigerator-Parts.htm",
    f"{BASE}/Bosch-Refrigerator-Parts.htm",
    f"{BASE}/Electrolux-Refrigerator-Parts.htm",
    f"{BASE}/Jenn-Air-Refrigerator-Parts.htm",
    f"{BASE}/Hotpoint-Refrigerator-Parts.htm",
    f"{BASE}/Dacor-Refrigerator-Parts.htm",
    f"{BASE}/Haier-Refrigerator-Parts.htm",
    f"{BASE}/Sub-Zero-Refrigerator-Parts.htm",
    f"{BASE}/Thermador-Refrigerator-Parts.htm",
    # Dishwasher — main + all brands
    f"{BASE}/Dishwasher-Parts.htm",
    f"{BASE}/Whirlpool-Dishwasher-Parts.htm",
    f"{BASE}/GE-Dishwasher-Parts.htm",
    f"{BASE}/Frigidaire-Dishwasher-Parts.htm",
    f"{BASE}/Bosch-Dishwasher-Parts.htm",
    f"{BASE}/Samsung-Dishwasher-Parts.htm",
    f"{BASE}/KitchenAid-Dishwasher-Parts.htm",
    f"{BASE}/Maytag-Dishwasher-Parts.htm",
    f"{BASE}/Kenmore-Dishwasher-Parts.htm",
    f"{BASE}/LG-Dishwasher-Parts.htm",
    f"{BASE}/Amana-Dishwasher-Parts.htm",
    f"{BASE}/Electrolux-Dishwasher-Parts.htm",
    f"{BASE}/Jenn-Air-Dishwasher-Parts.htm",
    f"{BASE}/Hotpoint-Dishwasher-Parts.htm",
    f"{BASE}/Dacor-Dishwasher-Parts.htm",
    f"{BASE}/Thermador-Dishwasher-Parts.htm",
    f"{BASE}/Haier-Dishwasher-Parts.htm",
    f"{BASE}/Beko-Dishwasher-Parts.htm",
    f"{BASE}/Blomberg-Dishwasher-Parts.htm",
    f"{BASE}/SMEG-Dishwasher-Parts.htm",
    f"{BASE}/Crosley-Dishwasher-Parts.htm",
    f"{BASE}/Roper-Dishwasher-Parts.htm",
    f"{BASE}/Admiral-Dishwasher-Parts.htm",
    f"{BASE}/Speed-Queen-Dishwasher-Parts.htm",
]

MAX_PARTS = 200  # default cap


# ── browser setup ────────────────────────────────────────────────────────────

async def new_browser(pw):
    browser = await pw.chromium.launch(
        headless=False,
        args=["--disable-blink-features=AutomationControlled"],
    )
    ctx = await browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        locale="en-US",
        viewport={"width": 1280, "height": 800},
    )
    await ctx.add_init_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return browser, ctx


# ── collect part URLs from a category listing page ────────────────────────────

async def collect_urls(page, category_url: str) -> list[str]:
    await page.goto(category_url, wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(2000)
    html = await page.content()
    if "Access Denied" in html:
        print(f"  BLOCKED: {category_url}")
        return []
    soup = BeautifulSoup(html, "html.parser")
    seen = set()
    urls = []
    for a in soup.find_all("a", href=re.compile(r"/PS\d+")):
        href = a["href"].split("?")[0].split("#")[0]
        ps = re.search(r"PS(\d+)", href)
        if ps and ps.group() not in seen:
            seen.add(ps.group())
            urls.append(BASE + href if href.startswith("/") else href)
    return urls


# ── parse a single part page ──────────────────────────────────────────────────

def _text(el) -> str:
    return el.get_text(strip=True) if el else ""


def parse_part(html: str, url: str, appliance_type: str) -> dict | None:
    soup = BeautifulSoup(html, "html.parser")

    if "Access Denied" in html[:500]:
        return None

    # PS and MFR numbers
    ps_match = re.search(r"PS(\d+)", url)
    if not ps_match:
        return None
    ps_number = ps_match.group()

    crossref = soup.find(class_="pd__crossref")
    mfr_number = ""
    if crossref:
        sm = crossref.find(class_="text-sm")
        if sm:
            spans = sm.find_all("span", class_="text-teal")
            if len(spans) >= 2:
                mfr_number = spans[1].get_text(strip=True)

    # Name
    h1 = soup.find("h1")
    name = _text(h1).replace(mfr_number, "").strip() if h1 else ""

    # Price
    price_el = soup.find(itemprop="price")
    try:
        price = float(price_el["content"]) if price_el else 0.0
    except (TypeError, ValueError):
        price = 0.0

    # In stock
    avail = soup.find(class_=re.compile(r"js-partAvailability"))
    in_stock = "out" not in _text(avail).lower() if avail else True
    if not avail:
        stock_el = soup.find(string=re.compile(r"In Stock", re.I))
        in_stock = stock_el is not None

    # Rating / review count
    rating_el = soup.find(itemprop="ratingValue")
    rating = float(rating_el["content"]) if rating_el else 0.0
    review_el = soup.find(itemprop="reviewCount")
    review_count = int(review_el["content"]) if review_el else 0

    # Brands — from crossref list
    brands = []
    if crossref:
        for row in crossref.select(".pd__crossref__list .row"):
            cols = row.find_all("div", recursive=False)
            if cols:
                b = cols[0].get_text(strip=True)
                if b and b not in brands:
                    brands.append(b)

    # Compatible models — from crossref list (limit 30)
    compatible_models = []
    if crossref:
        for a in crossref.select(".pd__crossref__list a")[:30]:
            m = a.get_text(strip=True)
            if m:
                compatible_models.append(m)

    # Fixes symptoms
    sym_label = soup.find(string=re.compile("fixes the following symptoms", re.I))
    fixes_symptoms = []
    if sym_label:
        ul = sym_label.find_parent().find_next_sibling("ul")
        if ul:
            fixes_symptoms = [li.get_text(strip=True) for li in ul.find_all("li")]

    # Replaces parts
    rep_label = soup.find(string=re.compile("replaces these", re.I))
    replaces_parts = []
    if rep_label:
        container = rep_label.find_parent().find_next_sibling()
        if container:
            raw = container.get_text(strip=True)
            replaces_parts = [p.strip() for p in raw.split(",") if p.strip()]

    # Install: difficulty + time from repair-rating widget
    difficulty = "Easy"
    install_time = ""
    rating_container = soup.find(class_="pd__repair-rating__container")
    if rating_container:
        p_tags = rating_container.find_all("p", class_="bold")
        for p in p_tags:
            t = p.get_text(strip=True)
            if "easy" in t.lower() or "difficult" in t.lower() or "expert" in t.lower():
                difficulty = t
            elif "min" in t.lower() or "hour" in t.lower():
                install_time = t

    # Install steps — look for ordered list near "Installation Instructions"
    install_header = soup.find(id="InstallationInstructions")
    steps = []
    if install_header:
        section = install_header.find_next_sibling()
        while section and not steps:
            ol = section.find("ol") if section.name != "ol" else section
            if ol:
                steps = [li.get_text(strip=True) for li in ol.find_all("li") if li.get_text(strip=True)]
            section = section.find_next_sibling() if section else None

    # Canonical URL (strip query/fragment)
    canonical_url = url.split("?")[0].split("#")[0]

    return {
        "ps_number": ps_number,
        "manufacturer_number": mfr_number,
        "url": canonical_url,
        "name": name,
        "appliance_type": appliance_type,
        "price": price,
        "in_stock": in_stock,
        "brands": brands,
        "fixes_symptoms": fixes_symptoms,
        "compatible_models": compatible_models,
        "replaces_parts": replaces_parts,
        "install": {
            "difficulty": difficulty,
            "time": install_time,
            "tools": [],
            "steps": steps,
        },
        "rating": round(rating, 2),
        "review_count": review_count,
    }


# ── main ──────────────────────────────────────────────────────────────────────

SEARCH_URL_PATTERN = re.compile(r"search/\?searchterm=PS\d+$")


async def main(max_parts: int):
    seen_ps: set[str] = set()
    results: list[dict] = []
    # Index for fast lookup when patching URLs
    results_index: dict[str, int] = {}

    # Keep existing catalog entries; flag those with placeholder search URLs for re-scrape
    needs_url: list[tuple[str, str]] = []  # (ps_number, appliance_type)
    if OUT.exists():
        existing = json.loads(OUT.read_text())
        for part in existing:
            seen_ps.add(part["ps_number"])
            results_index[part["ps_number"]] = len(results)
            results.append(part)
            if SEARCH_URL_PATTERN.search(part.get("url", "")):
                needs_url.append((part["ps_number"], part["appliance_type"]))
        print(f"Loaded {len(results)} existing parts ({len(needs_url)} need real URL).")

    async with async_playwright() as pw:
        browser, ctx = await new_browser(pw)
        page = await ctx.new_page()

        # 1. Collect URLs from all category pages
        all_urls: list[tuple[str, str]] = []  # (url, appliance_type)
        for cat_url in CATEGORY_PAGES:
            appliance = "Refrigerator" if "Refrigerator" in cat_url else "Dishwasher"
            print(f"Collecting URLs from {cat_url} ...")
            urls = await collect_urls(page, cat_url)
            print(f"  → {len(urls)} parts found")
            for u in urls:
                ps = re.search(r"PS\d+", u)
                if ps and ps.group() not in seen_ps:
                    all_urls.append((u, appliance))
            await asyncio.sleep(1.5)

        print(f"\nTotal new parts to scrape: {len(all_urls)} (cap: {max_parts})")
        all_urls = all_urls[:max_parts]

        # 2. Scrape each new part page
        for i, (url, appliance) in enumerate(all_urls):
            ps = re.search(r"PS\d+", url).group()
            if ps in seen_ps:
                continue
            print(f"[{i+1}/{len(all_urls)}] {ps} ({appliance}) ...")
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(1500)
                html = await page.content()
                part = parse_part(html, url, appliance)
                if part:
                    seen_ps.add(part["ps_number"])
                    results.append(part)
                    print(f"  ✓ {part['name']!r} ${part['price']}")
                else:
                    print(f"  ✗ parse failed or blocked")
            except Exception as e:
                print(f"  ✗ error: {e}")
            await asyncio.sleep(1.5)

        # 3. Patch real URLs for parts that only have search placeholder URLs
        if needs_url:
            print(f"\nPatching URLs for {len(needs_url)} existing parts ...")
            for i, (ps, appliance) in enumerate(needs_url):
                search_url = f"https://www.partselect.com/search/?searchterm={ps}"
                print(f"[{i+1}/{len(needs_url)}] {ps} ...")
                try:
                    await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
                    await page.wait_for_timeout(1500)
                    # The search page should redirect or show the part — grab the final URL
                    final_url = page.url.split("?")[0].split("#")[0]
                    if ps in final_url and "search" not in final_url:
                        idx = results_index[ps]
                        results[idx]["url"] = final_url
                        print(f"  ✓ {final_url}")
                    else:
                        # Try clicking the first result link
                        link = page.locator(f"a[href*='{ps}']").first
                        href = await link.get_attribute("href")
                        if href:
                            real = ("https://www.partselect.com" + href if href.startswith("/") else href).split("?")[0]
                            idx = results_index[ps]
                            results[idx]["url"] = real
                            print(f"  ✓ {real}")
                        else:
                            print(f"  ✗ could not find real URL")
                except Exception as e:
                    print(f"  ✗ {e}")
                await asyncio.sleep(1.5)

        await browser.close()

    OUT.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"\nDone. {len(results)} parts saved to {OUT}")


if __name__ == "__main__":
    cap = int(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else MAX_PARTS
    asyncio.run(main(cap))
