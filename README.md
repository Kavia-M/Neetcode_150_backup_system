# NeetCode 150 Scraper

Scrapes all 150 problems from [neetcode.io](https://neetcode.io/practice) and saves
them as an organized local backup with Markdown files and your own submissions.
Then builds a print-ready PDF book using Node.js + Puppeteer.

---

## Project Structure

```
neetcode_scraper/
├── helpers.js               ← Playwright JS helpers (loaded at runtime)
├── build_pdf.js             ← Node.js PDF builder (run after scraping)
├── login_once.py            ← Run ONCE to save session.json
├── main.py                  ← Orchestrator — run this every time
├── problem_list.py          ← Clicks Show All, scrapes 150 problem slugs
├── question_scraper.py      ← Module 1: saves Problem_Statement.md + Hint_page.md
├── solution_scraper.py      ← Module 2: saves Solution.md (Java)
├── submission_scraper.py    ← Module 3: saves your submissions
├── setup.py                 ← One-time environment setup wizard
├── topicsAndProblems.md     ← Section groupings used by PDF builder
├── requirements.txt         ← Python dependencies
├── package.json             ← Node.js dependencies (puppeteer, marked)
├── .env.example             ← Copy to .env and fill credentials
└── README.md
```

---

## Output Generated

Running `python main.py` produces:

```
NeetCode_150_Backup/
├── metadata.json                          ← problem list index
├── _Print_Ready/                          ← reserved for print assets
│
├── 001_Contains_Duplicate/
│   ├── Problem_Statement.md               ← problem description, constraints, examples
│   ├── Hint_page.md                       ← hints (if available on neetcode.io)
│   ├── Solution.md                        ← Java solution + explanation
│   └── Submissions/
│       ├── submission_1_wrong.java        ← your past submissions (earliest first)
│       └── submission_2_correct.java
│
├── 002_Valid_Anagram/
│   ├── Problem_Statement.md
│   ├── Hint_page.md
│   ├── Solution.md
│   └── Submissions/
│       └── submission_1_correct.cpp
│
│   ... (150 folders total, numbered 001–150)
│
└── 150_Reverse_Integer/
    ├── Problem_Statement.md
    ├── Hint_page.md
    ├── Solution.md
    └── Submissions/
```

### File naming rules

| File | Contents |
|---|---|
| `Problem_Statement.md` | Title, difficulty, acceptance rate, LeetCode ref, problem body, constraints, examples, company tags |
| `Hint_page.md` | Hints 1–N (only created if hints exist) |
| `Solution.md` | Java solution code + written explanation scraped from neetcode.io |
| `submission_N_correct.ext` | Accepted submission (N = chronological order, earliest = 1) |
| `submission_N_wrong.ext` | Wrong/TLE submission |
| `metadata.json` | JSON index: `{ total, problems: [{num, name, slug, folder}] }` |

Submission file extensions match the language: `.java` `.cpp` `.py` `.js` `.go` `.kt` `.swift` `.rs` `.cs`

---

## Quick Start

### Step 1 — Setup (run once)

Installs Python venv, all pip packages, Playwright Chromium, and Node.js packages.

```bash
python setup.py
```

> Requires **Python 3.9+** and **Node.js 18+** installed on your system.

### Step 2 — Add credentials

```bash
cp .env.example .env
# Edit .env — add your GITHUB_USERNAME and GITHUB_PASSWORD
```

### Step 3 — Activate venv

```bash
source venv/bin/activate      # macOS / Linux
.\venv\Scripts\activate       # Windows
```

### Step 4 — Login once (saves session)

```bash
python login_once.py
```

- Browser opens → auto-fills your GitHub credentials from `.env`
- GitHub shows a **verification number** on screen
- Open **GitHub mobile app** → tap **Approve**
- Session saved to `session.json` automatically
- **You never need to do this again** (until session expires)

### Step 5 — Run scraper

```bash
python main.py
```

1. A browser window opens and navigates to neetcode.io
2. Press **ENTER** in the terminal once you see you are logged in
3. The scraper fetches all 150 problems automatically
4. All files are saved to `NeetCode_150_Backup/`

### Step 6 — Build PDF

```bash
node build_pdf.js
```

- Reads all Markdown files from `NeetCode_150_Backup/`
- Renders a fully formatted A4 PDF book
- Output: **`NeetCode_150_Book.pdf`** in the project root

### Dry-run (folders only, no scraping)

```bash
python main.py --dry-run
```

---

## How It Works

| Module | Approach | Output |
|---|---|---|
| `problem_list.py` | Clicks NeetCode 150 tab, expands all sections, collects 150 problem links | list of slugs |
| `question_scraper.py` | `requests.get()` for body + parses `<details>` blocks for hints/company tags | `Problem_Statement.md`, `Hint_page.md` |
| `solution_scraper.py` | Playwright, clicks Java tab, reads CodeMirror 6 `.cm-line` + explanation text | `Solution.md` |
| `submission_scraper.py` | Playwright (uses saved session), iterates `?submissionIndex=N` | `Submissions/*.java/.py/.cpp` etc. |
| `build_pdf.js` | Node.js + Puppeteer, renders HTML→PDF via headless Chromium | `NeetCode_150_Book.pdf` |

### Key Technical Notes

- **helpers.js reloaded after every `page.goto()`** — Angular SPA resets `window` on route change
- **No inline JS** in `page.evaluate()` — all JS lives in `helpers.js` to avoid `\n` escape issues
- **Topics section** is empty in HTTP response — Playwright clicks accordion and reads DOM
- **Java button** is a plain `<button>`, not `[role='tab']`
- **CodeMirror 6** code lives in `.cm-line` divs
- **3 scraper modules fully independent** — one failure does not stop the others
- **PDF uses Puppeteer** (not WeasyPrint) — `build_pdf.js` launches headless Chromium to render HTML→PDF

---

## Login Flow

```
login_once.py runs once
      ↓
Auto-fills GitHub username + password from .env
      ↓
GitHub shows verification number in browser
      ↓
You tap Approve in GitHub mobile app
      ↓
GitHub redirects → neetcode.io  (Playwright detects instantly)
      ↓
session.json saved
      ↓
main.py loads session.json — no login prompt
      ↓
Press ENTER in terminal → scraping begins
```

---

## Requirements

### Python (managed by `setup.py`)

```
playwright==1.43.0
requests==2.31.0
tqdm==4.66.4
beautifulsoup4==4.12.3
markdown==3.6
python-dotenv==1.0.1
weasyprint==62.3
pyotp==2.9.0
```

> `weasyprint` and `reportlab` are only needed if you use `build_pdf.py` (the Python PDF builder).
> The primary PDF builder is `build_pdf.js` (Node.js) and does not require them.

### Node.js (managed by `npm install`)

```
puppeteer   ^24.x   ← headless Chromium for PDF rendering
marked      ^9.x    ← Markdown → HTML conversion
```

Install with:
```bash
npm install
```

### System requirements

- **Python 3.9+**
- **Node.js 18+** and **npm**
- NeetCode account with GitHub login
- GitHub mobile app (for one-time device approval)

---

## Files Never Committed to Git

```
.env                   ← GitHub credentials
session.json           ← Browser session cookies
NeetCode_150_Backup/   ← Scraped content (problem statements, solutions, submissions)
NeetCode_150_Book.pdf  ← Generated PDF
NeetCode_150_Links.txt ← Scraped problem links
node_modules/          ← Node.js packages
```

All of the above are in `.gitignore`. The scraped output and PDF are excluded intentionally — see the **Legal & Disclaimer** section below.

---

## Legal & Disclaimer

### What is safe to share

The **code** in this repository is safe to make public. It demonstrates browser automation (Playwright), DOM parsing (BeautifulSoup), file I/O, and PDF generation — all original work.

### What is not shared

The **generated output** — `NeetCode_150_Backup/` and `NeetCode_150_Book.pdf` — is intentionally excluded from this repository.

NeetCode is a business. Distributing a PDF of their curated 150 problems and solutions (even with credits) reproduces their intellectual property and could reduce traffic to their site. This is the standard that separates a *tool author* from a *content distributor*.

> **Publish the logic, not the content of website itself.**

This repository is a *scraper tool*. Users run it locally to generate their own personal backup. No copyrighted content is hosted here.

### Credits

All problem statements, solutions, and curated lists are the intellectual property of:

- **NeetCode** — [neetcode.io](https://neetcode.io) — original problem curation, video explanations, and written solutions
- **NeetCode GitHub** — [github.com/neetcode-gh/leetcode](https://github.com/neetcode-gh/leetcode) — official open-source solution repository
- **LeetCode** — [leetcode.com](https://leetcode.com) — original problem statements

### Disclaimer

This tool is for **educational and personal backup purposes only**. The author does not host or distribute any copyrighted content. Users are responsible for complying with the Terms of Service of NeetCode and LeetCode.

---

## Before Going Public — Checklist

| Action | Priority | Why |
|:---|:---|:---|
| `.env` and `session.json` in `.gitignore` | **Critical** | Contains your login credentials and session cookies |
| `NeetCode_150_Backup/` excluded | **Critical** | Contains scraped copyrighted content |
| `NeetCode_150_Book.pdf` excluded | **Recommended** | Distributing the PDF risks a DMCA takedown |
| `node_modules/` excluded | **Required** | Never commit Node dependencies |
| MIT License added | **Important** | Clarifies others can use your code but you are not liable for misuse |
