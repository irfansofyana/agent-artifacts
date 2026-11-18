#!/usr/bin/env python3
"""Build the here.now article page from the verified markdown source."""
import html
import os
import re

W = os.environ.get("CUBE_EKS_WORK", os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(W, "site")
MD = os.path.join(W, "article.md")

CSS = """
:root{
  color-scheme: light;
  --bg:#fafaf8; --surface:#ffffff; --surface-2:#f4f4f0;
  --border:#d3d3cb; --rule:#e7e7e0; --fg:#15171b; --fg-2:#454b54;
  --accent:#0f6f5c; --accent-soft:#e8f3f0; --code-bg:#f2f2ee;
  --measure:72ch;
  --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
  --mono:ui-monospace,SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace;
}
@media (prefers-color-scheme: dark){
  :root{
    color-scheme: dark;
    --bg:#0e1116; --surface:#161b22; --surface-2:#1b222b;
    --border:#313a47; --rule:#242c36; --fg:#e8ebf0; --fg-2:#aab3bf;
    --accent:#57d2b4; --accent-soft:#12312b; --code-bg:#171d26;
  }
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{
  margin:0; background:var(--bg); color:var(--fg);
  font-family:var(--sans); font-size:17px; line-height:1.65;
  font-kerning:normal;
}
.wrap{max-width:860px; margin:0 auto; padding:0 20px}
header.page{padding:56px 0 28px; border-bottom:1px solid var(--rule)}
h1{font-size:clamp(1.7rem,1.2rem + 2vw,2.4rem); line-height:1.2; letter-spacing:-.015em; margin:0 0 .5rem}
.lede{color:var(--fg-2); font-size:1rem; margin:0}
.lede b{color:var(--fg); font-weight:600}
nav.toc{margin:32px 0 8px; padding:18px 20px; background:var(--surface); border:1px solid var(--border); border-radius:10px}
nav.toc p{margin:0 0 10px; font-size:.78rem; text-transform:uppercase; letter-spacing:.08em; color:var(--fg-2); font-weight:600}
nav.toc ol{margin:0; padding-left:1.2rem; columns:2; column-gap:32px}
nav.toc li{margin:.25rem 0; font-size:.95rem}
nav.toc a{color:var(--fg); text-decoration:none; border-bottom:1px solid transparent}
nav.toc a:hover{border-bottom-color:var(--accent)}
main{padding:8px 0 40px}
h2{font-size:1.35rem; line-height:1.3; letter-spacing:-.01em; margin:2.6rem 0 .9rem; padding-top:.4rem}
h2:first-of-type{margin-top:1.6rem}
p{margin:0 0 1rem}
ul{margin:0 0 1rem; padding-left:1.15rem}
li{margin:.35rem 0}
li::marker{color:var(--accent)}
a{color:var(--accent)}
strong{font-weight:650}
code{font-family:var(--mono); font-size:.87em; background:var(--code-bg); padding:.12em .35em; border-radius:4px; overflow-wrap:anywhere}
pre{background:var(--code-bg); border:1px solid var(--border); border-radius:10px; padding:16px 18px; overflow-x:auto; max-width:100%; margin:0 0 1.2rem}
pre code{background:none; padding:0; font-size:.82rem; line-height:1.6}
figure{width:min(1240px,calc(100vw - 48px)); position:relative; left:50%; transform:translateX(-50%); margin:1.8rem 0 2.2rem}
figure img{width:100%; height:auto; display:block; border:1px solid var(--border); border-radius:10px; background:#fff}
figcaption{margin-top:.7rem; font-size:.86rem; color:var(--fg-2)}
figcaption a{color:var(--accent)}
sup.cite{font-size:.66em; line-height:0; margin-left:.15em}
sup.cite a{color:var(--accent); text-decoration:none; padding:0 .12em; border-bottom:1px solid transparent}
sup.cite a:hover{border-bottom-color:var(--accent)}
ol.sources{margin:1rem 0 0; padding:0; list-style:none; font-size:.9rem}
ol.sources li{display:flex; gap:.6rem; padding:.35rem 0; border-bottom:1px solid var(--rule); overflow-wrap:anywhere}
ol.sources .sid{color:var(--fg-2); font-family:var(--mono); font-size:.82rem; min-width:2.6rem; flex:none}
ol.sources a{color:var(--fg-2); text-decoration:none}
ol.sources a:hover{color:var(--accent)}
footer.foot{border-top:1px solid var(--rule); padding:22px 0 48px; color:var(--fg-2); font-size:.88rem}
@media (max-width:640px){
  nav.toc ol{columns:1}
  body{font-size:16px}
}
"""


def esc(t):
    return html.escape(t, quote=False)


def _join_cites(t):
    pattern = r'(?:<sup class="cite">.*?</sup>)+'

    def repl(m):
        ids = re.findall(r'href="#src-(\d+)"', m.group(0))
        inner = ", ".join(f'<a href="#src-{n}" aria-label="sumber {n}">{n}</a>' for n in ids)
        return f'<sup class="cite">{inner}</sup>'
    return re.sub(pattern, repl, t)


def inline(t):
    t = esc(t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"\[(\d+)\]", r'<sup class="cite"><a href="#src-\1" aria-label="sumber \1">\1</a></sup>', t)
    return _join_cites(t)


def slug(t):
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


def main():
    md = open(MD).read()
    body_md, _, src_md = md.partition("\n## Sources\n")
    lines = body_md.split("\n")

    out, toc = [], []
    i = 0
    in_code, in_list = False, False
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("```"):
            if not in_code:
                out.append('<pre><code>')
                in_code = True
            else:
                out.append("</code></pre>")
                in_code = False
            i += 1
            continue
        if in_code:
            out.append(esc(ln))
            i += 1
            continue
        if in_list and not ln.startswith("- "):
            out.append("</ul>")
            in_list = False
        if ln.startswith("# "):
            i += 1
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
            alt, src = m.group(1), m.group(2)
            out.append(
                f'<figure><picture>'
                f'<source srcset="diagram-dark.png" media="(prefers-color-scheme: dark)">'
                f'<img src="{src}" alt="{esc(alt)}" width="2560" height="1520" loading="lazy" decoding="async">'
                f"</picture><figcaption>{esc(alt)}. Versi interaktif: "
                f'<a href="diagram.html">buka diagram</a> (zoom, pencarian, tema).</figcaption></figure>'
            )
        elif ln.strip() == "":
            pass
        else:
            out.append(f"<p>{inline(ln)}</p>")
        i += 1
    if in_list:
        out.append("</ul>")
    if in_code:
        out.append("</code></pre>")

    tochtml = "".join(f'<li><a href="#{s}">{esc(t)}</a></li>' for s, t in toc)
    srcs = []
    for ln in src_md.split("\n"):
        m = re.match(r"^\[(\d+)\]\s+(\S+)$", ln.strip())
        if m:
            n, url = m.group(1), m.group(2)
            host = re.sub(r"^https?://", "", url).split("/")[0]
            short = url if len(url) <= 96 else url[:93] + "..."
            srcs.append(
                f'<li id="src-{n}"><span class="sid">[{n}]</span>'
                f'<a href="{url}" title="{esc(host)}">{esc(short)}</a></li>'
            )

    page = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CubeSandbox di EKS Jakarta: sandbox microVM buat agent infra</title>
<meta name="description" content="Riset arsitektur dan dependency CubeSandbox untuk deployment di Amazon EKS Jakarta: bare metal vs PVM, ketersediaan komponen di ap-southeast-3, biaya, dan catatan risiko.">
<link rel="canonical" href="./">
<meta property="og:title" content="CubeSandbox di EKS Jakarta">
<meta property="og:description" content="Arsitektur, dependency, biaya, dan risiko menjalankan CubeSandbox sebagai agent infrastructure di ap-southeast-3.">
<meta property="og:type" content="article">
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
<header class="page">
  <h1>CubeSandbox di EKS Jakarta</h1>
  <p class="lede">Sandbox microVM buat agent infrastructure. Riset arsitektur, dependency, biaya, dan risiko untuk deployment di <b>Amazon EKS ap-southeast-3</b>. Catatan riset, 17 November 2026.</p>
</header>
<nav class="toc" aria-label="Isi halaman">
  <p>Isi</p>
  <ol>{tochtml}</ol>
</nav>
<main>
{"".join(out)}
<h2 id="sources">Sources</h2>
<ol class="sources">
{"".join(srcs)}
</ol>
</main>
<footer class="foot">
  <p>Disusun oleh Kai. Semua klaim teknis mengacu ke dokumentasi resmi CubeSandbox dan dokumentasi AWS; angka biaya diambil dari AWS Price List API untuk region ap-southeast-3 pada 17 November 2026, on-demand, belum termasuk pajak.</p>
</footer>
</div>
</body>
</html>
"""
    os.makedirs(SITE, exist_ok=True)
    open(os.path.join(SITE, "index.html"), "w").write(page)
    print("index.html bytes:", len(page), "| sections:", len(toc), "| sources:", len(srcs))

    # --- contrast audit (WCAG relative luminance) ---
    def lum(hexc):
        c = hexc.lstrip("#")
        if len(c) == 3:
            c = "".join(ch * 2 for ch in c)
        r, g, b = (int(c[i:i + 2], 16) / 255 for i in (0, 2, 4))

        def f(v):
            return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
        return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)

    def ratio(a, b):
        la, lb = lum(a), lum(b)
        hi, lo = max(la, lb), min(la, lb)
        return round((hi + 0.05) / (lo + 0.05), 2)

    schemes = {
        "light": dict(bg="#fafaf8", surface="#ffffff", border="#d3d3cb", fg="#15171b", fg2="#454b54", accent="#0f6f5c"),
        "dark": dict(bg="#0e1116", surface="#161b22", border="#313a47", fg="#e8ebf0", fg2="#aab3bf", accent="#57d2b4"),
    }
    for name, t in schemes.items():
        checks = {
            "fg on bg": ratio(t["fg"], t["bg"]),
            "fg on surface": ratio(t["fg"], t["surface"]),
            "fg2 on bg": ratio(t["fg2"], t["bg"]),
            "fg2 on surface": ratio(t["fg2"], t["surface"]),
            "accent on bg": ratio(t["accent"], t["bg"]),
            "accent on surface": ratio(t["accent"], t["surface"]),
            "border vs surface": ratio(t["border"], t["surface"]),
        }
        print(f"[{name}]", {k: (v, "ok" if (v >= 4.5 if "border" not in k else v >= 1.5) else "FAIL") for k, v in checks.items()})


if __name__ == "__main__":
    main()
