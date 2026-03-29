import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
from problem_list import get_problem_list

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        context = await browser.new_context()
        page    = await context.new_page()

        problems = await get_problem_list(page)
        await browser.close()

    lines = []
    for p in problems:
        slug = p["slug"]
        num  = p["num"]
        name = p["name"]
        q_url = f"https://neetcode.io/problems/{slug}/question?list=neetcode150"
        s_url = f"https://neetcode.io/problems/{slug}/solution?list=neetcode150"
        lines.append(f"{num:>3}. {name}")
        lines.append(f"     Problem  : {q_url}")
        lines.append(f"     Solution : {s_url}")
        lines.append("")

    out = Path("NeetCode_150_Links.txt")
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ Saved {len(problems)} problems to {out}")

asyncio.run(main())
