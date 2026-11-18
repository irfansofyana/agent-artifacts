#!/usr/bin/env python3
"""Build every page of the CubeSandbox on EKS Jakarta artifact.

Emits the bilingual pair of documents (research + options, Indonesian and
English) plus the shared stylesheet and self-hosted font into the build
directory, and stages the Archify diagram documents and their PNG captures when
they are present.

Output directory: $CUBE_EKS_WORK/build by default (CUBE_EKS_BUILD overrides it).
``CUBE_EKS_WORK`` defaults to this file's directory, so no absolute machine path
is needed. The font is read from the artifact repo's own assets/ (../../assets
relative to this file, overridable with CUBE_EKS_FONT); the diagrams are read
from ./diagram (overridable with CUBE_EKS_DIAGRAM_DIR) and are copied verbatim
because they are Archify output, i.e. the diagram itself, not page chrome.
"""
import html
import os
import re
import shutil

W = os.environ.get("CUBE_EKS_WORK", os.path.dirname(os.path.abspath(__file__)))
OUT = os.environ.get("CUBE_EKS_BUILD", os.path.join(W, "build"))
ASSETS = os.path.join(OUT, "assets")
FONT_SRC = os.environ.get(
    "CUBE_EKS_FONT",
    os.path.normpath(os.path.join(W, os.pardir, os.pardir, "assets", "fonts", "InterVariable-latin.woff2")),
)
DIAGRAM_DIR = os.environ.get("CUBE_EKS_DIAGRAM_DIR", os.path.join(W, "diagram"))

# Only the shell needs these; content stays in the markdown sources.
SLUG = "frosty-aurora-2jqj"
REGISTRY = "https://artifacts.irfansp.dev/"

CSS_FILE = os.path.join(W, "site.css")

# build name -> candidate source names inside CUBE_EKS_DIAGRAM_DIR
# The Archify exports are the diagram itself, so they keep their own bytes and
# are published as *.html viewers; the Scandinavian host pages wrap them.
DIAGRAM_FILES = {
    "diagram-view.html": ("diagram.html", "cubesandbox-eks.html"),
    "diagram-view-en.html": ("diagram-en.html", "cubesandbox-eks-en.html"),
    "diagram-light.png": ("diagram-light.png",),
    "diagram-dark.png": ("diagram-dark.png",),
    "diagram-en-light.png": ("diagram-en-light.png",),
    "diagram-en-dark.png": ("diagram-en-dark.png",),
}


def esc(t):
    return html.escape(t, quote=False)


def _join_cites(t):
    def repl(m):
        ids = re.findall(r'href="#src-(\d+)"', m.group(0))
        inner = ", ".join(f'<a href="#src-{n}" aria-label="source {n}">{n}</a>' for n in ids)
        return f'<sup class="cite">{inner}</sup>'
    return re.sub(r'(?:<sup class="cite">.*?</sup>)+', repl, t)


def inline(t):
    t = esc(t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"\[(\d+)\]", r'<sup class="cite"><a href="#src-\1" aria-label="source \1">\1</a></sup>', t)
    return _join_cites(t)


def slug(t):
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


