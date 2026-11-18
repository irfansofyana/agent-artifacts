#!/usr/bin/env python3
"""Generate the research page: open-source projects that use AI to fix security
vulnerabilities found by GitLab (English + Indonesian, one source of truth).

Star counts and licences were read from the GitHub API on 18 November 2026.
Output: build/index.html (English) and build/id.html (Indonesian), plus assets/.
"""

import html
import os
import pathlib
import shutil

HERE = pathlib.Path(__file__).resolve().parent
OUT = pathlib.Path(os.environ.get("ARTIFACT_OUT") or (HERE / "build"))
ASSETS_SRC = HERE / "assets"
DATE_EN = "18 November 2026"
DATE_ID = "18 November 2026"

# Ranked by GitHub stars, with GitLab fit and licence shown beside each row.
# Each row: name, url, stars, licence, what it does, gitlab fit, status.
ROWS = [
    ("OpenHands", "https://github.com/OpenHands/OpenHands", 93749, "MIT",
     "AI agent platform for software engineering. Fix-and-PR is a use case built on it, not a built-in scanner integration.",
     "None in its README.", "Mature"),
    ("Strix", "https://github.com/usestrix/strix", 76460, "Apache-2.0",
     "AI penetration testing that finds and fixes app vulnerabilities.",
     "Lists GitLab among DevSecOps integrations. Fix-PR behaviour on GitLab not verified.", "Active"),
    ("Shannon", "https://github.com/KeygraphHQ/shannon", 52040, "AGPL-3.0",
     "AI pentester for web apps and APIs that checks source code for exploitable issues.",
     "Official GitLab CI/CD component. Fix generation not verified.", "Active"),
    ("Aider", "https://github.com/aider-AI/aider", 50167, "Apache-2.0",
     "Terminal AI pair programmer. General-purpose, not a security pipeline.",
     "None found. You would wire it into a pipeline yourself.", "Last push May 2026"),
    ("Trivy", "https://github.com/aquasecurity/trivy", 39503, "Apache-2.0",
     "Scanner for containers, IaC, dependencies and secrets. Finds issues, does not fix them.",
     "Scanner that runs as a CLI, so it can sit in any CI. GitLab not tested here. No AI fix.", "Active"),
    ("Continue", "https://github.com/continuedev/continue", 36510, "Apache-2.0",
     "Open-source coding agent (from its GitHub description).",
     "None specific to security.", "Active"),
    ("Renovate", "https://github.com/renovatebot/renovate", 23167, "AGPL-3.0",
     "Dependency update bot that opens merge requests for version bumps. Deterministic, not AI.",
     "Documented GitLab platform: creates merge requests when platform=gitlab. Not an AI fixer. Covers dependency updates, not code bugs.", "Active"),
    ("Semgrep engine", "https://github.com/semgrep/semgrep", 17801, "LGPL-2.1",
     "SAST engine (LGPL-2.1). AI Autofix that opens fix MRs is in the paid platform, not the engine.",
     "First-class GitLab integration; the README names GitLab among its users.", "Active"),
    ("CodeQL", "https://github.com/github/codeql", 10382, "MIT",
     "Query libraries and engine behind GitHub code scanning. Scanner, GitHub-centric.",
     "Not a GitLab-native fixer. Autofix is a GitHub Copilot feature.", "Active"),
    ("Opengrep", "https://github.com/opengrep/opengrep", 3357, "LGPL-2.1",
     "Open fork of Semgrep CE. Scanner only, no AI fix.",
     "Scanner that runs as a CLI. GitLab not tested here.", "Active"),
    ("Buttercup", "https://github.com/trailofbits/buttercup", 1757, "AGPL-3.0",
     "Trail of Bits' DARPA AIxCC cyber reasoning system: fuzzing plus multi-agent LLM patching, with fixes checked by a test build.",
     "No GitLab integration found in its README. Its fixes are checked against the project's build and tests.", "Active"),
    ("VulnHunter (Capital One)", "https://github.com/capitalone/vulnhunter", 1181, "Apache-2.0",
     "Claude Code skills: hunts exploitable bugs, writes a failing test, then proposes a fix.",
     "No GitLab support found in the README.", "Last push Oct 2026"),
    ("OpenHands vulnerability-fixer", "https://github.com/OpenHands/vulnerability-fixer", 31, "MIT",
     "OpenHands app: Trivy scan, then agents open one PR per selected fix.",
     "GitHub only, per its README.", "Prototype"),
    ("SecureFix", "https://github.com/mkamranr/securefix", 0, "None (no LICENSE file)",
     "GitLab SAST triage and validated fixes, using a self-hosted vLLM model. Air-gap ready.",
     "Built for GitLab: reads the SAST report, opens fix MRs. Needs GitLab Ultimate.", "New, single author"),
]

