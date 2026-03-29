"""
NeetCode GitHub Login Handler
Reads credentials from .env and auto-fills GitHub OAuth flow.
Falls back to manual login if credentials are missing.
"""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

GITHUB_USERNAME    = os.getenv("GITHUB_USERNAME", "").strip()
GITHUB_PASSWORD    = os.getenv("GITHUB_PASSWORD", "").strip()
GITHUB_TOTP_SECRET = os.getenv("GITHUB_TOTP_SECRET", "").strip()


def get_totp_code(secret: str) -> str:
    """Generate current TOTP code from secret (if 2FA is enabled)."""
    try:
        import pyotp
        return pyotp.TOTP(secret).now()
    except ImportError:
        print("  ⚠  pyotp not installed — cannot auto-fill 2FA code.")
        print("     Install it: pip install pyotp")
        return ""


async def login(page):
    """
    Auto-login via GitHub OAuth using .env credentials.
    Falls back to manual login if .env is not set.
    """
    print("\n" + "="*52)
    print("  NEETCODE LOGIN")
    print("="*52)

    await page.goto("https://neetcode.io/login", wait_until="networkidle")
    await asyncio.sleep(2)

    # Click "Sign in with GitHub" button
    try:
        github_btn = page.locator("button:has-text('GitHub'), a:has-text('GitHub')")
        await github_btn.first.click()
        await asyncio.sleep(3)
    except Exception as e:
        print(f"  ⚠  Could not find GitHub button: {e}")
        _manual_fallback()
        return

    # ── Auto-fill if credentials are in .env ─────────────────────────────────
    if GITHUB_USERNAME and GITHUB_PASSWORD:
        print(f"  ▶ Auto-filling GitHub credentials from .env...")
        try:
            # Fill username
            await page.wait_for_selector("#login_field", timeout=10000)
            await page.fill("#login_field", GITHUB_USERNAME)
            await page.fill("#password", GITHUB_PASSWORD)
            await page.click("[name='commit']")  # "Sign in" button
            await asyncio.sleep(3)

            # ── Handle 2FA if enabled ─────────────────────────────────────────
            otp_field = page.locator("#app_totp, input[name='app_otp'], input[autocomplete='one-time-code']")
            if await otp_field.count() > 0:
                print("  ▶ 2FA detected...")
                if GITHUB_TOTP_SECRET:
                    code = get_totp_code(GITHUB_TOTP_SECRET)
                    print(f"  ▶ Auto-filling TOTP code: {code}")
                    await otp_field.first.fill(code)
                    await page.keyboard.press("Enter")
                    await asyncio.sleep(3)
                else:
                    # No TOTP secret — ask user to type the code
                    print("  ⚠  2FA required but GITHUB_TOTP_SECRET not set in .env")
                    code = input("  Enter your 2FA code manually: ").strip()
                    await otp_field.first.fill(code)
                    await page.keyboard.press("Enter")
                    await asyncio.sleep(3)

            # ── Check if we're back on NeetCode ──────────────────────────────
            current_url = page.url
            if "neetcode.io" in current_url:
                print("  ✅ Logged in successfully via .env credentials!")
                return
            else:
                print(f"  ⚠  Unexpected URL after login: {current_url}")
                print("  Falling back to manual login...")
                _manual_fallback()

        except Exception as e:
            print(f"  ⚠  Auto-login failed: {e}")
            print("  Falling back to manual login...")
            _manual_fallback()

    else:
        # ── No credentials in .env — manual fallback ─────────────────────────
        print("  ℹ  No credentials found in .env")
        print("  Tip: Copy .env.example → .env and fill in your GitHub details")
        print("       to enable fully automatic login next time.")
        _manual_fallback()


def _manual_fallback():
    print("\n  ► Please complete the GitHub login in the browser window.")
    input("  ► Press ENTER here once you are logged into NeetCode... ")
    print("  ✅ Login confirmed.\n")
