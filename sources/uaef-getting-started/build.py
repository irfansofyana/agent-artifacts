#!/usr/bin/env python3
"""Build the published single-page site from content.md (single source of truth)."""
from __future__ import annotations

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "content.md"
OUT = ROOT / "site"

TITLE = "Getting started with UAEF"
DESC = ("A hands-on guide to the Universal Agent Evaluation Framework: install it, "
        "score an agent on deterministic metrics without an AWS account, and gate "
        "releases on regressions.")


def inline(text: str) -> str:
    """Inline markdown -> HTML. Code spans first, then links, then citations/bold."""
    stash: list[str] = []

    def keep(s: str) -> str:
        stash.append(s)
        return f"\x00{len(stash) - 1}\x00"

    text = re.sub(r"`([^`]+)`", lambda m: keep(f"<code>{html.escape(m.group(1))}</code>"), text)
    text = re.sub(
        r"\[([^\]]+)\]\(([^)\s]+)\)",
        lambda m: keep(f'<a href="{html.escape(m.group(2))}">{html.escape(m.group(1))}</a>'),
        text,
    )

    def cites(m: re.Match) -> str:
        nums = re.findall(r"\d+", m.group(0))
        links = "".join(
            f'<a class="cite" href="#src-{n}" title="Source {n}">{n}</a>' for n in nums
        )
        return keep(f'<sup class="cites">{links}</sup>')

    text = re.sub(r"(?:\[\d+\])+", cites, text)

    out = []
    for i, chunk in enumerate(re.split(r"(\*\*[^*]+\*\*)", text)):
        if i % 2:
            out.append(f"<strong>{chunk[2:-2]}</strong>")
        else:
            out.append(chunk)
    text = "".join(out)

    def restore(m: re.Match) -> str:
        return stash[int(m.group(1))]

    return re.sub(r"\x00(\d+)\x00", restore, text)


def split_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def slug(text: str) -> str:
    s = re.sub(r"<[^>]+>", "", text)
    s = re.sub(r"[^a-z0-9\s-]", "", s.lower())
    return re.sub(r"\s+", "-", s).strip("-")


