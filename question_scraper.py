import re
import requests
from pathlib import Path
from bs4 import BeautifulSoup


async def scrape_question(page, p: dict, prob_dir: Path):
    slug = p["slug"]
    url  = f"https://neetcode.io/problems/{slug}/question"

    resp = requests.get(url, timeout=15)
    raw  = resp.text

    # ── Extract meta description content ──────────────────────────────────────
    match = re.search(r'<meta name="description" content="(.*?)">\s*<base', raw, re.DOTALL)
    if match:
        content = match.group(1)
        content = content.replace("&lt;", "<").replace("&gt;", ">")
        content = content.replace("&amp;", "&").replace("&quot;", '"')
        content = content.replace("&#39;", "'")
    else:
        content = ""

    # ── Split at first <details> tag ──────────────────────────────────────────
    details_match = re.search(r'<details', content)
    if details_match:
        problem_body = content[:details_match.start()].strip()
        details_raw  = content[details_match.start():]
    else:
        problem_body = content.strip()
        details_raw  = ""

    # ── Extract Leetcode line (first line of problem_body) ────────────────────
    body_lines = problem_body.splitlines()
    leetcode_line = ""
    if body_lines and body_lines[0].strip().lower().startswith("leetcode"):
        leetcode_line = body_lines[0].strip()
        # remove "Leetcode NNN. " prefix, keep just "NNN. ProblemName"
        leetcode_ref  = re.sub(r'^leetcode\s*', '', leetcode_line, flags=re.IGNORECASE).strip()
        problem_body  = "\n".join(body_lines[1:]).strip()
    else:
        leetcode_ref  = ""

    # ── Parse <details> blocks ────────────────────────────────────────────────
    sections = []  # list of (heading, body_text)
    HINT_RE     = re.compile(r'^hint\s+\d+$', re.IGNORECASE)
    
    def extract_company_tags_container(detail_soup):
        container = detail_soup.find("div", class_="company-tags-container")
        if not container:
            return None
        items = []
        for a in container.find_all("a"):
            span = a.find("span")
            count = span.get_text(strip=True) if span else ""
            if span:
                span.extract()
            name = a.get_text(strip=True)
            items.append(f"{name} ({count})" if count else name)
        return "\n".join(f"- {item}" for item in items)

    def extract_detail_body(detail_soup):
        tags_md = extract_company_tags_container(detail_soup)
        if tags_md:
            return tags_md

        # Company Tags with no div = skip entirely, no fallback
        summary = detail_soup.find("summary").get_text(strip=True)
        if summary.lower() == "company tags":
            return None

        parts = []
        for child in detail_soup.children:
            if child.name == "summary":
                continue
            if child.name == "p":
                for code in child.find_all("code"):
                    code.replace_with(f"`{code.get_text()}`")
                parts.append(child.get_text())
            elif child.name in ("ul", "ol"):
                for li in child.find_all("li"):
                    parts.append(f"- {li.get_text(strip=True)}")
            elif child.name == "pre":
                parts.append(f"```\n{child.get_text()}\n```")
        return "\n\n".join(p.strip() for p in parts if p.strip())
    
    soup = BeautifulSoup(details_raw, "html.parser")
    for detail in soup.find_all("details"):
        summary_tag = detail.find("summary")
        if not summary_tag:
            continue
        heading = summary_tag.get_text(strip=True)
        body_md = extract_detail_body(detail)
        if body_md is not None:
            sections.append((heading, body_md))


    # ── Helpers ───────────────────────────────────────────────────────────────
    def clean_body(text: str) -> str:
        lines = [l.strip() for l in text.splitlines()]
        out, prev_blank = [], False
        for l in lines:
            if l == "":
                if not prev_blank and out:
                    out.append("")
                prev_blank = True
            else:
                out.append(l)
                prev_blank = False
        return "\n".join(out).strip()


    # ── Build markdown ────────────────────────────────────────────────────────
    md  = f"# {p['name']}\n\n"
    md += f"**Difficulty:** {_get_difficulty(raw)}\n\n"
    md += f"**Acceptance Rate:** {_get_acceptance(raw)}\n\n"
    if leetcode_ref:
        md += f"**Leetcode:** {leetcode_ref}\n\n"
    md += f"**Link:** {url}\n\n"
    md += f"## Problem Statement\n\n{clean_body(problem_body)}\n\n"

    hint_md = ""
    prob_md = ""

    for heading, body_md in sections:
        if body_md is None:
            continue
        section = f"### {heading}\n\n{body_md}\n\n"
        if HINT_RE.match(heading):
            hint_md += section
        else:
            prob_md += section

    # append prob_md to the main md string
    md += prob_md

    (prob_dir / "Problem_Statement.md").write_text(md.strip(), encoding="utf-8")
    print(f"  ✅ Problem_Statement.md saved")
    if hint_md:
        (prob_dir / "Hint_page.md").write_text(hint_md.strip(), encoding="utf-8")
        print(f"  HINT FOUND")
        print(f"  ✅ Hint_page.md saved")
    

def _get_difficulty(html: str) -> str:
    m = re.search(r'difficulty-pill[^>]*>\s*(Easy|Medium|Hard)\s*<', html)
    return m.group(1) if m else "Unknown"


def _get_acceptance(html: str) -> str:
    m = re.search(r'acceptance-value[^>]*>([\d.]+%)<', html)
    return m.group(1) if m else "N/A"
