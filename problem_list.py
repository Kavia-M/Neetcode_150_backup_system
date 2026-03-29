import asyncio
from pathlib import Path

PRACTICE_URL = "https://neetcode.io/practice/neetcode150"

async def get_problem_list(page) -> list[dict]:

    # Step 1: Load page
    print("Loading NeetCode 150 practice page...")
    await page.goto(PRACTICE_URL, wait_until="networkidle", timeout=60000)
    await page.wait_for_timeout(5000)

    # Step 2: Click 2nd tab — exactly from v6 which worked
    print("Clicking NeetCode 150 tab...")
    try:
        result = await page.evaluate("""
            (function() {
                var selectors = [
                    "[class*='tab-link']",
                    "[role='tab']",
                    "[class*='tab-item']",
                    "[class*='nav-item']",
                    "nav a",
                    "nav button"
                ];
                for (var i = 0; i < selectors.length; i++) {
                    var tabs = document.querySelectorAll(selectors[i]);
                    if (tabs.length >= 2) {
                        tabs[1].click();
                        return "Clicked 2nd of " + tabs.length + " | text: " + tabs[1].innerText.trim();
                    }
                }
                return null;
            })()
        """)
        print(f"  ✓ {result}" if result else "  ⚠ Tab not found")
        await page.wait_for_timeout(4000)
    except Exception as e:
        print(f"  ⚠ Tab click error: {e}")

    # Step 3: Scroll 20x to render all section rows
    print("Scrolling to render sections...")
    for _ in range(20):
        await page.evaluate("window.scrollBy(0, 400)")
        await page.wait_for_timeout(250)
    await page.evaluate("window.scrollTo(0, 0)")
    await page.wait_for_timeout(1000)

    # Step 4: Expand all sections — exactly from v6
    print("Expanding all sections...")
    try:
        clicked = await page.evaluate("""
            (function() {
                var count = 0;
                var seen = [];
                var groups = [
                    document.querySelectorAll("tr"),
                    document.querySelectorAll("[class*='header']"),
                    document.querySelectorAll("[class*='accordion']"),
                    document.querySelectorAll("[class*='section-row']"),
                    document.querySelectorAll("[class*='group-row']")
                ];
                for (var g = 0; g < groups.length; g++) {
                    var items = groups[g];
                    for (var i = 0; i < items.length; i++) {
                        var el = items[i];
                        if (seen.indexOf(el) !== -1) continue;
                        seen.push(el);
                        var hasSVG  = el.querySelector("svg") !== null;
                        var hasLink = el.querySelector("a[href*='/problems/']") !== null;
                        var text    = (el.innerText || "").trim();
                        if (hasSVG && !hasLink && text.length > 2 && text.length < 100) {
                            try { el.click(); count++; } catch(e) {}
                        }
                    }
                }
                return count;
            })()
        """)
        print(f"  Expanded {clicked} sections")
    except Exception as e:
        print(f"  ⚠ Expand error: {e}")

    await page.wait_for_timeout(3000)

    # Step 5: Scroll 20x again after expand to render all problem rows
    print("Scrolling after expand...")
    for _ in range(20):
        await page.evaluate("window.scrollBy(0, 400)")
        await page.wait_for_timeout(200)
    await page.evaluate("window.scrollTo(0, 0)")
    await page.wait_for_timeout(2000)

    # Step 6: Collect all problem links
    print("Collecting problem links...")
    all_links = await page.query_selector_all("a[href*='/problems/']")
    seen_slugs, problems, counter = set(), [], 1

    for link in all_links:
        href = await link.get_attribute("href")
        name = (await link.inner_text()).strip()
        if not href or not name:
            continue
        slug = href.split("/problems/")[-1].split("/")[0].split("?")[0].strip()
        if not slug or slug in seen_slugs:
            continue
        if len(name) < 3 or name.lower() in ["neetcode","home","roadmap","courses","practice"]:
            continue
        seen_slugs.add(slug)
        problems.append({"num": counter, "name": name, "slug": slug})
        counter += 1

    print(f"✅ Found {len(problems)} problems")
    return problems
