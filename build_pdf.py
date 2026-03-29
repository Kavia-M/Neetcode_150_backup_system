"""
build_pdf.py — NeetCode 150 PDF Book Generator
Requires: pip install weasyprint markdown requests
"""

import json
import re
import base64
import requests
from pathlib import Path
from io import BytesIO
import markdown
from weasyprint import HTML, CSS

# ─── Paths ────────────────────────────────────────────────────────────────────
BACKUP  = Path("NeetCode_150_Backup")
META    = BACKUP / "metadata.json"
OUT_PDF = Path("NeetCode_150_Book.pdf")

# ─── Section groupings — parsed from topicsAndProblems.md ───────────────────
TOPICS_FILE = Path("topicsAndProblems.md")

def parse_sections(meta: dict) -> list:
    """Parse topicsAndProblems.md → list of (section_name, [problem_nums])"""
    # Build name→num lookup from metadata (lowercase, stripped)
    name_to_num = {}
    for p in meta["problems"]:
        key = p["name"].lower().strip()
        name_to_num[key] = p["num"]

    sections = []
    current_section = None
    current_problems = []

    for line in TOPICS_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("## "):
            if current_section:
                sections.append((current_section, current_problems))
            # e.g. "## 1. Arrays & Hashing" → "Arrays & Hashing"
            current_section = re.sub(r'^##\s+\d+\.\s*', '', line).strip()
            current_problems = []
        elif re.match(r'^\d+\.\s+', line):
            prob_name = re.sub(r'^\d+\.\s+', '', line).strip()
            key = prob_name.lower().strip()
            # fuzzy match — try exact first, then partial
            num = name_to_num.get(key)
            if num is None:
                for k, v in name_to_num.items():
                    if key in k or k in key:
                        num = v
                        break
            if num:
                current_problems.append(num)

    if current_section:
        sections.append((current_section, current_problems))

    return sections

# ─── CSS ──────────────────────────────────────────────────────────────────────
CSS_STYLE = """
@page {
    size: A4;
    margin-top: 2.2cm;
    margin-bottom: 2.2cm;
    margin-left: 3cm;
    margin-right: 2cm;
    @bottom-center {
        content: counter(page);
        font-family: Georgia, serif;
        font-size: 9pt;
        color: #444;
    }
}

body {
    font-family: Georgia, "Times New Roman", serif;
    font-size: 10.5pt;
    line-height: 1.55;
    color: #111;
}

h1 { font-size: 17pt; margin-top: 0.6em; margin-bottom: 0.4em; page-break-after: avoid; border-bottom: 1.5px solid #333; padding-bottom: 4px; }
h2 { font-size: 13.5pt; margin-top: 1em; margin-bottom: 0.3em; page-break-after: avoid; }
h3 { font-size: 11.5pt; margin-top: 0.9em; margin-bottom: 0.2em; page-break-after: avoid; }
h4 { font-size: 10.5pt; margin-top: 0.8em; margin-bottom: 0.2em; page-break-after: avoid; font-style: italic; }
h5 { font-size: 10pt;   margin-top: 0.7em; margin-bottom: 0.2em; page-break-after: avoid; }

p  { margin: 0.3em 0 0.5em 0; orphans: 3; widows: 3; }
li { margin: 0.15em 0; orphans: 3; widows: 3; }
ul, ol { margin: 0.3em 0 0.5em 1.4em; }

pre {
    font-family: "Courier New", Courier, monospace;
    font-size: 8.8pt;
    line-height: 1.4;
    background: #f5f5f5;
    border-left: 3px solid #999;
    padding: 0.6em 0.8em;
    margin: 0.7em 0 0.7em 0;
    white-space: pre;
    overflow-wrap: normal;
    page-break-inside: auto;
}

code {
    font-family: "Courier New", Courier, monospace;
    font-size: 8.8pt;
    background: #f0f0f0;
    padding: 1px 3px;
}

pre code {
    background: none;
    padding: 0;
    font-size: inherit;
}

img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 0.6em auto;
}

blockquote {
    border-left: 3px solid #aaa;
    margin-left: 1em;
    padding-left: 0.8em;
    color: #444;
    font-style: italic;
}

/* Section separator page */
.section-page {
    page-break-before: always;
    page-break-after: always;
    display: flex;
    flex-direction: column;
    justify-content: center;
    min-height: 24cm;
    padding: 3cm 1cm;
}
.section-page h1 {
    font-size: 22pt;
    border-bottom: 2px solid #111;
    padding-bottom: 8px;
    margin-bottom: 1em;
}
.section-page ol {
    font-size: 11pt;
    line-height: 1.8;
}

/* Cover page */
.cover-page {
    page-break-after: always;
    text-align: center;
    padding-top: 6cm;
}
.cover-page h1 { font-size: 26pt; border: none; }
.cover-page p  { font-size: 11pt; color: #555; margin-top: 0.5em; }

/* Credits page */
.credits-page {
    page-break-after: always;
    padding-top: 4cm;
}

/* Problem/solution page breaks */
.problem-block  { page-break-after: always; }
.solution-block { page-break-after: always; }

/* Hint starts on fresh page */
.hint-section { page-break-before: always; }
"""

