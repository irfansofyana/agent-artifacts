#!/usr/bin/env python3
"""Generate the Codex Security x GitLab research page (Indonesian + English)
from a single source. Every table, count and piece of chrome is rendered from
the data below so the two language pages cannot drift apart.
"""

import html
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "site"
DATE_ID = "18 November 2026"
DATE_EN = "18 November 2026"

# ---------------------------------------------------------------- chrome

CHROME = {
    "id": {
        "lang": "id",
        "title": "Codex Security untuk GitLab: yang benar-benar bisa dipakai, dan di mana batasnya",
        "description": "Riset Codex Security dari OpenAI untuk alur kerja GitLab: apa yang sudah bisa dipakai hari ini, fakta yang menentukan desainnya, batasan yang jangan diklaim, dan asumsi yang belum diverifikasi.",
        "eyebrow": f"Riset &middot; Codex Security &times; GitLab &middot; {DATE_ID}",
        "lede": "Catatan riset atas Codex Security dari OpenAI untuk alur kerja GitLab: apa yang sudah bisa dipakai hari ini, fakta yang menentukan desainnya, batasan yang jangan diklaim, dan asumsi yang belum diverifikasi.",
        "nav_label": "Navigasi bahasa",
        "here": "Bahasa Indonesia",
        "other": "English",
        "scroll_hint": "Tabel bisa digeser ke samping.",
        "footer": "Riset teknologi, bukan runbook yang sudah terbukti jalan. Pipeline dan script-nya sudah divalidasi sintaks terhadap payload contoh, tapi belum pernah dieksekusi end to end di runner sungguhan.",
    },
    "en": {
        "lang": "en",
        "title": "Codex Security on GitLab: what actually works, and where it stops",
        "description": "Research notes on OpenAI's Codex Security for a GitLab workflow: what is usable today, the facts that decide the design, the limits not to promise, and the assumptions still unverified.",
        "eyebrow": f"Research &middot; Codex Security &times; GitLab &middot; {DATE_EN}",
        "lede": "Research notes on OpenAI's Codex Security for a GitLab workflow: what is usable today, the facts that decide the design, the limits not to promise, and the assumptions still unverified.",
        "nav_label": "Language navigation",
        "here": "English",
        "other": "Bahasa Indonesia",
        "scroll_hint": "This table scrolls sideways.",
        "footer": "Technology research, not a proven runbook. The pipeline and its scripts were syntax-validated against sample payloads, but have never been executed end to end on a real runner.",
    },
}

# ---------------------------------------------------------------- data

TWO_JOBS = [
    {
        "id": "Scan",
        "en": "Scan",
        "id_d": "Mencari kerentanan yang belum pernah dilaporkan siapa pun. Butuh threat model untuk repo itu, analisis, lalu validasi di sandbox.",
        "en_d": "Hunts for vulnerabilities nobody has reported yet. Needs a repo-specific threat model, analysis, then sandboxed validation.",
    },
    {
        "id": "Assess &amp; fix",
        "en": "Assess &amp; fix",
        "id_d": "Menilai dan memperbaiki temuan yang sudah dilaporkan scanner lain. Tidak butuh scanner-nya ikut jalan: temuan masuk sebagai teks biasa atau path file.",
        "en_d": "Assesses and fixes a finding another scanner already reported. It does not need its own scanner to run: the finding arrives as literal text or a file path.",
    },
]

COMMANDS = [
    (
        "scan",
        "Memindai repo, path terpilih, atau diff. Mode <code>standard</code> dan <code>deep</code>.",
        "Scans the repository, selected paths, or a diff. Modes <code>standard</code> and <code>deep</code>.",
    ),
    (
        "validate",
        "Menilai satu kandidat temuan terhadap source, di sandbox read-only.",
        "Assesses one candidate finding against source, in a read-only sandbox.",
    ),
    (
        "patch",
        "Membuat lalu memverifikasi perbaikan, opsional membuka draft PR atau MR.",
        "Generates and verifies a fix, optionally opening a draft PR or MR.",
    ),
    (
        "verify-fix",
        "Pemeriksaan independen apakah sebuah isu sudah benar-benar diperbaiki.",
        "Independent check of whether an issue is actually fixed.",
    ),
    (
        "scan import",
        "Memuat temuan yang sudah ada dalam skema Codex Security, lewat CSV atau JSON.",
        "Loads findings already in the Codex Security schema, as CSV or JSON.",
    ),
    (
        "publish findings",
        "Mengimpor laporan dari scanner lain ke workbench.",
        "Imports an external scanner report into the workbench.",
    ),
    (
        "findings, scans, export,<br>dedupe, classify-severity,<br>suggest-owners",
        "Operasi workbench atas hasil yang sudah tersimpan.",
        "Workbench operations on saved results.",
    ),
]

EXIT_CODES = [
    ("0", "Lolos, tidak ada temuan di atas threshold.", "Pass, no findings at or above the threshold.", "lolos", "pass"),
    ("1", "Ada temuan di atau di atas threshold.", "Findings at or above the threshold.", "ada temuan", "findings"),
    ("2", "Error input, runtime, atau integritas hasil.", "Input, runtime, or result-integrity error.", "error", "error"),
    ("130 / 143", "Proses terinterupsi.", "Interrupted.", "terinterupsi", "interrupted"),
]


def exits_inline(lang):
    idx = 3 if lang == "id" else 4
    return ", ".join(f"<code>{c[0]}</code> {c[idx]}" for c in EXIT_CODES)

FLOW = {
    "id": [
        ("Temuan GitLab", "Artefak SAST/DAST atau vulnerability report project."),
        ("Satu statement per temuan", "Menyebut rule, file, dan baris. Yang tanpa lokasi masuk triage."),
        ("validate", "Penilaian read-only lewat gateway. Mengonfirmasi atau menolak."),
        ("patch", "Perbaikan diverifikasi, di-commit ke branch, jadi draft MR."),
    ],
    "en": [
        ("GitLab findings", "SAST/DAST artifacts, or the project vulnerability report."),
        ("One statement per finding", "Names the rule, file and line. The ones without a location go to triage."),
        ("validate", "Read-only assessment through the gateway. Confirms or rejects."),
        ("patch", "Fix verified, committed to a branch, opened as a draft MR."),
    ],
    "id_cap": "Alur fix-first: hanya temuan yang dikonfirmasi <code>validate</code> yang sampai ke tahap patch.",
    "en_cap": "The fix-first flow: only findings <code>validate</code> confirmed reach the patch stage.",
}

