#!/usr/bin/env python3
"""
NeetCode 150 — Setup Script
Run once before first use: python setup.py
"""

import sys
import subprocess
import platform
from pathlib import Path


class SetupManager:

    def __init__(self):
        self.root   = Path.cwd()
        self.venv   = self.root / "venv"
        self.is_win = platform.system() == "Windows"

    def python(self):
        return str(self.venv / ("Scripts/python.exe" if self.is_win else "bin/python"))

    def pip(self):
        return str(self.venv / ("Scripts/pip.exe" if self.is_win else "bin/pip"))

    def run(self, cmd: str, label: str) -> bool:
        print(f"\n  ▶ {label}")
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if r.returncode == 0:
            print("    ✓ Done")
            return True
        print(f"    ✗ Failed:\n{r.stderr.strip()}")
        return False

    def step1_check_python(self) -> bool:
        print("\n" + "="*52)
        print("  Step 1 — Check Python version")
        print("="*52)
        v = sys.version_info
        print(f"  Python {v.major}.{v.minor}.{v.micro}")
        if v.major < 3 or v.minor < 9:
            print("  ✗ Need Python 3.9+")
            return False
        print("  ✓ OK")
        return True

    def step2_create_venv(self) -> bool:
        print("\n" + "="*52)
        print("  Step 2 — Create virtual environment")
        print("="*52)
        if self.venv.exists():
            print("  ✓ venv already exists — skipping")
            return True
        return self.run(f'"{sys.executable}" -m venv venv', "Creating venv")

    def step3_install_deps(self) -> bool:
        print("\n" + "="*52)
        print("  Step 3 — Install dependencies")
        print("="*52)
        req = self.root / "requirements.txt"
        if not req.exists():
            print("  ✗ requirements.txt not found")
            return False
        self.run(f'"{self.pip()}" install --upgrade pip', "Upgrade pip")
        return self.run(f'"{self.pip()}" install -r requirements.txt', "Install packages")

    def step4_playwright(self) -> bool:
        print("\n" + "="*52)
        print("  Step 4 — Install Playwright Chromium")
        print("="*52)
        ok = self.run(
            f'"{self.python()}" -m playwright install chromium',
            "Install Chromium"
        )
        if not ok:
            print(f"  ⚠  Try manually: {self.python()} -m playwright install chromium")
        return True

    def step5_validate(self) -> bool:
        print("\n" + "="*52)
        print("  Step 5 — Validate imports")
        print("="*52)
        packages = [
            ("playwright",   "Playwright"),
            ("requests",     "Requests"),
            ("tqdm",         "tqdm"),
            ("dotenv",       "python-dotenv"),
            ("bs4",          "BeautifulSoup4"),
            ("markdown",     "Markdown"),
        ]
        all_ok = True
        for pkg, name in packages:
            ok = self.run(f'"{self.python()}" -c "import {pkg}"', f"Check {name}")
            if not ok:
                all_ok = False
        return all_ok

    def step5b_node(self) -> bool:
        print("\n" + "="*52)
        print("  Step 5b — Install Node.js packages (for build_pdf.js)")
        print("="*52)
        # Check node is available
        r = subprocess.run("node --version", shell=True, capture_output=True, text=True)
        if r.returncode != 0:
            print("  ⚠  Node.js not found — install Node.js 18+ from https://nodejs.org")
            print("     Skipping npm install (build_pdf.js will not work until Node is installed)")
            return True  # non-fatal — Python scraper still works
        print(f"  ✓ Node.js {r.stdout.strip()}")
        pkg_json = self.root / "package.json"
        if not pkg_json.exists():
            print("  ⚠  package.json not found — skipping npm install")
            return True
        return self.run("npm install", "npm install (puppeteer + marked)")

    def step6_folders(self) -> bool:
        print("\n" + "="*52)
        print("  Step 6 — Create base folders")
        print("="*52)
        for folder in ["NeetCode_150_Backup", "NeetCode_150_Backup/_Print_Ready"]:
            Path(folder).mkdir(parents=True, exist_ok=True)
            print(f"  ✓ {folder}/")
        print("  (Problem folders created automatically by main.py)")
        return True

    def step7_env(self) -> bool:
        print("\n" + "="*52)
        print("  Step 7 — Check .env file")
        print("="*52)
        if Path(".env").exists():
            print("  ✓ .env already exists")
        else:
            import shutil
            if Path(".env.example").exists():
                shutil.copy(".env.example", ".env")
                print("  ✓ .env created from .env.example")
                print("  ⚠  Edit .env and fill in your GITHUB_USERNAME and GITHUB_PASSWORD")
            else:
                print("  ⚠  .env.example not found — create .env manually")
        return True

    def print_done(self):
        activate = r".\venv\Scripts\activate" if self.is_win else "source venv/bin/activate"
        print(f"""
╔══════════════════════════════════════════════════╗
║        ✓  Setup complete!                        ║
║                                                  ║
║  Next steps:                                     ║
║  1. Edit .env with your GitHub credentials       ║
║  2. Activate venv:                               ║
║     {activate:<44}                               ║
║  3. Login once (saves session):                  ║
║     python login_once.py                         ║
║  4. Run scraper:                                 ║
║     python main.py                               ║
║  5. Dry-run (folders only):                      ║
║     python main.py --dry-run                     ║
╚══════════════════════════════════════════════════╝""")

    def go(self):
        print("""
╔══════════════════════════════════════════════════╗
║     NeetCode 150 Backup — Setup Wizard           ║
╚══════════════════════════════════════════════════╝""")
        for step in [
            self.step1_check_python,
            self.step2_create_venv,
            self.step3_install_deps,
            self.step4_playwright,
            self.step5_validate,
            self.step5b_node,
            self.step6_folders,
            self.step7_env,
        ]:
            if not step():
                print("\n✗ Setup stopped. Fix the error above and re-run setup.py")
                sys.exit(1)
        self.print_done()


if __name__ == "__main__":
    SetupManager().go()
