#!/usr/bin/env python3
"""Build both language versions of the CubeSandbox research page."""
import html
import os
import re

W = os.environ.get("CUBE_EKS_WORK", os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(W, "site")

CSS = open(os.path.join(W, "site.css")).read()


def esc(t):
    return html.escape(t, quote=False)


def _join_cites(t):
    pattern = r'(?:<sup class="cite">.*?</sup>)+'

    def repl(m):
        ids = re.findall(r'href="#src-(\d+)"', m.group(0))
        inner = ", ".join(f'<a href="#src-{n}" aria-label="source {n}">{n}</a>' for n in ids)
        return f'<sup class="cite">{inner}</sup>'
    return re.sub(pattern, repl, t)


def inline(t):
    t = esc(t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"\[(\d+)\]", r'<sup class="cite"><a href="#src-\1" aria-label="source \1">\1</a></sup>', t)
    return _join_cites(t)


def slug(t):
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


def parse(md_path):
    md = open(md_path).read()
    body_md, _, src_md = md.partition("\n## Sources\n")
    lines = body_md.split("\n")
    out, toc = [], []
    in_code, in_list = False, False
    for ln in lines:
        if ln.startswith("```"):
            if not in_code:
                out.append("<pre><code>")
                in_code = True
            else:
                out.append("</code></pre>")
                in_code = False
            continue
        if in_code:
            out.append(esc(ln))
            continue
        if in_list and not ln.startswith("- "):
            out.append("</ul>")
            in_list = False
        if ln.startswith("# "):
            continue
        if ln.startswith("## "):
            title = ln[3:].strip()
            sid = slug(title)
            toc.append((sid, title))
            out.append(f'<h2 id="{sid}">{inline(title)}</h2>')
        elif ln.startswith("- "):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{inline(ln[2:])}</li>")
        elif ln.startswith("!["):
            m = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", ln)
            out.append(("FIGURE", m.group(1), m.group(2)))
        elif ln.strip() == "":
            pass
        else:
            out.append(f"<p>{inline(ln)}</p>")
    if in_list:
        out.append("</ul>")
    if in_code:
        out.append("</code></pre>")

    srcs = []
    for ln in src_md.split("\n"):
        m = re.match(r"^\[(\d+)\]\s+(\S+)$", ln.strip())
        if m:
            n, url = m.group(1), m.group(2)
            short = url if len(url) <= 96 else url[:93] + "..."
            srcs.append(
                f'<li id="src-{n}"><span class="sid">[{n}]</span>'
                f'<a href="{url}">{esc(short)}</a></li>'
            )
    return out, toc, srcs


def render(lang, cfg, blocks, toc, srcs):
    body = []
    for b in blocks:
        if isinstance(b, tuple) and b and b[0] == "FIGURE":
            alt, src = b[1], b[2]
            body.append(
                '<figure><picture>'
                f'<source srcset="{cfg["diagram_dark"]}" media="(prefers-color-scheme: dark)">'
                f'<img src="{cfg["diagram_light"]}" alt="{esc(alt)}" width="2560" height="1520" loading="lazy" decoding="async">'
                f'</picture><figcaption>{esc(alt)}. {cfg["fig_link_text"]} '
                f'<a href="{cfg["diagram_page"]}">{cfg["fig_link_label"]}</a>{cfg["fig_link_tail"]}</figcaption></figure>'
            )
        else:
            body.append(b)
    tochtml = "".join(f'<li><a href="#{s}">{esc(t)}</a></li>' for s, t in toc)
    sw = " &middot; ".join(
        f'<a href="{href}" {"aria-current=\"page\"" if active else ""}>{esc(label)}</a>'
        for label, href, active in cfg["switch"]
    )
    page = f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(cfg["title"])}</title>