CREDS = [
    (
        "Model key",
        "Virtual key gateway",
        "Gateway virtual key",
        "Kedua tahap, lewat provider profile.",
        "Both stages, through the provider profile.",
    ),
    (
        "Read token",
        "<code>read_api</code>",
        "<code>read_api</code>",
        "Cuma tahap validate, buat menarik daftar temuan.",
        "The validate stage only, to pull the findings list.",
    ),
    (
        "Write token",
        "<code>api</code>, <code>write_repository</code>",
        "<code>api</code>, <code>write_repository</code>",
        "Cuma tahap publish, buat push branch dan bikin draft MR.",
        "The publish stage only, to push a branch and open a draft MR.",
    ),
]

FINDING_SOURCES = [
    (
        "Vulnerability report",
        "<code>GET /projects/:id/vulnerability_findings</code> dengan read token.",
        "<code>GET /projects/:id/vulnerability_findings</code> with a read token.",
        "Pandangan backlog: apa yang masih open sekarang, setelah triase manusia.",
        "The backlog view: what is open right now, after human triage.",
    ),
    (
        "SAST artifact",
        "<code>gl-sast-report.json</code> dari job scanner.",
        "The <code>gl-sast-report.json</code> artifact from the scanner job.",
        "Output mentah seluruhnya, termasuk temuan yang GitLab tidak promosikan jadi record.",
        "The whole raw output, including findings GitLab did not promote to records.",
    ),
    (
        "DAST artifact",
        "Artefak report dari job DAST.",
        "The report artifact from the DAST job.",
        "Temuan runtime. Sebagian besar butuh triase dulu sebelum bisa di-patch.",
        "Runtime findings. Most of them need triage before anything can be patched.",
    ),
]

RISKS = [
    (
        "<code>--auth api-key</code> menerima environment key milik provider custom.",
        "Run preflight. Ini titik paling mungkin di mana desainnya perlu diubah.",
        "<code>--auth api-key</code> accepts the custom provider's environment key.",
        "The preflight run. This is the most likely place the design needs a change.",
    ),
    (
        "Alias gateway-nya Responses-native, bukan bridged.",
        "Cek <code>model_info.supported_endpoints</code>. Kalau bridged, ini jadi tiket gateway sebelum apa pun bisa mulai.",
        "The gateway alias is Responses-native, not bridged.",
        "Check <code>model_info.supported_endpoints</code>. If it is bridged, that becomes a gateway ticket before anything starts.",
    ),
    (
        "Model di belakang alias bisa menghasilkan JSON sesuai schema.",
        "Jalankan <code>validate</code> pada satu temuan dan periksa outputnya. Tanpa ini, gate confirm-then-patch butuh mekanisme lain.",
        "The model behind the alias can produce schema-constrained JSON.",
        "Run <code>validate</code> on a single finding and inspect the output. Without it, the confirm-then-patch gate needs another mechanism.",
    ),
    (
        "Patching a supplied finding can run unattended in a CI checkout, and the files the CLI reports are the files that changed.",
        "One real run, then <code>git status</code> and <code>git diff --stat</code> in the clone. The branch is cut from exactly those reported paths.",
        "Supplied-issue patching can run unattended in a CI checkout, and the files the CLI reports are the files that changed.",
        "One real run, then <code>git status</code> and <code>git diff --stat</code> in the clone. The branch is cut from exactly those reported paths.",
    ),
    (
        "Field path di respons vulnerability sesuai dengan yang diharapkan mapping script.",
        "Dump satu respons asli lalu bandingkan. Endpoint-nya ditandai deprecated ke arah GraphQL.",
        "Field paths in the vulnerability response match what the mapping script expects.",
        "Dump one real response and compare. The endpoints are marked deprecated in favour of GraphQL.",
    ),
    (
        "Temuan tanpa lokasi source bisa dipetakan dengan andal.",
        "Untuk DAST, anggap belum bisa di iterasi pertama dan rencanakan triase sebagai langkah terpisah.",
        "Findings with no source location can be mapped reliably.",
        "For DAST, assume they cannot in the first iteration and plan triage as its own step.",
    ),
    (
        "Semantik entitlement tetap berlaku saat inference lewat gateway.",
        "Konfirmasi ke pemilik akun apakah akses Codex Security mengikuti key yang sampai ke model.",
        "Entitlement semantics hold when inference is routed through the gateway.",
        "Confirm with the account owner whether Codex Security access follows the key that reaches the model.",
    ),
    (
        "Kualitas perbaikan tetap bagus di model apa pun yang dipasang di belakang alias.",
        "Bandingkan beberapa fix buatan agen dengan fix dari model frontier. Kalau gateway-nya menyajikan model yang lebih kecil, perilaku validated-fix akan turun.",
        "Fix quality holds on whatever model sits behind the alias.",
        "Compare a few agent-authored fixes against a hosted frontier model. If the gateway fronts a smaller model, expect validated-fix behaviour to degrade.",
    ),
]

OUTCOMES = [
    ("verified",
     "A fix was produced and the agent's own verification passed.",
     "The only class that gets committed and opened as a draft MR."),
    ("no_change",
     "The agent judged that nothing needs changing.",
     "Recorded. Never retried: it is a judgement, not a failure."),
    ("blocked",
     "The agent needs a decision it is not allowed to make.",
     "Recorded. A human decides; the loop does not guess."),
    ("failed",
     "A fix was produced but did not verify.",
     "Recorded. Read the reasoning rather than rerunning it unchanged."),
    ("timeout",
     "Our own per-call ceiling fired (exit 124).",
     "Infrastructure. One retry if the budget still allows it."),
    ("sandbox_unavailable, error, interrupted",
     "Operational failure, not a security judgement.",
     "One retry, capped by the attempt limit; then it stays recorded."),
    ("no_patch_applied",
     "The statement was too vague for the agent to act on.",
     "Recorded. Sharpen the statement; a rerun changes nothing."),
]

POC = [
    ("Step 1, half a day: measure instead of guessing",
     "Run validate over five hand-picked findings in a clone, one call at a time, "
     "with a 600s ceiling. Log wall time, cost, and whether schema-constrained JSON "
     "comes back at all.",
     "A p50 and p90 seconds per finding, and a yes or no on the gateway schema "
     "question. Without those numbers any budget you set is a guess."),
    ("Step 2, week 1: patch without publishing",
     "Same five findings, patch with assess-patch-risk and JSON, publishing off. "
     "Results stay artifacts and a reviewer reads the diffs.",
     "A security reviewer agrees the fixes are worth review time, and you have a "
     "patch p90 to put in CS_PER_FINDING_P90."),
    ("Step 3, week 2: publish a small seed",
     "Turn on branch, push and draft MR for eight to ten confirmed findings, with a "
     "45 minute budget inside a 50 minute job ceiling.",
     "The number of merge requests equals the number of verified results, no secret "
     "appears in the job log, and a rejected fix produces no branch."),
    ("Step 4, week 3 and after: put it on a schedule",
     "Nightly validate, then the budgeted patch loop, then the report job that reads "
     "the merge requests back from the API.",
     "Two consecutive runs work on disjoint sets of findings, and a run that hits "
     "the budget loses nothing."),
]

