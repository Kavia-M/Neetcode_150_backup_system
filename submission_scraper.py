import asyncio
from pathlib import Path

LANG_EXT = {
    "java":       ".java",
    "javascript": ".js",
    "python":     ".py",
    "cpp":        ".cpp",
    "csharp":     ".cs",
    "go":         ".go",
    "kotlin":     ".kt",
    "swift":      ".swift",
    "rust":       ".rs",
}


async def scrape_submissions(page, problem: dict, out_dir: Path):
    """Module 3 — Scrapes Submissions → Submissions/ folder"""
    slug            = problem["slug"]
    base_url        = f"https://neetcode.io/problems/{slug}/history"
    js              = Path("helpers.js").read_text(encoding="utf-8")
    submissions_dir = out_dir / "Submissions"
    submissions_dir.mkdir(exist_ok=True)

    try:
        # Step 1 — get total count
        await page.goto(base_url, wait_until="networkidle")
        await asyncio.sleep(3)

        rows = await page.query_selector_all("tbody tr")
        total = len(rows)
        if total == 0:
            print(f"    ℹ  No submissions for {slug}")
            return
        print(f"    Found {total} submissions")

        # submissionIndex 0 = earliest, total-1 = latest
        for idx in range(total):
            submission_idx = idx  # 0=earliest → file 1, 1→file 2...
            url = f"{base_url}?submissionIndex={submission_idx}"
            try:
                await page.goto(url, wait_until="networkidle")
                await asyncio.sleep(2)
                await page.evaluate(js)

                data = await page.evaluate("window.__nc.getSubmissionData()")
                status = data.get("status", "wrong")
                lang   = data.get("lang", "unknown")
                code   = data.get("code", "")
                ext    = LANG_EXT.get(lang, ".txt")

                filename = f"submission_{idx + 1}_{status}{ext}"
                (submissions_dir / filename).write_text(code, encoding="utf-8")
                print(f"    ✅ {filename}")

            except Exception as e:
                print(f"    ⚠  Submission {idx + 1} error: {e}")

    except Exception as e:
        print(f"    ⚠  submission_scraper failed for {slug}: {e}")

    except Exception as e:
        print(f"    ⚠  submission_scraper failed for {slug}: {e}")