def build_body(md: str) -> tuple[str, str, str, list[tuple[str, str]]]:
    lines = md.splitlines()
    # Hero: first H1 + the H2 immediately after it act as title and tagline.
    idx_h1 = next(i for i, l in enumerate(lines) if l.startswith("# "))
    hero_title = lines[idx_h1][2:].strip()
    idx_tag = next(i for i in range(idx_h1 + 1, len(lines)) if lines[i].startswith("## "))
    tagline = lines[idx_tag][3:].strip()

    body_lines = lines[idx_h1 + 1:idx_tag] + lines[idx_tag + 1:]
    html_parts: list[str] = []
    toc: list[tuple[str, str]] = []
    i = 0
    fact_mode = False
    table_idx = 0

    def close_list(stack: list[str]) -> None:
        while stack:
            html_parts.append(f"</{stack.pop()}>")

    while i < len(body_lines):
        line = body_lines[i]
        stripped = line.strip()

        # source list -------------------------------------------------------
        if re.fullmatch(r"\[\d+\] \S+", stripped):
            close_list([])
            items = []
            while i < len(body_lines) and re.fullmatch(r"\[\d+\] \S+", body_lines[i].strip()):
                m = re.fullmatch(r"\[(\d+)\] (\S+)", body_lines[i].strip())
                num, url = m.group(1), m.group(2)
                items.append(
                    f'<li id="src-{num}"><span class="src-num">{num}</span>'
                    f'<a href="{html.escape(url)}">{html.escape(url)}</a></li>'
                )
                i += 1
            html_parts.append('<ol class="source-list">' + "".join(items) + "</ol>")
            continue

        # fenced code -------------------------------------------------------
        if stripped.startswith("```"):
            lang = stripped[3:].strip() or "text"
            i += 1
            buf = []
            while i < len(body_lines) and not body_lines[i].strip().startswith("```"):
                buf.append(body_lines[i])
                i += 1
            i += 1
            code = html.escape("\n".join(buf))
            label = {"python": "Python", "bash": "Shell", "text": "Output"}.get(lang, lang)
            html_parts.append(
                '<div class="code">'
                f'<div class="code-head"><span class="code-lang">{label}</span>'
                '<button class="copy" type="button" data-copy>Copy</button></div>'
                f'<pre><code>{code}</code></pre></div>'
            )
            continue

        # table -------------------------------------------------------------
        if stripped.startswith("|") and i + 1 < len(body_lines) and re.match(
            r"^\|[\s:|-]+\|$", body_lines[i + 1].strip()
        ):
            head = split_row(stripped)
            i += 2
            rows = []
            while i < len(body_lines) and body_lines[i].strip().startswith("|"):
                rows.append(split_row(body_lines[i]))
                i += 1
            table_idx += 1
            hint_id = f"tbl-{table_idx}-hint"
            thead = "".join(f"<th scope=\"col\">{inline(c)}</th>" for c in head)
            tbody = "".join(
                "<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in rows
            )
            html_parts.append(
                '<div class="table-wrap" role="region" tabindex="0" '
                f'aria-labelledby="{hint_id}">'
                f'<p class="table-hint" id="{hint_id}" hidden>Scroll sideways to see every column.</p>'
                f'<table><thead><tr>{thead}</tr></thead><tbody>{tbody}</tbody></table></div>'
            )
            continue

        # headings ----------------------------------------------------------
        if stripped.startswith("### "):
            txt = stripped[4:]
            html_parts.append(f'<h3 id="{slug(txt)}">{inline(txt)}</h3>')
            i += 1
            continue
        if stripped.startswith("## "):
            txt = stripped[3:]
            sid = slug(txt)
            toc.append((sid, txt))
            html_parts.append(f'<h2 id="{sid}">{inline(txt)}</h2>')
            i += 1
            continue

        # blockquote / callout ----------------------------------------------
        if stripped.startswith(">"):
            buf = []
            while i < len(body_lines) and body_lines[i].strip().startswith(">"):
                buf.append(body_lines[i].strip().lstrip(">").strip())
                i += 1
            html_parts.append(f'<blockquote class="callout">{inline(" ".join(buf))}</blockquote>')
            continue

        # lists ---------------------------------------------------------------
        if re.match(r"^\s*[-*] ", line):
            tag = "ul"
            if fact_mode:
                tag = "ul class=\"facts\""
                fact_mode = False
            items = []
            while i < len(body_lines) and re.match(r"^\s*[-*] ", body_lines[i]):
                text = re.sub(r"^\s*[-*] ", "", body_lines[i])
                items.append("<li>" + inline(text) + "</li>")
                i += 1
            html_parts.append("<" + tag + ">" + "".join(items) + "</" + tag.split()[0] + ">")
            continue
        if re.match(r"^\s*\d+\. ", line):
            items = []
            while i < len(body_lines) and re.match(r"^\s*\d+\. ", body_lines[i]):
                text = re.sub(r"^\s*\d+\. ", "", body_lines[i])
                items.append("<li>" + inline(text) + "</li>")
                i += 1
            html_parts.append("<ol>" + "".join(items) + "</ol>")
            continue

        # blank line -----------------------------------------------------------
        if not stripped:
            i += 1
            continue

        # paragraph ------------------------------------------------------------
        if stripped == "**At a glance**":
            fact_mode = True
            html_parts.append('<p class="eyebrow">At a glance</p>')
            i += 1
            continue
        buf = []
        while i < len(body_lines) and body_lines[i].strip() and not re.match(
            r"^(#|\||```|>|\s*[-*] |\s*\d+\. |\[\d+\] )", body_lines[i]
        ):
            buf.append(body_lines[i].strip())
            i += 1
        html_parts.append(f"<p>{inline(' '.join(buf))}</p>")

    return hero_title, tagline, "\n".join(html_parts), toc


def main() -> None:
    md = SRC.read_text()
    hero_title, tagline, body, toc = build_body(md)
    nav = "".join(
        f'<li><a href="#{sid}">{html.escape(txt)}</a></li>' for sid, txt in toc
    )
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(TITLE)}</title>
<meta name="description" content="{html.escape(DESC)}">
<meta property="og:title" content="{html.escape(TITLE)}">
<meta property="og:description" content="{html.escape(DESC)}">
<meta property="og:type" content="article">
<meta name="color-scheme" content="light dark">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='7' fill='%233b5bdb'/%3E%3Cpath d='M9 22V10h3.1l3.9 6.4L19.9 10H23v12h-2.6v-7.3L16.8 21h-1.6l-3.6-6.3V22z' fill='white'/%3E%3C/svg%3E">
<link rel="stylesheet" href="assets/styles.css">
</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
<div class="progress" aria-hidden="true"><span id="progress-bar"></span></div>
<header class="hero">
  <p class="hero-kicker">AWS Labs · Apache 2.0 · v0.2.0</p>
  <h1>{html.escape(hero_title)}</h1>
  <p class="hero-tagline">{inline(tagline)}</p>
</header>
<div class="layout">
  <nav class="toc" aria-label="On this page">
    <p class="toc-title">On this page</p>
    <ol id="toc">{nav}</ol>
  </nav>
  <main id="main" class="content">
{body}
  </main>
</div>
<footer class="site-footer">
  <p>Built from the official UAEF documentation, repository source, and the AWS Machine Learning Blog post, with code paths run locally against UAEF 0.2.0.</p>
  <p class="fine">UAEF is an AWS Labs open-source project. This page is an independent getting-started guide.</p>
</footer>
<script src="assets/app.js"></script>
</body>
</html>
"""
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "index.html").write_text(page)
    print(f"wrote {OUT / 'index.html'} ({len(page)} bytes, {len(toc)} sections, {len(body.splitlines())} body lines)")


if __name__ == "__main__":
    main()