POC_DONT = [
    "A deep scan of the whole repository inside the pilot budget.",
    "Auto-fixing DAST findings. They have no source location to reason about.",
    "One job for the entire backlog. Its blast radius is the whole backlog.",
    "Disabling the sandbox to make a runner work. Fix the runner instead.",
]

LOOP_SNIPPET = """while IFS=$'\\t' read -r id statement; do
  remaining=$(( BUDGET - ( $(date +%s) - started ) ))
  [ "$remaining" -lt "$P90" ] && { echo "budget stop: $remaining left"; break; }

  git -C "$WORK" checkout -f -q "$BASE_SHA"      # patch refuses a dirty tree
  git -C "$WORK" reset --hard -q "$BASE_SHA"
  git -C "$WORK" clean -qfd

  ( cd "$WORK" && env -i PATH="$PATH" HOME="$AGENT_HOME" CI=true \\
      LITELLM_API_KEY="$key" \\
      timeout "$CALL_TIMEOUT" codex-security patch "$statement" \\
      --assess-patch-risk --json > "$OUT/patch-$id.json" 2> "$OUT/patch-$id.err" )
  rc=$?

  case "$(classify "$id" "$rc")" in
    verified)                          publish_patch.sh "$id" "$files" ;;
    timeout|error|sandbox_unavailable) retry_once "$id" ;;
    *)                                 record_terminal "$id" ;;   # a judgement
  esac
done < "$WORKLIST"
"""

SOURCES = [
    ("Codex Security overview (OpenAI Help Center)", "https://help.openai.com/en/articles/20001107-codex-security"),
    ("Codex Security repository, CLI and SDK", "https://github.com/openai/codex-security"),
    ("CLI reference: scan, validate, patch, verify-fix", "https://learn.chatgpt.com/docs/security/cli/reference"),
    ("Scanner import guides", "https://github.com/openai/codex-security/blob/main/docs/scanner-imports/README.md"),
    ("Run Codex Security in GitLab CI/CD", "https://learn.chatgpt.com/docs/security/cli/ci/gitlab"),
    ("Codex advanced configuration, custom model providers", "https://developers.openai.com/codex/config-advanced"),
    ("LiteLLM native /v1/responses passthrough", "https://docs.litellm.ai/docs/response_api_native_passthrough"),
    ("GitLab vulnerability findings API", "https://docs.gitlab.com/api/vulnerability_findings/"),
    ("GitLab SAST report format and artifact name", "https://docs.gitlab.com/user/application_security/sast/"),
    ("glab authentication in CI", "https://docs.gitlab.com/cli/authentication/"),
]

# ---------------------------------------------------------------- render helpers


def table(headers, rows, region_label, first_wide=26, num=False):
    """rows: list of tuples of already-escaped HTML cell strings."""
    out = [
        '<div class="table-wrap" tabindex="0" role="region" '
        f'aria-label="{region_label}">',
        "<table>",
        "<thead><tr>",
    ]
    for i, h in enumerate(headers):
        style = f' style="width:{first_wide}%"' if i == 0 else ""
        out.append(f"<th{style}>{h}</th>")
    out.append("</tr></thead><tbody>")
    for r in rows:
        out.append("<tr>")
        for i, c in enumerate(r):
            cls = ' class="num"' if (num and i == 0) else ""
            out.append(f"<td{cls}>{c}</td>")
        out.append("</tr>")
    out.append("</tbody></table></div>")
    return "\n".join(out)


def flow_block(lang):
    boxes = []
    for i, (title, desc) in enumerate(FLOW[lang]):
        if i:
            boxes.append('<div class="arrow" aria-hidden="true">&#8594;</div>')
        boxes.append(f'<div class="box"><b>{title}</b>{desc}</div>')
    cap = FLOW["id_cap"] if lang == "id" else FLOW["en_cap"]
    return (
        '<figure class="figure"><div class="flow">'
        + "".join(boxes)
        + f'</div><figcaption>{cap}</figcaption></figure>'
    )


def outcomes_table():
    return table(
        ["Outcome", "What it means", "What the pipeline does"],
        [(f"<code>{r[0]}</code>", r[1], r[2]) for r in OUTCOMES],
        "Table: outcome classification",
        first_wide=24,
    )


def poc_block():
    cards = []
    for title, body, exit_criteria in POC:
        cards.append(
            f'<div class="card"><h3>{title}</h3><p>{body}</p>'
            f'<p class="exit"><strong>Exit criteria.</strong> {exit_criteria}</p></div>'
        )
    return "\n".join(cards)


def poc_dont_block():
    return "\n".join(f"<li>{item}</li>" for item in POC_DONT)


def snippet_block():
    return f"<pre><code>{html.escape(LOOP_SNIPPET)}</code></pre>"