# Vendor features that a team may use alongside (not open source).
VENDOR = [
    ("GitLab Duo Agentic SAST Vulnerability Resolution",
     "https://docs.gitlab.com/user/application_security/vulnerabilities/agentic_vulnerability_resolution/",
     "Generally available since GitLab 18.11. Opens an MR with a fix for High and Critical SAST findings on the default branch. Needs GitLab Ultimate, GitLab Duo Agent Platform, and the flows turned on."),
    ("GitLab Duo Vulnerability Resolution (non-agentic)",
     "https://docs.gitlab.com/user/application_security/remediate/duo/",
     "Creates an MR suggestion comment on a SAST finding. Ultimate tier, default model Anthropic Claude Sonnet 4.6, and the output needs review."),
]

# Tools that open a GitLab MR. Blurbs are (en, id). Checked against vendor docs, not by running them.
DRAFT_MR = [
    ("Codex Security",
     "https://learn.chatgpt.com/docs/security/cli/ci/gitlab",
     "OpenAI, research preview. The official GitLab CI example opens a draft MR when CODEX_SECURITY_CREATE_MR is true, on branch codex-security/fix-<finding-hash>, and never merges. You paste the YAML. It is not an include. Needs an OpenAI key with Codex Security access. SARIF ingestion needs GitLab Ultimate 19.2 or later. The example pins the CLI at 0.8.1.",
     "OpenAI, masih research preview. Contoh GitLab CI resminya membuka draft MR kalau CODEX_SECURITY_CREATE_MR true, di branch codex-security/fix-<finding-hash>, dan tidak pernah merge. YAML-nya ditempel, bukan include. Butuh OpenAI key yang punya akses Codex Security. Ingest SARIF butuh GitLab Ultimate 19.2 atau lebih baru. Contohnya mem-pin CLI di 0.8.1."),
    ("Pixee",
     "https://docs.pixee.ai/integrations/scms/gitlab/",
     "Commercial. Opens GitLab merge requests for SAST and dependency findings through a service-account token and webhooks. Their docs say no change to .gitlab-ci.yml is required. Works with GitLab.com and self-hosted GitLab. Not an importable CI template.",
     "Komersial. Membuka merge request GitLab untuk temuan SAST dan dependency lewat token service-account dan webhook. Dokumentasinya bilang .gitlab-ci.yml tidak perlu diubah. Jalan di GitLab.com dan GitLab self-hosted. Bukan template CI yang bisa di-import."),
    ("Aikido AutoFix",
     "https://help.aikido.dev/autofix-and-remediation/configure/autofix-pr-configuration",
     "Commercial. Opens GitLab merge requests, and a setting can mark them draft. Configuration is the Aikido UI plus an optional .aikido file, not a CI include.",
     "Komersial. Membuka merge request GitLab, dan ada setting untuk menandainya sebagai draft. Konfigurasinya UI Aikido plus file .aikido opsional, bukan CI include."),
]