# ─── Helpers ──────────────────────────────────────────────────────────────────

def embed_images(md_text: str) -> str:
    """Download images and embed as base64 data URIs."""
    def replace_img(m):
        url = m.group(1)
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                ct = r.headers.get("Content-Type", "image/png").split(";")[0]
                b64 = base64.b64encode(r.content).decode()
                return f'<img src="data:{ct};base64,{b64}" alt="diagram">'
        except Exception:
            pass
        return f'<img src="{url}" alt="diagram">'
    # Replace markdown images
    md_text = re.sub(r'!\[.*?\]\((https?://[^)]+)\)', replace_img, md_text)
    return md_text

def normalize_code_fences(md_text: str) -> str:
    """Strip language hints from fenced code blocks — treat all as plain code."""
    return re.sub(r'^```\w+', '```', md_text, flags=re.MULTILINE)

def inject_hint_breaks(html: str) -> str:
    """Wrap Hint sections in hint-section div for page-break-before."""
    return re.sub(
        r'(<h3[^>]*>)(Hint\s+\d+)(</h3>)',
        r'<div class="hint-section">\1\2\3',
        html
    )

def md_to_html(md_text: str) -> str:
    md_text = normalize_code_fences(md_text)
    md_text = embed_images(md_text)
    html = markdown.markdown(
        md_text,
        extensions=["fenced_code", "tables", "nl2br"]
    )
    html = inject_hint_breaks(html)
    return html

def cover_page_html() -> str:
    return """
    <div class="cover-page">
        <h1>NeetCode 150</h1>
        <h2 style="border:none; font-size:15pt; font-weight:normal;">Questions &amp; Solutions</h2>
        <p style="margin-top:3em; font-size:10pt; color:#777;">Java Solutions &nbsp;|&nbsp; All 150 Problems</p>
    </div>
    """

def credits_page_html() -> str:
    return """
    <div class="credits-page">
        <h2>Credits &amp; Disclaimer</h2>
        <p><strong>Source:</strong> All problems and solutions are sourced from
        <a href="https://neetcode.io/practice/neetcode150">https://neetcode.io/practice/neetcode150</a></p>
        <p><strong>Author:</strong> NeetCode</p>
        <br>
        <h3>Disclaimer</h3>
        <p>This document was generated programmatically using a custom web scraper
        built with Python and Playwright, with assistance from AI tools (Amazon Q).
        It is intended solely for personal offline study and reference.</p>
        <p>All content — problem statements, solutions, explanations, and code —
        belongs to NeetCode. No content has been modified, summarized, or
        generated by AI. The scraper only collected and formatted existing content.</p>
        <p>This PDF is not for redistribution or commercial use.</p>
    </div>
    """

def section_page_html(section_name: str, problems: list, num_map: dict) -> str:
    items = ""
    for n in problems:
        if n in num_map:
            items += f"<li>{num_map[n]['name']}</li>\n"
    return f"""
    <div class="section-page">
        <h1>{section_name}</h1>
        <ol>
        {items}
        </ol>
    </div>
    """

# ─── Main ─────────────────────────────────────────────────────────────────────

def build():
    meta = json.loads(META.read_text(encoding="utf-8"))
    num_map = {p["num"]: p for p in meta["problems"]}
    sections = parse_sections(meta)

    html_parts = []

    # Cover
    html_parts.append(cover_page_html())

    # Credits
    html_parts.append(credits_page_html())

    # Sections
    for section_name, nums in sections:
        # Section separator page
        html_parts.append(section_page_html(section_name, nums, num_map))

        for n in nums:
            if n not in num_map:
                continue
            p = num_map[n]
            folder = BACKUP / p["folder"]

            # Problem Statement
            ps_file = folder / "Problem_Statement.md"
            if ps_file.exists():
                ps_html = md_to_html(ps_file.read_text(encoding="utf-8"))
                html_parts.append(f'<div class="problem-block">{ps_html}</div>')

            # Solution
            sol_file = folder / "Solution.md"
            if not sol_file.exists():
                sol_file = folder / "Solution.txt"
            if sol_file.exists():
                sol_html = md_to_html(sol_file.read_text(encoding="utf-8"))
                html_parts.append(f'<div class="solution-block">{sol_html}</div>')

    full_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
</head>
<body>
{''.join(html_parts)}
</body>
</html>"""

    print("Rendering PDF... (this may take a few minutes)")
    HTML(string=full_html, base_url=".").write_pdf(
        str(OUT_PDF),
        stylesheets=[CSS(string=CSS_STYLE)]
    )
    print(f"✅ PDF saved: {OUT_PDF}")

if __name__ == "__main__":
    build()