def build(lang):
    c = CHROME[lang]
    L = lang == "id"

    two_jobs = table(
        ["Pekerjaan", "Isinya"] if L else ["Job", "What it does"],
        [(r[lang], r[f"{lang}_d"]) for r in TWO_JOBS],
        "Tabel: dua pekerjaan" if L else "Table: the two jobs",
        first_wide=22,
    )
    commands = table(
        ["Perintah", "Kegunaan"] if L else ["Command", "Purpose"],
        [(f"<code>{r[0]}</code>", r[1] if L else r[2]) for r in COMMANDS],
        "Tabel: peta kemampuan CLI" if L else "Table: CLI capability map",
        first_wide=24,
    )
    exits = table(
        ["Exit code", "Artinya"] if L else ["Exit code", "Meaning"],
        [(f"<code>{r[0]}</code>", r[1] if L else r[2]) for r in EXIT_CODES],
        "Tabel: arti exit code" if L else "Table: exit code meanings",
        first_wide=18,
        num=True,
    )
    creds = table(
        ["Kredensial", "Scope", "Dipakai di"] if L else ["Credential", "Scope", "Used by"],
        [(f"<code>{r[0]}</code>", r[1] if L else r[2], r[3] if L else r[4]) for r in CREDS],
        "Tabel: pemisahan kredensial" if L else "Table: credential split",
        first_wide=20,
    )
    sources_tbl = table(
        ["Sumber", "Cara ambil", "Paling cocok untuk"] if L else ["Source", "How to get it", "Best for"],
        [(r[0], r[1] if L else r[2], r[3] if L else r[4]) for r in FINDING_SOURCES],
        "Tabel: sumber temuan di GitLab" if L else "Table: GitLab finding sources",
        first_wide=20,
    )
    risks = table(
        ["Asumsi", "Cara menutupnya"] if L else ["Assumption", "How to close it"],
        [(r[0] if L else r[2], r[1] if L else r[3]) for r in RISKS],
        "Tabel: risiko terbuka" if L else "Table: open risks",
        first_wide=42,
    )
    src_list = "\n".join(
        f'<li><a href="{u}">{t}</a><br><span class="muted">{u}</span></li>' for t, u in SOURCES
    )

    body = BODY[lang]
    tokens = {
        "@@TWO_JOBS@@": two_jobs,
        "@@COMMANDS@@": commands,
        "@@CMD_COUNT@@": str(len(COMMANDS)),
        "@@EXITS@@": exits,
        "@@EXITS_INLINE@@": exits_inline(lang),
        "@@FLOW@@": flow_block(lang),
        "@@CREDS@@": creds,
        "@@FINDING_SOURCES@@": sources_tbl,
        "@@RISKS@@": risks,
        "@@RISK_COUNT@@": str(len(RISKS)),
        "@@OUTCOMES@@": outcomes_table(),
        "@@OUTCOME_COUNT@@": str(len(OUTCOMES)),
        "@@POC@@": poc_block(),
        "@@POC_DONT@@": poc_dont_block(),
        "@@LOOP@@": snippet_block(),
        "@@SOURCE_LIST@@": src_list,
    }
    for k, v in tokens.items():
        body = body.replace(k, v)

    # English is the root page. Add "id" here to emit the Indonesian page at
    # index-id.html again and get the language switcher back.
    PUBLISH_LANGS = ("en",)
    self_file = "index-id.html" if L else "index.html"
    other = "index.html" if L else "index-id.html"
    if len(PUBLISH_LANGS) > 1:
        nav = (
            f'<nav class="switch" aria-label="{c["nav_label"]}">\n'
            f'<a href="{self_file}" aria-current="page">{c["here"]}</a>'
            f'<span class="sep">&middot;</span><a href="{other}">{c["other"]}</a>\n'
            "</nav>"
        )
    else:
        nav = ""
    return f"""<!DOCTYPE html>
<html lang="{c['lang']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{c['title']}</title>
<meta name="description" content="{c['description']}">
<link rel="stylesheet" href="assets/style.css">
</head>
<body data-scroll-hint="{c['scroll_hint']}">
<div class="wrap">
<header class="site">
<p class="eyebrow">{c['eyebrow']}</p>
<h1>{c['title']}</h1>
<p class="lede">{c['lede']}</p>
{nav}
</header>
<main>
{body}
</main>
<footer class="site">
<p>{c['footer']}</p>
</footer>
</div>
<script>
(function () {{
  var label = document.body.getAttribute('data-scroll-hint');
  var wraps = Array.prototype.slice.call(document.querySelectorAll('.table-wrap'));
  var hints = wraps.map(function (wrap) {{
    var p = document.createElement('p');
    p.className = 'hint';
    p.textContent = label;
    wrap.parentNode.insertBefore(p, wrap);
    return p;
  }});
  function check() {{
    wraps.forEach(function (wrap, i) {{
      hints[i].hidden = wrap.scrollWidth <= wrap.clientWidth;
    }});
  }}
  check();
  addEventListener('resize', check);
}})();
</script>
</body>
</html>
"""


# ---------------------------------------------------------------- content

BODY = {}