def parse(md_path):
    md = open(md_path, encoding="utf-8").read()
    body_md, _, src_md = md.partition("\n## Sources\n")
    lines = body_md.split("\n")
    out, toc = [], []
    in_code = in_list = False
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("```"):
            if not in_code:
                out.append("<pre><code>")
                in_code = True
            else:
                out.append("</code></pre>")
                in_code = False
            i += 1
            continue
        if in_code:
            out.append(esc(ln)); i += 1; continue
        if in_list and not ln.startswith("- "):
            out.append("</ul>"); in_list = False
        # table block
        if ln.strip().startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|$", lines[i + 1].strip()):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not re.match(r"^[\s:|-]+$", "".join(cells)):
                    rows.append(cells)
                i += 1
            head, body = rows[0], rows[1:]
            thead = "<tr>" + "".join(f"<th>{inline(c)}</th>" for c in head) + "</tr>"
            tbody = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in body)
            out.append(
                '<div class="table-wrap" tabindex="0" role="region" aria-label="Tabel">'
                f"<table><thead>{thead}</thead><tbody>{tbody}</tbody></table></div>"
                '<p class="tablehint" hidden>Geser ke samping untuk melihat seluruh tabel.</p>'
            )
            continue
        if ln.startswith("# "):
            i += 1; continue
        if ln.startswith("## "):
            title = ln[3:].strip(); sid = slug(title)
            toc.append((sid, title)); out.append(f'<h2 id="{sid}">{inline(title)}</h2>')
        elif ln.startswith("- "):
            if not in_list:
                out.append("<ul>"); in_list = True
            out.append(f"<li>{inline(ln[2:])}</li>")
        elif ln.startswith("!["):
            m = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", ln)
            out.append(("FIGURE", m.group(1), m.group(2)))
        elif ln.strip() == "":
            pass
        else:
            out.append(f"<p>{inline(ln)}</p>")
        i += 1
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
            srcs.append(f'<li id="src-{n}"><span class="sid">[{n}]</span><a href="{url}">{esc(short)}</a></li>')
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
                f'</picture><figcaption>{esc(alt)}. {cfg["fig_link_text"]} <a href="{cfg["diagram_page"]}">{cfg["fig_link_label"]}</a>{cfg["fig_link_tail"]}</figcaption></figure>'
            )
        else:
            body.append(b)

    if cfg.get("viewer"):
        body = [
            '<div class="viewer">'
            f'<iframe src="{cfg["viewer"]}" title="{esc(cfg["viewer_title"])}" loading="lazy"></iframe>'
            "</div>"
        ]
        toc, srcs = [], []

    toc_nav = ""
    if toc:
        tochtml = "".join(f'<li><a href="#{s}">{esc(t)}</a></li>' for s, t in toc)
        toc_nav = (f'  <nav class="toc" aria-label="{esc(cfg["toc_label"])}">\n'
                   f'    <p>{esc(cfg["toc_label"])}</p>\n'
                   f"    <ol>{tochtml}</ol>\n"
                   f"  </nav>\n")

    sources = ""
    if srcs:
        sources = (f'<h2 id="sources">{esc(cfg["sources_label"])}</h2>\n'
                   f'<ol class="sources">\n{"".join(srcs)}\n</ol>\n')

    foot_note = f'<p>{cfg["footer"]}</p>\n    ' if cfg.get("footer") else ""

    def link(label, href, cur):
        attr = ' aria-current="page"' if cur else ""
        return f'<a href="{href}"{attr}>{esc(label)}</a>'

    docs = "\n      ".join(link(*t) for t in cfg["docs"]) + "\n      " + link(cfg["registry_label"], REGISTRY, False)
    langs = "\n      ".join(link(*t) for t in cfg["switch"])

    page = f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(cfg["title"])}</title>
<meta name="description" content="{esc(cfg["description"])}">
<meta property="og:title" content="{esc(cfg["og_title"])}">
<meta property="og:description" content="{esc(cfg["description"])}">
<meta property="og:type" content="{'article' if not cfg.get('viewer') else 'website'}">
<link rel="icon" href="data:,">
<link rel="stylesheet" href="assets/page.css">
</head>
<body>
<a class="skip" href="#main">{esc(cfg["skip"])}</a>
<header class="masthead">
  <div class="page">
    <p class="wordmark">Irfan's AI agents</p>
    <nav class="shellnav" aria-label="{esc(cfg["docs_label"])}">
      {docs}
    </nav>
    <nav class="shellnav langnav" aria-label="{esc(cfg["lang_label"])}">
      {langs}
    </nav>
  </div>
</header>
<div class="page">
  <header class="hero">
    <p class="eyebrow">{esc(cfg["eyebrow"])}</p>
    <h1>{esc(cfg["h1"])}</h1>
    <p class="lede">{cfg["lede"]}</p>
  </header>
{toc_nav}  <main id="main">
{"".join(body)}
{sources}  </main>
</div>
<footer class="foot">
  <div class="page">
    {foot_note}<p class="footmeta">{esc(SLUG)} &middot; <a href="{REGISTRY}">artifacts.irfansp.dev</a></p>
  </div>
