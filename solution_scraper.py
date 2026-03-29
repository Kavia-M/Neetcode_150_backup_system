from pathlib import Path

async def scrape_solution(page, p: dict, prob_dir: Path):
    slug = p["slug"]
    url = f"https://neetcode.io/problems/{slug}/solution"

    await page.goto(url, wait_until="domcontentloaded")
    await page.wait_for_timeout(3000)

    # Reload helpers.js — Angular resets window on every navigation
    js = Path("helpers.js").read_text(encoding="utf-8")
    await page.evaluate(js)

    # NEW: Click ALL Java tabs first
    tabs_clicked = await page.evaluate("window.__nc.clickAllJavaTabs()")
    print(f"  Clicked {tabs_clicked} Java tabs")
    await page.wait_for_timeout(1000 * tabs_clicked)
    await page.evaluate("window.scrollTo(0, 0)")

    # Click Java button (plain with innerText "Java", NOT role=tab)
    await page.evaluate("window.__nc.clickJavaButton()")
    await page.wait_for_timeout(1500)

    # Get explanation text — skip video/canvas/iframe/svg elements
    explanation = await page.evaluate("window.__nc.getSolutionText()")
    # page.on("console", lambda msg: print(f"  [JS] {msg.text}"))




    md = f"# Solution — {p['name']}\n"
    md += f"\n{explanation.strip()}\n"

    (prob_dir / "Solution.md").write_text(md.strip(), encoding="utf-8")
    print(f"  ✅ Solution.md saved")