BODY["id"] = """
<h2>Ringkasan</h2>

<p>Codex Security itu agen <em>application security</em> dari OpenAI, masih tahap research preview. Bentuknya CLI
(<code>@openai/codex-security</code>, binary <code>cs</code> dan <code>codex-security</code>), SDK TypeScript, satu GitHub
Action, dan plugin Codex. Yang membuatnya beda dari scanner biasa: dia menalar atas source code, bukan mencocokkan
signature, jadi di kode platform internal jumlah noise-nya jauh lebih sedikit.</p>

<p>Tapi bagian yang benar-benar berguna hari ini lebih sempit dari itu. <code>validate</code>, <code>patch</code>, dan
<code>verify-fix</code> menerima temuan sebagai teks biasa atau path file, jadi temuan dari GitLab SAST/DAST bisa
diserahkan ke agen tanpa menjalankan scanner Codex Security sama sekali. Itu yang membuat urutannya berubah:
backlog temuan yang sudah ada di GitLab adalah masalah mendesak, sedangkan scanning untuk temuan baru bisa menyusul
setelah loop perbaikannya dipercaya.</p>

<div class="note">
<p>Prioritasnya fix-first. Ambil temuan yang sudah dilaporkan, nilai dulu, baru patch. Scanning untuk temuan yang belum
pernah dilaporkan siapa pun tetap penting, tapi dia bergantung pada dua hal yang belum terbukti: alias gateway yang
Responses-native dan model di belakangnya yang sanggup mengikuti schema. Keduanya harus ditutup lebih dulu.</p>
</div>

<h2>Dua pekerjaan yang berbeda</h2>

<p>Dua hal ini gampang dicampur, dan mencampurnya bikin rencana kerja melenceng berminggu-minggu: satu pekerjaan
memindai repo untuk mencari kerentanan yang belum pernah dilaporkan, satu lagi menilai dan memperbaiki temuan yang
sudah dilaporkan orang lain. Yang kedua tidak butuh yang pertama jalan.</p>

@@TWO_JOBS@@

<h2>Peta kemampuan CLI</h2>

<p>Ada @@CMD_COUNT@@ entri perintah yang relevan. Empat teratas yang dipakai di alur fix-first, sisanya operasi
workbench atas hasil yang sudah tersimpan.</p>

@@COMMANDS@@

<h2>Alur fix-first</h2>

<ol>
<li>Ambil temuan dari sumber mana pun. GitLab SAST/DAST, vulnerability report, GitHub code scanning, Sonar, Snyk,
Semgrep, semuanya bisa.</li>
<li>Tulis satu statement per temuan yang menyebut rule, lokasi, dan apa yang terlihat, misalnya
<code>[sast 101, severity high] SQL injection in report filter at src/reports/query.py:42</code>.</li>
<li><code>validate</code> dulu. Read-only: tidak build, tidak menjalankan test, tidak mengeksekusi aplikasi, tidak
menghubungi service. Gate langkah berikutnya di verdict-nya.</li>
<li><code>patch --create-pr --assess-patch-risk</code> cuma untuk temuan yang lolos validate.</li>
<li><code>verify-fix</code> kalau perbaikannya sudah landing dan butuh pembacaan independen.</li>
</ol>

<p>Jaga assess dan patch sebagai dua tahap yang bisa direview orang. Validate biayanya cuma model call; patch
menyentuh branch. Yang memutuskan apa yang di-patch tetap manusia.</p>

@@FLOW@@

<h2>Fakta yang menentukan desain</h2>

<ul>
<li><code>validate</code> tidak punya <code>--json</code>. Supaya output-nya bisa digate mesin, paksa struktur dengan
<code>--output-schema</code> plus satu JSON Schema kecil. Kalau output model tidak sesuai schema, command keluar dengan
code 2 dan tidak menulis apa pun. Tanpa ini pipeline tidak bisa memutuskan secara mekanis, cuma bisa menebak.</li>
<li><code>patch</code> mengembalikan <code>verified</code>, <code>no_change</code>, <code>blocked</code>, atau
<code>failed</code>. Hanya hasil <code>verified</code> yang di-commit. <code>SANDBOX_UNAVAILABLE</code> dan
<code>NO_PATCH_APPLIED</code> itu kejadian operasional, bukan penilaian keamanan. Perubahan file saja juga bukan bukti
perbaikannya benar.</li>
<li>Patching temuan yang kita suplai butuh working tree bersih. Kerjakan di direktori temp di luar checkout dan copy
artefaknya setelah proses patch selesai. Kalau file yang mau di-patch sudah punya edit lokal, CLI-nya meninggalkan
patch di working tree buat kita review, bukan mempublish-nya.</li>
<li><code>--create-pr</code> membuka draft PR atau MR lewat <code>gh</code> atau <code>glab</code>, dan tidak pernah
merge. Kalau push-nya gagal, CLI mencetak perintah <code>patch --resume-pr BRANCH</code> untuk mengulang dari checkout
yang sama.</li>
<li>Exit code: @@EXITS_INLINE@@. Gate yang menganggap setiap non-zero sebagai temuan akan melaporkan error sebagai
kerentanan.</li>
</ul>

@@EXITS@@

<ul>
<li><code>--provider</code> itu enum tertutup (<code>openai</code>, <code>openrouter</code>, <code>fireworks</code>,
<code>amazon-bedrock</code>, plus satu jalur cheaper-inference). Tidak ada opsi OpenAI-compatible generik, jadi gateway
self-hosted hanya bisa dijangkau lewat override config Codex native.</li>
<li>Routing inference lewat gateway sendiri tidak memberi entitlement. Run yang memakai inference OpenAI tetap butuh
akses Codex Security di akun pemilik key-nya.</li>
<li>Supplied-issue patching butuh tree yang bersih, dan artefak GitLab harus berada di dalam direktori project. Dua
batasan itu bertabrakan, jadi urutannya harus: kerja di luar checkout, patch dulu, baru copy artefak masuk.</li>
</ul>

<h2>Batasan yang jangan diklaim</h2>

<ul>
<li>Jangan pernah menjanjikan auto-fix untuk DAST. <code>validate</code> menalar dari bukti di source dan tidak
menjalankan aplikasi, jadi temuan runtime tanpa lokasi source tidak bisa dinilai sampai ada orang yang memetakan
endpoint-nya ke handler. Validasi dinamis memang ada lewat <code>--validation-prompt-file</code>, lengkap dengan setup,
target yang diizinkan, hasil yang diharapkan, dan cleanup, tapi itu proyek sendiri.</li>
<li><code>--max-cost</code> itu guardrail estimasi, bukan batas tagihan. Request yang sudah jalan bisa melewatinya.</li>
<li><code>--external-sandbox</code> mematikan enforcement filesystem dan network milik agennya sendiri. Pakai hanya di
dalam container yang menyediakan isolasi itu, jangan sebagai jalan pintas untuk runner yang tidak bisa sandbox.</li>
<li>Sebagian kelas kerentanan dan protected finding butuh Trusted Access for Cyber. Cek dulu sebelum menjanjikan
cakupannya, jangan setelah.</li>
<li>Research preview: pin versi CLI-nya secara sadar, jangan ikut latest. Setiap bump, tes ulang autentikasi, artefak,
dan ingest laporan. Versi yang dipublish bergerak lebih cepat dari contoh di dokumentasi vendornya sendiri.</li>
<li>HTTP 200 di <code>/responses</code> tidak membuktikan apa pun soal route gateway. Deployment LiteLLM yang bridged
menjawab path itu dan membuang field khusus Responses, termasuk deklarasi tool, dan gejalanya muncul sebagai kegagalan
yang sulit dijelaskan di tengah run.</li>
<li>Baca coverage dan exclusion sebelum menyebut sesuatu bersih. Selesai bukan berarti tersertifikasi, dan diff scan
tidak bilang apa pun soal sisa repo di luar diff itu.</li>
</ul>

<h2>Menyambung lewat gateway self-hosted</h2>

<p>Agennya jalan dari Codex home yang terisolasi, jadi provider custom harus didefinisikan di dalamnya. Taruh
setting-nya di file profile yang namanya sama dengan nama profile-nya, lalu pilih dengan
<code>--codex "profile='&lt;profile&gt;'"</code>.</p>

<pre><code># $CODEX_HOME/&lt;profile&gt;.config.toml
model = "&lt;alias yang diekspos gateway&gt;"
model_reasoning_effort = "high"
model_provider = "&lt;provider-id&gt;"

[model_providers.&lt;provider-id&gt;]
name = "&lt;nama tampilan&gt;"
base_url = "https://&lt;gateway&gt;/v1"
wire_api = "responses"           # wajib; agennya bicara lewat Responses API
env_key = "&lt;ENV_VAR_YANG_ISI_KEY&gt;"
requires_openai_auth = false     # jangan pernah coba auth akun ChatGPT atau OpenAI</code></pre>

<p>Route-nya harus Responses-native. Deployment tanpa konfigurasi Responses native akan menjembatani
<code>/v1/responses</code> lewat <code>/v1/chat/completions</code>, mengonversi request-nya, lalu mengaproksimasi atau
membuang field khusus Responses. Verifikasi deployment-nya, bukan route-nya:</p>

<pre><code>curl -s "$BASE/model/info" -H "Authorization: Bearer $ADMIN_KEY" \\
| jq '.data[] | {name: .model_name, model: .litellm_params.model,
                 endpoints: .model_info.supported_endpoints}'</code></pre>

<p><code>/v1/responses</code> harus muncul di <code>model_info.supported_endpoints</code>. Opt-in itu dibaca per
deployment, tidak tergantung prefix provider, dan berlaku untuk request baru tanpa restart. Untuk provider native
custom, <code>--auth auto</code> dan <code>--auth api-key</code> memakai environment variable yang disebut
<code>model_providers.&lt;id&gt;.env_key</code>, sedangkan <code>--auth chatgpt</code> memilih auth akun tersimpan dan
mengabaikan provider key, jadi provider yang butuh key-nya sendiri tidak bisa memakai opsi itu.</p>

<h2>Wiring ke GitLab CI</h2>

<p>Pisahkan kredensial, dan jangan biarkan satu job bisa membaca secret job lain. Tiga secret, tiga scope:</p>

@@CREDS@@

<ul>
<li>Tiap secret disalin ke shell variable, yang asli di-<code>unset</code>, lalu agen dijalankan dengan
<code>env -i</code> plus environment minimal yang eksplisit (<code>PATH</code>, <code>HOME</code>, <code>LANG</code>,
<code>CI</code>, <code>CI_PROJECT_DIR</code>, <code>CODEX_HOME</code>, <code>CODEX_SECURITY_STATE_DIR</code>, dan key
provider-nya). Agen menjalankan command yang dikontrol repo dan tidak boleh mewarisi environment job.</li>
<li>Seluruh run di luar checkout (<code>WORK_DIR=/tmp/...</code>), hasilnya di-copy masuk ke direktori project di akhir.
Menulis file kerja di bawah <code>$CI_PROJECT_DIR</code> mengotori tree dan bikin <code>patch</code> menolak jalan.</li>
<li>Job-nya butuh <code>git</code>, <code>python3</code>, <code>ripgrep</code>, <code>util-linux</code> untuk cek sandbox,
<code>curl</code>, dan <code>glab</code> untuk <code>--create-pr</code>. Bake semuanya di image runner yang di-pin,
jangan install saat job jalan.</li>
<li>Gagalkan lebih awal dan berisik: <code>unshare -Ur true</code> (agennya sandbox sendiri pakai user namespace), lalu
<code>--version</code>, lalu satu pass <code>--dry-run --verbose</code> yang mencetak provider, model, dan effort yang
resolve tanpa memulai run berbayar.</li>
<li><code>--setup-git-credential-helper</code> di <code>glab auth login</code> bikin push branch-nya memakai token yang
sama. <code>CI_JOB_TOKEN</code> tidak bisa membuat merge request, jadi jalur tulisnya perlu project access token
khusus.</li>
<li>Findings API GitLab butuh <code>scope=all</code>, karena default-nya cuma temuan dismissed. Endpoint vulnerabilities
dan vulnerability_findings ditandai deprecated ke arah GraphQL, dan responsnya dipaginasi (20 per halaman secara
default), jadi backlog besar butuh paging sendiri.</li>
</ul>

<h2>Temuan dari mana di GitLab</h2>

@@FINDING_SOURCES@@

<p>Payload scanner-nya sendiri datang sebagai string JSON di <code>finding.raw_metadata</code>. Untuk SAST, lokasinya
ada di sana sebagai <code>location.file</code> dan <code>location.start_line</code>. Lokasi DAST mendeskripsikan request
(<code>hostname</code>, <code>path</code>, <code>method</code>, <code>param</code>), dan itu sebabnya temuan DAST tidak
bisa langsung diserahkan ke <code>validate</code>: tidak ada baris source yang bisa dinilai.</p>

<h2>Risiko terbuka</h2>

<p>Semua di bawah ini datang dari dokumentasi resmi OpenAI, LiteLLM, dan GitLab, bukan dari hasil eksekusi. Belum ada
satu pun yang pernah dijalankan di runner sungguhan. Ada @@RISK_COUNT@@ item yang harus ditutup sebelum ini dipakai
serius, dan yang pertama sengaja ditaruh paling atas karena itu titik paling mungkin desainnya perlu diubah.</p>

@@RISKS@@

<h2>Status verifikasi</h2>

<p>Yang sudah benar-benar diuji di mesin ini:</p>

<ul>
<li>Pipeline CI-nya parse sebagai YAML, dan setiap blok shell di dalamnya lolos <code>bash -n</code>.</li>
<li>Tiga script helper dijalankan terhadap payload GitLab sintetis: temuan SAST dengan lokasi di
<code>raw_metadata</code> berubah jadi statement, temuan DAST tanpa lokasi masuk daftar triage, temuan dengan metadata
rusak ditangani tanpa crash, verdict <code>confirmed</code> menghasilkan kandidat patch, dan verdict
<code>not_applicable</code> tidak.</li>
<li>Command yang dihasilkan script-nya juga lolos <code>bash -n</code>, termasuk <code>patch --create-pr</code> per
temuan yang dikonfirmasi.</li>
</ul>

<p>Yang belum, dan ini penting: pipeline-nya belum pernah jalan di runner GitLab milik siapa pun, belum pernah
menyentuh alias gateway sungguhan, dan kualitas perbaikannya belum pernah dibandingkan dengan fix buatan manusia.
Anggap bagian gateway dan CI di halaman ini sebagai rancangan yang sudah divalidasi sintaks, bukan resep yang sudah
terbukti.</p>

<h2>Sumber</h2>

<ul>
@@SOURCE_LIST@@
</ul>
"""