</footer>
<script>
document.querySelectorAll('.table-wrap').forEach(function(w){{
  var hint = w.nextElementSibling;
  function check(){{ if (hint && hint.classList.contains('tablehint')) hint.hidden = w.scrollWidth <= w.clientWidth + 2; }}
  check(); window.addEventListener('resize', check);
}});
</script>
</body>
</html>
"""
    path = os.path.join(OUT, cfg["out"])
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(page)
    print(f"{cfg['out']}: {len(page)} B | sections {len(toc)} | sources {len(srcs)}")


RESEARCH = dict(
    docs=[("Riset CubeSandbox", "index.html", True), ("Opsi sandbox", "sandbox-options.html", False)],
    switch=[("Bahasa Indonesia", "index.html", True), ("English", "index-en.html", False)],
    docs_label="Navigasi", lang_label="Bahasa", registry_label="Registry", skip="Lewati ke konten",
)
RESEARCH_EN = dict(
    docs=[("CubeSandbox research", "index-en.html", True), ("Sandbox options", "sandbox-options-en.html", False)],
    switch=[("Bahasa Indonesia", "index.html", False), ("English", "index-en.html", True)],
    docs_label="Navigation", lang_label="Language", registry_label="Registry", skip="Skip to content",
)
OPTIONS = dict(
    diagram_light="diagram-light.png", diagram_dark="diagram-dark.png", diagram_page="diagram.html",
    fig_link_text="", fig_link_label="", fig_link_tail="",
    docs=[("Riset CubeSandbox", "index.html", False), ("Opsi sandbox", "sandbox-options.html", True)],
    switch=[("Bahasa Indonesia", "sandbox-options.html", True), ("English", "sandbox-options-en.html", False)],
    docs_label="Navigasi", lang_label="Bahasa", registry_label="Registry", skip="Lewati ke konten",
)
OPTIONS_EN = dict(
    diagram_light="diagram-en-light.png", diagram_dark="diagram-en-dark.png", diagram_page="diagram-en.html",
    fig_link_text="", fig_link_label="", fig_link_tail="",
    docs=[("CubeSandbox research", "index-en.html", False), ("Sandbox options", "sandbox-options-en.html", True)],
    switch=[("Bahasa Indonesia", "sandbox-options.html", False), ("English", "sandbox-options-en.html", True)],
    docs_label="Navigation", lang_label="Language", registry_label="Registry", skip="Skip to content",
)

ID_RESEARCH = dict(
    out="index.html",
    title="CubeSandbox di EKS Jakarta: sandbox microVM buat agent infra",
    description="Riset arsitektur dan dependency CubeSandbox untuk deployment di Amazon EKS Jakarta: bare metal vs PVM, ketersediaan komponen di ap-southeast-3, biaya, dan catatan risiko.",
    og_title="CubeSandbox di EKS Jakarta",
    h1="CubeSandbox di EKS Jakarta",
    eyebrow="Catatan riset",
    lede='Sandbox microVM buat agent infrastructure. Riset arsitektur, dependency, biaya, dan risiko untuk deployment di <b>Amazon EKS ap-southeast-3</b>. Catatan riset, 17 November 2026.',
    toc_label="Isi", sources_label="Sources",
    diagram_light="diagram-light.png", diagram_dark="diagram-dark.png", diagram_page="diagram.html",
    fig_link_text="Versi interaktif:", fig_link_label="buka diagram", fig_link_tail=" (zoom, pencarian, tema).",
    footer="Disusun oleh Kai. Semua klaim teknis mengacu ke dokumentasi resmi CubeSandbox dan dokumentasi AWS; angka biaya diambil dari AWS Price List API untuk region ap-southeast-3 pada 17 November 2026, on-demand, belum termasuk pajak.",
    **RESEARCH,
)
EN_RESEARCH = dict(
    out="index-en.html",
    title="CubeSandbox on EKS Jakarta: microVM sandboxes for agent infrastructure",
    description="Architecture and dependency research for deploying CubeSandbox on Amazon EKS Jakarta: bare metal vs PVM, component availability in ap-southeast-3, cost, and known risks.",
    og_title="CubeSandbox on EKS Jakarta",
    h1="CubeSandbox on EKS Jakarta",
    eyebrow="Research note",
    lede='MicroVM sandboxes for agent infrastructure. Architecture, dependencies, cost, and risks for a deployment on <b>Amazon EKS ap-southeast-3</b>. Research note, 17 November 2026.',
    toc_label="Contents", sources_label="Sources",
    diagram_light="diagram-en-light.png", diagram_dark="diagram-en-dark.png", diagram_page="diagram-en.html",
    fig_link_text="Interactive version:", fig_link_label="open the diagram", fig_link_tail=" (zoom, search, themes).",
    footer="Written by Kai. Every technical claim references the official CubeSandbox documentation or AWS documentation; cost figures come from the AWS Price List API for the ap-southeast-3 Region, retrieved 17 November 2026, on-demand, excluding tax.",
    **RESEARCH_EN,
)
ID_OPTIONS = dict(
    out="sandbox-options.html",
    title="Opsi sandbox untuk AI agent di AWS Jakarta: CubeSandbox vs E2B Embed vs Nitro Sandboxes",
    description="Tiga opsi sandbox untuk WeKnora dan agent lain di AWS Jakarta, lengkap dengan komponen yang dibutuhkan, estimasi biaya bulanan, dan verdict perubahan kode WeKnora.",
    og_title="Opsi sandbox untuk AI agent di AWS Jakarta",
    h1="Sandbox untuk AI agent di AWS Jakarta",
    eyebrow="Dokumen keputusan",
    lede='Tiga opsi untuk WeKnora dan agent lain: <b>CubeSandbox</b>, <b>E2B Embed</b>, dan <b>AWS Nitro Sandboxes</b>. Komponen yang dibutuhkan, estimasi biaya di region Jakarta, dan mana yang perlu patch kode WeKnora. Dokumen keputusan, 17 November 2026.',
    toc_label="Isi", sources_label="Sources",
    footer="Disusun oleh Kai. Semua komponen berada di region ap-southeast-3 (Jakarta). Angka biaya dari AWS Price List API region tersebut, on-demand, di luar pajak, data transfer keluar, dan biaya LLM.",
    **OPTIONS,
)
EN_OPTIONS = dict(
    out="sandbox-options-en.html",
    title="Sandbox options for AI agents on AWS Jakarta: CubeSandbox vs E2B Embed vs Nitro Sandboxes",
    description="Three sandbox options for WeKnora and other agents on AWS Jakarta with the components each needs, monthly cost estimates, and which one requires WeKnora code changes.",
    og_title="Sandbox options for AI agents on AWS Jakarta",
    h1="Sandboxes for AI agents on AWS Jakarta",
    eyebrow="Decision document",
    lede='Three options for WeKnora and other agents: <b>CubeSandbox</b>, <b>E2B Embed</b>, and <b>AWS Nitro Sandboxes</b>. What each needs, what it costs in the Jakarta Region, and which one requires patching WeKnora. Decision document, 17 November 2026.',
    toc_label="Contents", sources_label="Sources",
    footer="Written by Kai. Every component runs in ap-southeast-3 (Jakarta). Cost figures come from the AWS Price List API for that Region, on-demand, excluding tax, data transfer out, and LLM spend.",
    **OPTIONS_EN,
)

PAGES = [
    ("article.md", "id", ID_RESEARCH),
    ("article-en.md", "en", EN_RESEARCH),
    ("article-options.md", "id", ID_OPTIONS),
    ("article-options-en.md", "en", EN_OPTIONS),
]

# The Archify diagram documents get a Scandinavian host page so the artifact
# reads as one system; the viewer itself is embedded unchanged (its colour is
# diagram content, and every viewer control stays reachable).
DIAGRAM_ID = dict(
    out="diagram.html",
    viewer="diagram-view.html",
    viewer_title="CubeSandbox di Amazon EKS Jakarta (ap-southeast-3) — diagram interaktif",
    title="CubeSandbox di Amazon EKS Jakarta (ap-southeast-3): diagram",
    description="Diagram arsitektur CubeSandbox di Amazon EKS Jakarta (ap-southeast-3), dapat di-zoom, dicari, dan diganti tema.",
    og_title="CubeSandbox di Amazon EKS Jakarta (ap-southeast-3)",
    h1="CubeSandbox di Amazon EKS Jakarta (ap-southeast-3)",
    eyebrow="Diagram",
    lede="Arsitektur CubeSandbox di EKS Jakarta.",
    docs=[("Riset CubeSandbox", "index.html", False), ("Opsi sandbox", "sandbox-options.html", False)],
    switch=[("Bahasa Indonesia", "diagram.html", True), ("English", "diagram-en.html", False)],
    docs_label="Navigasi", lang_label="Bahasa", registry_label="Registry", skip="Lewati ke konten",
)
DIAGRAM_EN = dict(
    out="diagram-en.html",
    viewer="diagram-view-en.html",
    viewer_title="CubeSandbox on Amazon EKS Jakarta (ap-southeast-3) — interactive diagram",
    title="CubeSandbox on Amazon EKS Jakarta (ap-southeast-3): diagram",
    description="CubeSandbox architecture diagram for Amazon EKS Jakarta (ap-southeast-3), with zoom, search, and themes.",
    og_title="CubeSandbox on Amazon EKS Jakarta (ap-southeast-3)",
    h1="CubeSandbox on Amazon EKS Jakarta (ap-southeast-3)",
    eyebrow="Diagram",
    lede="CubeSandbox architecture on EKS Jakarta.",
    docs=[("CubeSandbox research", "index-en.html", False), ("Sandbox options", "sandbox-options-en.html", False)],
    switch=[("Bahasa Indonesia", "diagram.html", False), ("English", "diagram-en.html", True)],
    docs_label="Navigation", lang_label="Language", registry_label="Registry", skip="Skip to content",
)
VIEWERS = [("id", DIAGRAM_ID), ("en", DIAGRAM_EN)]


def stage_shared():
    os.makedirs(os.path.join(ASSETS, "fonts"), exist_ok=True)
    with open(CSS_FILE, encoding="utf-8") as fh:
        css = fh.read()
    with open(os.path.join(ASSETS, "page.css"), "w", encoding="utf-8") as fh:
        fh.write(css)
    if os.path.exists(FONT_SRC):
        shutil.copyfile(FONT_SRC, os.path.join(ASSETS, "fonts", "InterVariable-latin.woff2"))
        print(f"assets/page.css + assets/fonts/InterVariable-latin.woff2 ({os.path.getsize(FONT_SRC)} B)")
    else:
        print(f"WARNING: font not found at {FONT_SRC}; page.css still references assets/fonts/InterVariable-latin.woff2")


def stage_diagrams():
    if not os.path.isdir(DIAGRAM_DIR):
        print(f"diagrams: no {DIAGRAM_DIR} directory; skipped (figure links will 404 in the build)")
        return
    for dest, candidates in DIAGRAM_FILES.items():
        for name in candidates:
            src = os.path.join(DIAGRAM_DIR, name)
            if os.path.exists(src):
                shutil.copyfile(src, os.path.join(OUT, dest))
                print(f"{dest}: {os.path.getsize(src)} B (from {name})")
                break
        else:
            print(f"diagrams: no source for {dest} in {DIAGRAM_DIR}")


def main():
    os.makedirs(OUT, exist_ok=True)
    stage_shared()
    stage_diagrams()
    for md, lang, cfg in PAGES:
        blocks, toc, srcs = parse(os.path.join(W, md))
        render(lang, cfg, blocks, toc, srcs)
    for lang, cfg in VIEWERS:
        render(lang, cfg, [], [], [])
    print(f"build output: {OUT}")


if __name__ == "__main__":
    main()