EN = {
    "lang": "en",
    "title": "Open-source projects that use AI to fix GitLab vulnerabilities",
    "description": "Ranked by GitHub stars, with GitLab fit and licence. Which open-source projects use AI to fix security findings from GitLab, and which are trustworthy enough to use.",
    "eyebrow": f"Research · GitLab × AI remediation · {DATE_EN}",
    "h1": "Open-source projects that use AI to fix GitLab vulnerabilities",
    "lede": "Short answer: no open-source project is both widely used and built to fix GitLab findings with AI. The most-starred AI fixers are generic or GitHub-first. The GitLab-native ones are new and have almost no adoption yet.",
    "switch": ("Bahasa Indonesia", "id.html"),
    "sections": [
        ("verdict", "Verdict", [
            "If you need a GitLab fix loop today, use Semgrep for findings and fix suggestions, and GitLab Duo's agentic resolution if you are on Ultimate. Both are trusted by many teams. Neither is a fully open AI fix pipeline.",
            "If you need an open, self-hosted AI fix loop, none of the projects below is a safe default yet. SecureFix is the closest match for GitLab, but it has no licence and no adoption. OpenHands has the adoption, but its vulnerability-fixer is a GitHub-only prototype.",
            "Stars measure attention, not whether a fix is correct. I ran none of these tools against a GitLab project. Treat this as a shortlist to test, not a verdict on quality.",
            "If the requirement is a draft MR from CI, Codex Security is the one whose docs describe that job. Pixee and Aikido also open GitLab MRs, from their own service, not from a template you import.",
        ]),
        ("ranking", "Open-source candidates, ranked by GitHub stars", None),
        ("vendor", "Vendor features (not open source)", None),
        ("draft_mr", "Opening a merge request", [
            "The open-source table has no widely used tool that opens a GitLab fix MR from CI. Shannon's open-source GitLab component does not include remediation. Fix pull requests are a paid Shannon feature, and those docs do not say the MR lands on GitLab.",
            "Of the tools below, only Codex Security documents the path as a GitLab CI job, and that job is YAML you paste, not a CI/CD Catalog component. Pixee and Aikido open the MR from their platform. GitLab Duo's agentic flow, in the vendor list above, also opens an MR on Ultimate.",
        ]),
        ("method", "How this was checked", [
            "Star counts, licences, last push dates and descriptions came from the GitHub REST API on 18 November 2026. READMEs were read from raw.githubusercontent.com. Claims about GitLab support come from README text and GitLab's own docs, not from running the tools.",
            "Not verified by running them: whether Strix or Shannon open fix MRs on GitLab. Renovate's docs say it creates GitLab merge requests; this run did not execute Renovate. VulnHunter's licence is Apache-2.0, read from the repo LICENSE file.",
            "Star counts change daily. Re-check before you decide.",
        ]),
        ("sources", "Sources", None),
    ],
    "table_head": ["Project", "Stars", "Licence", "What it does", "GitLab fit", "Status"],
    "footer": "Research notes, not a tested runbook. No candidate was executed against a GitLab project.",
    "other_lang_label": "Bahasa Indonesia",
}

ID = {
    "lang": "id",
    "title": "Proyek open-source yang pakai AI untuk memperbaiki kerentanan GitLab",
    "description": "Diurutkan berdasarkan bintang GitHub, dengan kecocokan GitLab dan lisensi. Proyek open-source mana yang memakai AI untuk memperbaiki temuan keamanan dari GitLab, dan mana yang cukup layak dipakai.",
    "eyebrow": f"Riset · GitLab × AI remediation · {DATE_ID}",
    "h1": "Proyek open-source yang pakai AI untuk memperbaiki kerentanan GitLab",
    "lede": "Jawaban singkatnya: belum ada proyek open-source yang sekaligus banyak dipakai dan dibangun untuk memperbaiki temuan GitLab pakai AI. Pemberi fix AI dengan bintang terbanyak umumnya generik atau berpusat di GitHub. Yang khusus GitLab masih baru dan adopsinya belum banyak.",
    "switch": ("English", "index.html"),
    "sections": [
        ("verdict", "Kesimpulan", [
            "Kalau butuh alur fix GitLab sekarang, pakai Semgrep untuk temuan dan saran perbaikannya, plus agentic resolution dari GitLab Duo kalau kamu di tier Ultimate. Keduanya dipercaya banyak tim. Tapi dua-duanya bukan pipeline AI fix yang sepenuhnya open.",
            "Kalau butuh alur AI fix yang open dan self-hosted, belum ada proyek di bawah yang aman dijadikan default. SecureFix paling cocok untuk GitLab, tapi belum punya lisensi dan belum ada adopsinya. OpenHands punya adopsi, tapi vulnerability-fixer-nya prototipe yang hanya untuk GitHub.",
            "Bintang mengukur perhatian, bukan apakah fix-nya benar. Saya tidak menjalankan satu pun tool ini terhadap proyek GitLab. Anggap ini shortlist untuk diuji, bukan vonis soal kualitas.",
            "Kalau syaratnya draft MR dari CI, Codex Security yang dokumentasinya menjelaskan job itu. Pixee dan Aikido juga membuka MR GitLab, dari layanan mereka sendiri, bukan dari template yang di-import.",
        ]),
        ("ranking", "Kandidat open-source, diurutkan berdasarkan bintang GitHub", None),
        ("vendor", "Fitur vendor (bukan open source)", None),
        ("draft_mr", "Membuka merge request", [
            "Tabel open-source tidak punya tool yang banyak dipakai dan membuka MR fix GitLab dari CI. Component GitLab Shannon yang open-source tidak mencakup remediation. Fix pull request ada di Shannon berbayar, dan dokumentasinya tidak bilang MR-nya mendarat di GitLab.",
            "Dari tool di bawah, hanya Codex Security yang mendokumentasikan jalurnya sebagai job GitLab CI, dan job itu YAML yang ditempel, bukan CI/CD Catalog component. Pixee dan Aikido membuka MR dari platform mereka. Alur agentic GitLab Duo, di daftar vendor di atas, juga membuka MR di tier Ultimate.",
        ]),
        ("method", "Cara pengecekannya", [
            "Jumlah bintang, lisensi, tanggal push terakhir, dan deskripsi diambil dari GitHub REST API pada 18 November 2026. README dibaca dari raw.githubusercontent.com. Klaim dukungan GitLab berasal dari teks README dan dokumentasi GitLab, bukan dari menjalankan tool-nya.",
            "Belum dijalankan di riset ini: apakah Strix atau Shannon benar-benar membuka MR fix di GitLab. Dokumentasi Renovate bilang dia membuat merge request di GitLab; Renovate tidak dijalankan di sini. Lisensi VulnHunter Apache-2.0, dibaca dari file LICENSE di repo.",
            "Jumlah bintang berubah setiap hari. Cek ulang sebelum memutuskan.",
        ]),
        ("sources", "Sumber", None),
    ],
    "table_head": ["Proyek", "Bintang", "Lisensi", "Fungsinya", "Kecocokan GitLab", "Status"],
    "footer": "Catatan riset, bukan runbook yang sudah teruji. Tidak ada kandidat yang dijalankan terhadap proyek GitLab.",
    "other_lang_label": "English",
}