<meta name="description" content="{esc(cfg["description"])}">
<meta property="og:title" content="{esc(cfg["og_title"])}">
<meta property="og:description" content="{esc(cfg["description"])}">
<meta property="og:type" content="article">
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
<header class="page">
  <nav class="lang" aria-label="Language">{sw}</nav>
  <h1>{esc(cfg["h1"])}</h1>
  <p class="lede">{cfg["lede"]}</p>
</header>
<nav class="toc" aria-label="{cfg["toc_label"]}">
  <p>{cfg["toc_label"]}</p>
  <ol>{tochtml}</ol>
</nav>
<main>
{"".join(body)}
<h2 id="sources">{cfg["sources_label"]}</h2>
<ol class="sources">
{"".join(srcs)}
</ol>
</main>
<footer class="foot">
  <p>{cfg["footer"]}</p>
</footer>
</div>
</body>
</html>
"""
    path = os.path.join(SITE, cfg["out"])
    open(path, "w").write(page)
    print(f"{cfg['out']}: {len(page)} bytes | sections {len(toc)} | sources {len(srcs)}")


ID = dict(
    out="index.html",
    title="CubeSandbox di EKS Jakarta: sandbox microVM buat agent infra",
    description="Riset arsitektur dan dependency CubeSandbox untuk deployment di Amazon EKS Jakarta: bare metal vs PVM, ketersediaan komponen di ap-southeast-3, biaya, dan catatan risiko.",
    og_title="CubeSandbox di EKS Jakarta",
    h1="CubeSandbox di EKS Jakarta",
    lede='Sandbox microVM buat agent infrastructure. Riset arsitektur, dependency, biaya, dan risiko untuk deployment di <b>Amazon EKS ap-southeast-3</b>. Catatan riset, 17 November 2026.',
    toc_label="Isi",
    sources_label="Sources",
    diagram_light="diagram-light.png",
    diagram_dark="diagram-dark.png",
    diagram_page="diagram.html",
    fig_link_text="Versi interaktif:",
    fig_link_label="buka diagram",
    fig_link_tail=" (zoom, pencarian, tema).",
    footer="Disusun oleh Kai. Semua klaim teknis mengacu ke dokumentasi resmi CubeSandbox dan dokumentasi AWS; angka biaya diambil dari AWS Price List API untuk region ap-southeast-3 pada 17 November 2026, on-demand, belum termasuk pajak.",
    switch=[("Bahasa Indonesia", "./", True), ("English", "index-en.html", False)],
)

EN = dict(
    out="index-en.html",
    title="CubeSandbox on EKS Jakarta: microVM sandboxes for agent infrastructure",
    description="Architecture and dependency research for deploying CubeSandbox on Amazon EKS Jakarta: bare metal vs PVM, component availability in ap-southeast-3, cost, and known risks.",
    og_title="CubeSandbox on EKS Jakarta",
    h1="CubeSandbox on EKS Jakarta",
    lede='MicroVM sandboxes for agent infrastructure. Architecture, dependencies, cost, and risks for a deployment on <b>Amazon EKS ap-southeast-3</b>. Research note, 17 November 2026.',
    toc_label="Contents",
    sources_label="Sources",
    diagram_light="diagram-en-light.png",
    diagram_dark="diagram-en-dark.png",
    diagram_page="diagram-en.html",
    fig_link_text="Interactive version:",
    fig_link_label="open the diagram",
    fig_link_tail=" (zoom, search, themes).",
    footer="Written by Kai. Every technical claim references the official CubeSandbox documentation or AWS documentation; cost figures come from the AWS Price List API for the ap-southeast-3 Region, retrieved 17 November 2026, on-demand, excluding tax.",
    switch=[("Bahasa Indonesia", "index.html", False), ("English", "index-en.html", True)],
)

blocks_id, toc_id, srcs_id = parse(os.path.join(W, "article.md"))
blocks_en, toc_en, srcs_en = parse(os.path.join(W, "article-en.md"))
render("id", ID, blocks_id, toc_id, srcs_id)
render("en", EN, blocks_en, toc_en, srcs_en)