BODY["en"] = """
<h2>Summary</h2>

<p>Codex Security is OpenAI's application security agent, still in research preview. It ships as a CLI
(<code>@openai/codex-security</code>, binaries <code>cs</code> and <code>codex-security</code>), a TypeScript SDK, one
GitHub Action, and a Codex plugin. What separates it from an ordinary scanner: it reasons over source rather than
matching signatures, so on internal platform code it produces far less noise.</p>

<p>The genuinely useful part today is narrower than that. <code>validate</code>, <code>patch</code> and
<code>verify-fix</code> accept a finding as literal text or a file path, so a GitLab SAST or DAST finding can be handed
to the agent without running Codex Security's own scanner at all. That is what flips the order of work: the backlog
GitLab already produced is the immediate problem, while scanning for unreported vulnerabilities can wait until the fix
loop is trusted.</p>

<div class="note">
<p>Fix-first. Take findings that were already reported, assess them, then patch. Scanning for vulnerabilities nobody
has reported still matters, but it depends on two things that are not proven yet: a Responses-native gateway alias and
a model behind it that can honour a schema. Both have to close first.</p>
</div>

<h2>Two jobs that are easy to confuse</h2>

<p>Mixing these two up costs weeks of work in the wrong direction: one job scans a repository for vulnerabilities
nobody has reported, the other assesses and fixes a finding somebody already reported. The second one does not need the
first one to run.</p>

@@TWO_JOBS@@

<h2>CLI capability map</h2>

<p>@@CMD_COUNT@@ commands matter here. The top four carry the fix-first flow; the rest are workbench operations on
saved results.</p>

@@COMMANDS@@

<h2>The fix-first flow</h2>

<ol>
<li>Take the finding from any source. GitLab SAST/DAST, the vulnerability report, GitHub code scanning, Sonar, Snyk,
Semgrep, all of them work.</li>
<li>Write one statement per finding naming the rule, the location and the observation, for example
<code>[sast 101, severity high] SQL injection in report filter at src/reports/query.py:42</code>.</li>
<li><code>validate</code> first. Read-only: it does not build, run tests, execute the application, or contact
services. Gate the next step on its verdict.</li>
<li><code>patch --create-pr --assess-patch-risk</code> only for the findings that validated.</li>
<li><code>verify-fix</code> when a fix already landed and you want an independent read.</li>
</ol>

<p>Keep assess and patch as two reviewable stages. Validation costs model calls and nothing else; patching touches a
branch. A person still decides what gets patched.</p>

@@FLOW@@

<h2>Facts that decide the design</h2>

<ul>
<li><code>validate</code> has no <code>--json</code>. To gate it mechanically, force structure with
<code>--output-schema</code> and a small JSON Schema. If the model's output does not match the schema the command exits
2 and writes nothing. Without this a pipeline can only guess.</li>
<li><code>patch</code> returns <code>verified</code>, <code>no_change</code>, <code>blocked</code> or
<code>failed</code>. Only <code>verified</code> results are committed. <code>SANDBOX_UNAVAILABLE</code> and
<code>NO_PATCH_APPLIED</code> are operational outcomes, not security judgements, and file changes alone are not proof
of a fix.</li>
<li>Patching a supplied finding requires a clean tree. Work in a temp directory outside the checkout and copy artifacts
out only after patching finishes. If a selected file already has local edits, the CLI leaves the patch in the working
tree for review instead of publishing it.</li>
<li><code>--create-pr</code> opens a draft PR or MR through <code>gh</code> or <code>glab</code> and never merges. A
failed push prints a <code>patch --resume-pr BRANCH</code> command to rerun from the same checkout.</li>
<li>Exit codes: @@EXITS_INLINE@@. A gate that treats every non-zero as a finding misreports errors as
vulnerabilities.</li>
</ul>

@@EXITS@@

<ul>
<li><code>--provider</code> is a closed enum (<code>openai</code>, <code>openrouter</code>, <code>fireworks</code>,
<code>amazon-bedrock</code>, plus one cheaper-inference path). There is no generic OpenAI-compatible option, so a
self-hosted gateway is reachable only through native Codex config overrides.</li>
<li>Routing inference through your own gateway does not confer entitlement. Runs that use OpenAI inference still need
Codex Security access on the account behind the key.</li>
<li>Supplied-issue patching needs a clean tree, while GitLab artifacts have to live inside the project directory. Those
two constraints collide, so the order is: work outside the checkout, patch first, copy artifacts in afterwards.</li>
</ul>

<h2>Limits not to promise</h2>

<ul>
<li>Never promise DAST auto-fix. <code>validate</code> reasons over source evidence and does not run the application,
so a runtime finding with no source location cannot be assessed until somebody maps the endpoint to its handler.
Dynamic validation exists through <code>--validation-prompt-file</code>, with setup, authorized targets, expected
results and cleanup, but treat that as its own project.</li>
<li><code>--max-cost</code> is an estimated guardrail, not a billing cap. In-flight requests can exceed it.</li>
<li><code>--external-sandbox</code> disables the agent's own filesystem and network enforcement. Only use it inside a
container that provides that isolation, never as a workaround for a runner that cannot sandbox.</li>
<li>Some vulnerability classes and protected findings need Trusted Access for Cyber. Check before promising coverage,
not after.</li>
<li>Research preview: pin the CLI version deliberately instead of tracking latest, and retest authentication,
artifacts and report ingestion on every bump. The published version moves faster than the vendor's own examples.</li>
<li>A 200 on <code>/responses</code> proves nothing about a gateway route. A bridged LiteLLM deployment answers that
path and drops Responses-only fields, including tool declarations, which surfaces as an unexplained failure mid-run.</li>
<li>Read coverage and exclusions before calling anything clean. Completion is not certification, and a diff scan says
nothing about the rest of the repository.</li>
</ul>

<h2>Reaching a self-hosted gateway</h2>

<p>The agent runs from an isolated Codex home, so a custom provider has to be defined inside it. Put the settings in a
profile file named after the profile, then select it with <code>--codex "profile='&lt;profile&gt;'"</code>.</p>

<pre><code># $CODEX_HOME/&lt;profile&gt;.config.toml
model = "&lt;alias the gateway exposes&gt;"
model_reasoning_effort = "high"
model_provider = "&lt;provider-id&gt;"

[model_providers.&lt;provider-id&gt;]
name = "&lt;display name&gt;"
base_url = "https://&lt;gateway&gt;/v1"
wire_api = "responses"           # required; the agent speaks the Responses API
env_key = "&lt;ENV_VAR_HOLDING_THE_KEY&gt;"
requires_openai_auth = false     # never attempt ChatGPT or OpenAI account auth</code></pre>

<p>The route must be Responses-native. A deployment with no native Responses configuration bridges
<code>/v1/responses</code> through <code>/v1/chat/completions</code>, converting the request and approximating or
dropping Responses-only fields. Verify the deployment, not the route:</p>

<pre><code>curl -s "$BASE/model/info" -H "Authorization: Bearer $ADMIN_KEY" \\
| jq '.data[] | {name: .model_name, model: .litellm_params.model,
                 endpoints: .model_info.supported_endpoints}'</code></pre>

<p><code>/v1/responses</code> must appear in <code>model_info.supported_endpoints</code>. That opt-in is read per
deployment, is independent of the provider prefix, and applies to new requests without a restart. For a custom native
provider, <code>--auth auto</code> and <code>--auth api-key</code> use the environment variable named by
<code>model_providers.&lt;id&gt;.env_key</code>, while <code>--auth chatgpt</code> selects stored account auth and omits
the provider key, so a provider that needs its own key cannot use it.</p>

<h2>Wiring into GitLab CI</h2>

<p>Split credentials so that no job can read another job's secret. Three secrets, three scopes:</p>

@@CREDS@@

<ul>
<li>Copy each secret into a shell variable, <code>unset</code> the original, and launch the agent with
<code>env -i</code> plus an explicit minimal environment (<code>PATH</code>, <code>HOME</code>, <code>LANG</code>,
<code>CI</code>, <code>CI_PROJECT_DIR</code>, <code>CODEX_HOME</code>, <code>CODEX_SECURITY_STATE_DIR</code>, and the
provider key). The agent runs repository-controlled commands and must not inherit the job environment.</li>
<li>Keep the whole run outside the checkout (<code>WORK_DIR=/tmp/...</code>) and copy results into the project
directory at the end. Work files under <code>$CI_PROJECT_DIR</code> dirty the tree and make <code>patch</code> refuse
to run.</li>
<li>The job needs <code>git</code>, <code>python3</code>, <code>ripgrep</code>, <code>util-linux</code> for the sandbox
check, <code>curl</code>, and <code>glab</code> for <code>--create-pr</code>. Bake them into a pinned runner image
instead of installing at job time.</li>
<li>Fail early and loudly: <code>unshare -Ur true</code> (the agent sandboxes itself with user namespaces), then
<code>--version</code>, then a <code>--dry-run --verbose</code> pass that prints the resolved provider, model and
effort without starting a paid run.</li>
<li><code>--setup-git-credential-helper</code> on <code>glab auth login</code> lets the branch push reuse the same
token. <code>CI_JOB_TOKEN</code> cannot create a merge request, so the write path needs its own project access
token.</li>
<li>GitLab's findings API needs <code>scope=all</code>, because it defaults to dismissed findings only. The
vulnerabilities and vulnerability-findings endpoints are marked deprecated in favour of GraphQL, and responses are
paginated (20 by default), so a large backlog needs its own paging.</li>
</ul>

<h2>Running it under a CI time budget</h2>

<p>A GitLab job cannot run forever, and a timeout is a hard kill rather than a pause
button. Nothing in the agent resumes a batch, so the design has to make the kill
both unnecessary and cheap: keep the work unit small, let the loop own its own
clock, and publish every finding the moment it verifies.</p>

<p>The inversion that makes this work is boring and easy to get wrong: <strong>the
script's budget has to expire before the job timeout, which has to expire before
the project maximum.</strong> A 45 minute budget inside a 50 minute job inside a
60 minute project ceiling means the pipeline stops itself at a point it chose,
prints what it did, and leaves the rest for the next run. GitLab never gets to
kill a push that is in flight.</p>

<p>Every iteration starts from a clean clone at the base commit, because the patch
command refuses to run against a dirty tree. One finding, one call, one
decision:</p>

@@LOOP@@

<p>Every outcome is classified, because an exit code is not a security judgement.
Exit 124 is our own ceiling firing, exit 2 is a runtime error, and a clean exit
with <code>no_change</code> is a decision the agent made. Only
<code>verified</code> is published, and only the infrastructure classes are
retried. @@OUTCOME_COUNT@@ statuses, three different responses:</p>

@@OUTCOMES@@

<h3>Who holds the credential</h3>

<p>The agent is the least trustworthy process in the pipeline, because it runs
repository-controlled commands. So it gets no repository credential at all: it is
launched with <code>env -i</code>, a HOME that holds no glab or git configuration,
and exactly one secret, the model key. A separate publisher step holds the only
<code>write_repository</code> token, stages exactly the files the CLI reported as
changed, commits, pushes a branch named after the finding, and opens a draft
MR.</p>

<p>That split pays for itself twice. The agent cannot leak a credential it never
had, and because the branch name comes from the finding id, the remote becomes a
second idempotency source: a run that lost its progress file still refuses to
publish a finding that already has a branch. It is also why this pipeline does not
use <code>patch --create-pr</code>, even though the command supports it: that flag
puts the write credential inside the agent's own process, which is the one place it
should never be.</p>

<h3>Two traps worth knowing before you start</h3>

<p>A loop that always starts from the same ordered list starves its own tail. If
the budget runs out at finding seven of thirty, the next run has to continue at
eight. That comes free from a stable ordering plus a recorded marker, but only if
the marker is consulted before the agent is called.</p>

<p>The other trap is social. One change per merge request is excellent for review,
while thirty draft merge requests are thirty notifications. Run the first week
without publishing, read the diffs as artifacts, and let the team agree the volume
is worth the review time before the notifications start.</p>

<h2>Proof of concept</h2>

<p>Four steps, each with an exit criterion that has to hold before the next one
starts. The order matters: sizing a budget before measuring anything is how a
pilot turns into a story about timeouts.</p>

@@POC@@

<p>Deliberately out of scope for the pilot:</p>

<ul>
@@POC_DONT@@
</ul>

<h2>Where findings come from in GitLab</h2>

@@FINDING_SOURCES@@

<p>The scanner's own payload arrives as a JSON <em>string</em> in <code>finding.raw_metadata</code>. For SAST the
location lives there as <code>location.file</code> and <code>location.start_line</code>. DAST locations describe a
request (<code>hostname</code>, <code>path</code>, <code>method</code>, <code>param</code>), which is why a DAST
finding cannot go straight into <code>validate</code>: there is no source line to reason about.</p>

<h2>Open risks</h2>

<p>Everything below comes from OpenAI's, LiteLLM's and GitLab's published documentation rather than from execution.
None of it has run on a real runner yet. There are @@RISK_COUNT@@ items to close before this is taken seriously, and
the first one is deliberately at the top because it is the most likely place the design has to change.</p>

@@RISKS@@

<h2>Verification status</h2>

<p>What was actually exercised on this machine:</p>

<ul>
<li>The CI pipeline parses as YAML, and every shell block inside it passes <code>bash -n</code>.</li>
<li>The three helper scripts ran against synthetic GitLab payloads: a SAST finding with a location in
<code>raw_metadata</code> became a statement, a DAST finding without one went to the triage list, a finding with broken
metadata was handled without crashing, a <code>confirmed</code> verdict produced a patch candidate, and
<code>not_applicable</code> did not.</li>
<li>The time-budgeted loops ran end to end against stub binaries and a real local git remote, 36 checks: a budget stop
before any call, a killed call classified as <code>timeout</code>, one retry for infrastructure only, branch-based
idempotency proven with the progress file deleted, and the write token proven absent from the agent's environment.</li>
<li>Every shell block in the pipeline passes <code>bash -n</code>, the include parses as YAML, and the report script
exits 2 when a published finding carries no merge request link.</li>
</ul>

<p>What has not happened, and this matters: the pipeline has never run on anyone's GitLab runner, has never touched a
real gateway alias, and its fix quality has never been compared against human-authored fixes. The timings in the budget
variables are placeholders, not measurements. Treat the gateway, CI and budget sections as a harness-tested design, not
a proven recipe.</p>

<h2>Sources</h2>

<ul>
@@SOURCE_LIST@@
</ul>
"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "assets").mkdir(parents=True, exist_ok=True)
    langs = (("en", "index.html"),)
    wanted = {name for _, name in langs}
    for p in OUT.glob("index*.html"):
        if p.name not in wanted:
            p.unlink()
            print("removed stale", p)
    for lang, name in langs:
        (OUT / name).write_text(build(lang), encoding="utf-8")
        print("wrote", OUT / name)
    print("tables rendered from data; risk count", len(RISKS), "command count", len(COMMANDS))


if __name__ == "__main__":
    main()