# Citations are numbered in the order the ledger returned them (see sources.py output).
SOURCES = [
    ("GitLab Docs: Agentic SAST Vulnerability Resolution", "https://docs.gitlab.com/user/application_security/vulnerabilities/agentic_vulnerability_resolution/"),
    ("GitLab Docs: Vulnerability details", "https://docs.gitlab.com/user/application_security/vulnerabilities/"),
    ("GitLab Docs: Resolve vulnerabilities with AI", "https://docs.gitlab.com/user/application_security/remediate/duo/"),
    ("GitLab 18.9 release notes", "https://docs.gitlab.com/releases/18/gitlab-18-9-released/"),
    ("GitLab 18.10: AI-native triage and remediation", "https://about.gitlab.com/blog/gitlab-18-10-brings-ai-native-triage-and-remediation/"),
    ("GitLab Docs: Static application security testing (SAST)", "https://docs.gitlab.com/user/application_security/sast/"),
    ("SecureFix repository", "https://github.com/mkamranr/securefix"),
    ("SecureFix README", "https://raw.githubusercontent.com/mkamranr/securefix/main/README.md"),
    ("OpenHands vulnerability-fixer repository", "https://github.com/OpenHands/vulnerability-fixer"),
    ("OpenHands vulnerability-fixer README", "https://raw.githubusercontent.com/OpenHands/vulnerability-fixer/main/README.md"),
    ("OpenHands: Vulnerability Fixer announcement", "https://www.openhands.dev/blog/20260303-vulnerability-fixer"),
    ("Buttercup repository", "https://github.com/trailofbits/buttercup"),
    ("Buttercup LICENSE (AGPL-3.0)", "https://raw.githubusercontent.com/trailofbits/buttercup/main/LICENSE"),
    ("Trail of Bits: Buttercup is now open source", "https://blog.trailofbits.com/2025/08/08/buttercup-is-now-open-source/"),
    ("Opengrep vs Semgrep CE comparison", "https://docs.semgrep.dev/faq/comparisons/opengrep-1"),
    ("Semgrep: Rule-defined fix", "https://docs.semgrep.dev/writing-rules/rule-defined-fix.md"),
    ("Semgrep: Autofix for Semgrep Code", "https://docs.semgrep.dev/semgrep-code/triage-remediation/autofix"),
    ("GitHub changelog: agentic autofix GA", "https://github.blog/changelog/2026-10-15-agentic-autofix-for-code-scanning-alerts-general-availability/"),
    ("Renovate docs: GitLab platform", "https://docs.renovatebot.com/modules/platform/gitlab/"),
    ("VulnHunter LICENSE (Apache-2.0)", "https://raw.githubusercontent.com/capitalone/vulnhunter/main/LICENSE"),
    ("Codex Security: Run in GitLab CI/CD", "https://learn.chatgpt.com/docs/security/cli/ci/gitlab"),
    ("Pixee: GitLab integration", "https://docs.pixee.ai/integrations/scms/gitlab/"),
    ("Aikido: AutoFix PR configuration", "https://help.aikido.dev/autofix-and-remediation/configure/autofix-pr-configuration"),
    ("Shannon: open source vs paid remediation", "https://keygraph.io/open-source"),
]

