"""
Run this ONCE to create session.json.
After that, main.py uses session.json automatically — no login needed.

Usage:
    python login_once.py
"""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()

GITHUB_USERNAME = os.getenv("GITHUB_USERNAME", "").strip()
GITHUB_PASSWORD = os.getenv("GITHUB_PASSWORD", "").strip()
SESSION_FILE    = Path("session.json")


async def main():
    print("""
╔══════════════════════════════════════════════════╗
║     NeetCode — One-Time Login Setup              ║
╚══════════════════════════════════════════════════╝
""")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        context = await browser.new_context()
        page    = await context.new_page()

        # Step 1: Go to NeetCode homepage
        print("▶ Opening NeetCode homepage...")
        await page.goto("https://neetcode.io", wait_until="networkidle")
        await asyncio.sleep(2)

        # Step 2: Click "Sign in" button (top right)
        print("▶ Clicking Sign in button...")
        try:
            sign_in_btn = page.locator("text=Sign in").last
            await sign_in_btn.click()
            await asyncio.sleep(1)
        except Exception as e:
            print(f"  ⚠  Could not click Sign in: {e}")
            input("  Please click 'Sign in' manually, then press ENTER...")

        # Step 3: Click "GitHub" from the dropdown
        print("▶ Clicking GitHub from dropdown...")
        try:
            github_btn = page.locator("text=GitHub").last
            await github_btn.wait_for(state="visible", timeout=5000)
            await github_btn.click()
            await asyncio.sleep(3)
        except Exception as e:
            print(f"  ⚠  Could not click GitHub: {e}")
            input("  Please click 'GitHub' manually, then press ENTER...")

        # Step 4: Auto-fill GitHub credentials if set in .env
        if GITHUB_USERNAME and GITHUB_PASSWORD:
            print(f"▶ Auto-filling GitHub credentials from .env...")
            try:
                await page.wait_for_selector("#login_field", timeout=10000)
                await page.fill("#login_field", GITHUB_USERNAME)
                await page.fill("#password",    GITHUB_PASSWORD)
                await page.click("[name='commit']")
                print("▶ Credentials submitted.")
            except Exception as e:
                print(f"  ⚠  Auto-fill failed: {e}")
                print("  Please fill in your GitHub credentials manually.")
        else:
            print("  ℹ  No credentials in .env — please log in manually in the browser.")

        # Step 5: Wait for GitHub device confirmation (approve on phone)
        print("""
▶ GitHub will show a verification number in the browser.
▶ Open your GitHub mobile app and tap Approve.
  (Waiting up to 2 minutes...)
""")

        try:
            # Fires instantly once GitHub redirects back to neetcode.io after phone approval
            await page.wait_for_url("*neetcode.io*", timeout=120000)
            print("✅ Login detected — redirected back to NeetCode!")
        except Exception:
            print("  ⚠  Timeout. If you are already on NeetCode, press ENTER to continue.")
            input("  Press ENTER: ")

        # Step 6: Save session
        await context.storage_state(path=str(SESSION_FILE))
        print(f"""
✅ Session saved → {SESSION_FILE}
   From now on, just run: python main.py
   No login needed until session expires.
""")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
