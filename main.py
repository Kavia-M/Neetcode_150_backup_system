"""
NeetCode 150 Scraper

Usage:
    python main.py            # scrape all 150 problems
    python main.py --dry-run  # build folders only, no scraping
"""

import asyncio
import json
import sys
from pathlib import Path
from tqdm import tqdm
from playwright.async_api import async_playwright

from problem_list import get_problem_list
from question_scraper import scrape_question
from solution_scraper import scrape_solution
from submission_scraper import scrape_submissions

BASE_DIR = Path("NeetCode_150_Backup")
DRY_RUN  = "--dry-run" in sys.argv


def get_prob_dir(p: dict) -> Path:
    safe_name = p["name"].replace(" ", "_").replace("/", "_").replace(":", "")
    return BASE_DIR / f"{p['num']:03d}_{safe_name}"


def build_folder_structure(problems: list[dict]):
    BASE_DIR.mkdir(exist_ok=True)
    (BASE_DIR / "_Print_Ready").mkdir(exist_ok=True)
    for p in problems:
        get_prob_dir(p).mkdir(parents=True, exist_ok=True)
        (get_prob_dir(p) / "Submissions").mkdir(exist_ok=True)
    print(f"✅ Created {len(problems)} problem folders inside {BASE_DIR}/")


async def save_metadata(problems: list[dict]):
    meta = {
        "total": len(problems),
        "problems": [
            {
                "num":    p["num"],
                "name":   p["name"],
                "slug":   p["slug"],
                "folder": get_prob_dir(p).name,
            }
            for p in problems
        ],
    }
    path = BASE_DIR / "metadata.json"
    path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"✅ metadata.json → {path}")


async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        context = await browser.new_context()
        page    = await context.new_page()

        # Step 1: Manual login
        print("""
╔══════════════════════════════════════════════════╗
║  Please log in to NeetCode in the browser window ║
║                                                  ║
║  1. Click Sign in (top right)                    ║
║  2. Click GitHub                                 ║
║  3. Complete login (approve on phone if needed)  ║
╚══════════════════════════════════════════════════╝
""")
        # Use domcontentloaded — much more reliable than networkidle for Angular SPAs
        await page.goto("https://neetcode.io", wait_until="domcontentloaded")
        await asyncio.sleep(2)

        input("  Press ENTER once you are logged in... ")
        print("✅ Login confirmed. Starting scraper...\n")

        # Step 2: Get flat list of 150 problems
        problems = await get_problem_list(page)

        if not problems:
            print("❌ No problems found! Check if the tab clicked correctly.")
            input("Press ENTER to close browser...")
            await browser.close()
            return

        # Step 3: Build folder structure
        build_folder_structure(problems)

        if DRY_RUN:
            print("\n--dry-run: folders built, scraping skipped.")
            await save_metadata(problems)
            input("Press ENTER to close browser...")
            await browser.close()
            return

        # Step 4: Scrape each problem independently
        for p in tqdm(problems, desc="Scraping problems"):
            prob_dir = get_prob_dir(p)
            print(f"\n[{p['num']:>3}/150] {p['name']}")

            try:
                await scrape_question(page, p, prob_dir)
            except Exception as e:
                print(f"  ❌ question_scraper: {e}")

            try:
                await scrape_solution(page, p, prob_dir)
            except Exception as e:
                print(f"  ❌ solution_scraper: {e}")

            try:
                await scrape_submissions(page, p, prob_dir)
            except Exception as e:
                print(f"  ❌ submission_scraper: {e}")

        # Step 5: Save metadata
        await save_metadata(problems)

        await browser.close()
        print("\n🎉 Done! Backup saved to NeetCode_150_Backup/")


if __name__ == "__main__":
    asyncio.run(main())