CSS_HREF = "assets/page.css"


def esc(s):
    return html.escape(s, quote=True)


def fmt_stars(n):
    return "not checked" if n is None else f"{n:,}"


def render_table(lang):
    head = "".join(f"<th scope=\"col\">{esc(h)}</th>" for h in lang["table_head"])
    body = []
    for name, url, stars, lic, what, fit, status in ROWS:
        body.append(
            "<tr>"
            f"<th scope=\"row\"><a href=\"{esc(url)}\">{esc(name)}</a></th>"
            f"<td class=\"num\">{fmt_stars(stars)}</td>"
            f"<td>{esc(lic)}</td>"
            f"<td>{esc(what)}</td>"
            f"<td>{esc(fit)}</td>"
            f"<td>{esc(status)}</td>"
            "</tr>"
        )
    return (
        "<div class=\"table-wrap\" tabindex=\"0\"><table>"
        f"<thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table></div>"
    )


def render_vendor(lang):
    items = "".join(
        f"<li><a href=\"{esc(u)}\">{esc(n)}</a>. {esc(d)}</li>" for n, u, d in VENDOR
    )
    return f"<ul>{items}</ul>"


def render_draft(lang):
    idx = 2 if lang["lang"] == "en" else 3
    items = "".join(
        f"<li><a href=\"{esc(r[1])}\">{esc(r[0])}</a>. {esc(r[idx])}</li>"
        for r in DRAFT_MR
    )
    return f"<ul>{items}</ul>"


def render_sources():
    items = "".join(
        f"<li><a href=\"{esc(u)}\">{esc(t)}</a></li>" for t, u in SOURCES
    )
    return f"<ol class=\"sources\">{items}</ol>"


def render_page(lang):
    sections = []
    for key, heading, paras in lang["sections"]:
        sid = f"s-{key}"
        if key == "ranking":
            inner = render_table(lang)
        elif key == "vendor":
            inner = render_vendor(lang)
        elif key == "draft_mr":
            inner = "".join(f"<p>{esc(p)}</p>" for p in paras) + render_draft(lang)
        elif key == "sources":
            inner = render_sources()
        else:
            inner = "".join(f"<p>{esc(p)}</p>" for p in paras)
        sections.append(
            f"<section id=\"{sid}\" class=\"chapter\"><h2>{esc(heading)}</h2>{inner}</section>"
        )
    switch_label, other_href = lang["switch"]
    return f"""<!doctype html>
<html lang="{lang['lang']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(lang['title'])}</title>
<meta name="description" content="{esc(lang['description'])}">
<meta name="color-scheme" content="light dark">
<link rel="stylesheet" href="{CSS_HREF}">
</head>
<body>
<a class="skip" href="#site-main">Skip to content</a>
<header class="masthead">
  <div class="page">
    <p class="wordmark">Research</p>
    <nav aria-label="Language">
      <a href="{esc(other_href)}">{esc(switch_label)}</a>
    </nav>
  </div>
</header>
<main id="site-main" class="page">
  <header class="hero">
    <p class="eyebrow">{esc(lang['eyebrow'])}</p>
    <h1>{esc(lang['h1'])}</h1>
    <p class="lede">{esc(lang['lede'])}</p>
  </header>
  {''.join(sections)}
</main>
<footer class="page foot">
  <p>{esc(lang['footer'])}</p>
</footer>
</body>
</html>
"""


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "assets").mkdir(parents=True)
    (OUT / "index.html").write_text(render_page(EN), encoding="utf-8")
    (OUT / "id.html").write_text(render_page(ID), encoding="utf-8")
    # Shared stylesheet and font come from the verified here.now starter.
    starter = pathlib.Path(os.environ.get(
        "HERENOW_STARTER",
        os.path.expanduser("~/.hermes/skills/productivity/herenow-artifact-publisher/templates/scandinavian-page.css"),
    ))
    font = pathlib.Path(os.environ.get(
        "HERENOW_FONT",
        os.path.expanduser("~/.hermes/skills/productivity/herenow-artifact-publisher/root-index/assets/inter-latin-wght-normal.woff2"),
    ))
    shutil.copy(starter, OUT / CSS_HREF)
    (OUT / "assets" / "fonts").mkdir(parents=True, exist_ok=True)
    shutil.copy(font, OUT / "assets" / "fonts" / "InterVariable-latin.woff2")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
