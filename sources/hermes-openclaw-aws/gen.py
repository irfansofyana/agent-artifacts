#!/usr/bin/env python3
"""Generate the bilingual (EN root, ID secondary) here.now page from one data structure.

Writes a self-contained build directory (index.html, index-id.html, assets/).
Output defaults to <repo>/sources/hermes-openclaw-aws/build so nothing is
committed; override with the HERMES_OPENCLAW_AWS_OUT environment variable.
The page ships the Scandinavian monochrome system: see assets/site.css.
"""
import html
import os
import pathlib
import shutil

HERE = pathlib.Path(__file__).resolve().parent          # sources/hermes-openclaw-aws
REPO_ROOT = HERE.parents[1]                             # repository root
DEFAULT_OUT = REPO_ROOT / "sources" / "hermes-openclaw-aws" / "build"
OUT = pathlib.Path(os.environ.get("HERMES_OPENCLAW_AWS_OUT", DEFAULT_OUT))

# Inter is self-hosted next to the page. Resolved from the publishing skill's
# vendored copy (no absolute path in code); override with HERMES_INTER_FONT.
FONT_SRC = pathlib.Path(os.environ.get(
    "HERMES_INTER_FONT",
    os.path.expanduser(
        "~/.hermes/skills/productivity/herenow-artifact-publisher/"
        "root-index/assets/inter-latin-wght-normal.woff2"),
))

SLUG = "cosmic-desert-y4tm"
REGISTRY = "https://artifacts.irfansp.dev/"

TITLE = {
    "en": "Running Hermes and OpenClaw on AWS",
    "id": "Menjalankan Hermes dan OpenClaw di AWS",
}
LEDE = {
    "en": "AWS now ships first-party material for both agents: a campaign page, a Lightsail quick start, one-click CloudFormation samples, Marketplace listings and four Builder Center write-ups. The community layer is thin, and only one Terraform module looks maintained.",
    "id": "AWS sekarang menyediakan materi first-party untuk kedua agent: halaman kampanye, quick start Lightsail, sample CloudFormation sekali klik, listing Marketplace, dan empat artikel Builder Center. Lapisan komunitasnya tipis, dan cuma satu modul Terraform yang kelihatan dirawat.",
}
EYEBROW = {"en": "AWS · agents · source-checked 18 Nov 2026", "id": "AWS · agent · dicek 18 Nov 2026"}
SKIP = {"en": "Skip to content", "id": "Lewati ke konten"}

LABEL = {
    "en": {"lang_name": "English", "other_name": "Indonesian", "other_href": "index-id.html",
           "table_region": "Scrollable table", "hint": "Swipe sideways to see all columns",
           "sources": "Sources", "published": "Published",
           "footer": "Written by Kai (Hermes Agent) · checked against live AWS and repository sources on 18 November 2026 · site published with here.now"},
    "id": {"lang_name": "Indonesia", "other_name": "English", "other_href": "index.html",
           "table_region": "Tabel yang bisa di-scroll", "hint": "Geser ke samping untuk lihat semua kolom",
           "sources": "Sumber", "published": "Dipublikasikan",
           "footer": "Ditulis oleh Kai (Hermes Agent) · dicek langsung ke sumber AWS dan repo pada 18 November 2026 · situs dipublikasikan lewat here.now"},
}

# ---------------------------------------------------------------- shared data

SAMPLES = [
    {
        "url": "https://github.com/aws-samples/sample-OpenClaw-on-AWS-with-Bedrock",
        "name": "aws-samples/sample-OpenClaw-on-AWS-with-Bedrock",
        "chips": ["AWS sample", "MIT-0", "418★"],
        "en": "One CloudFormation stack that stands up OpenClaw on a Graviton instance with Bedrock for model access, SSM Session Manager instead of open SSH, VPC endpoints and CloudTrail. The README claims about 8 minutes to deploy and prices it from roughly $30/month. Messaging plugins arrive pre-installed. Launch buttons cover us-west-2, us-east-1, eu-west-1 and ap-northeast-1.",
        "id": "Satu stack CloudFormation yang menaikkan OpenClaw di instance Graviton, pakai Bedrock untuk akses model, SSM Session Manager sebagai ganti SSH terbuka, VPC endpoints, dan CloudTrail. README-nya bilang deploy sekitar 8 menit dan mulai dari sekitar $30/bulan. Plugin messaging sudah terpasang. Tombol launch-nya mencakup us-west-2, us-east-1, eu-west-1, dan ap-northeast-1.",
        "notes_en": [
            "Bedrock model access is handled by the stack, so no API keys live on the instance.",
            "Access is through SSM, so no inbound ports and no SSH key.",
            "Caveat: the one-click template sits in a single S3 bucket, so any other region means uploading the template yourself.",
        ],
        "notes_id": [
            "Akses model Bedrock diurus stack-nya, jadi tidak ada API key di instance.",
            "Aksesnya lewat SSM, jadi tanpa inbound port dan tanpa SSH key.",
            "Catatan: template sekali klik-nya ada di satu bucket S3, jadi untuk region lain kamu harus upload template-nya sendiri.",
        ],
    },
    {
        "url": "https://github.com/aws-samples/sample-host-hermesagent-on-amazon-bedrock-agentcore",
        "name": "aws-samples/sample-host-hermesagent-on-amazon-bedrock-agentcore",
        "chips": ["AWS sample", "MIT-0", "45★"],
        "en": "The most architecturally interesting option for Hermes: per-user Firecracker microVMs on AgentCore Runtime, 9 CDK stacks, API Gateway plus a router Lambda for inbound webhooks, and an ECS Fargate gateway for channels that need long-lived connections. State is S3-backed so memory and sessions survive the microVM.",
        "id": "Opsi paling menarik secara arsitektur untuk Hermes: Firecracker microVM per user di AgentCore Runtime, 9 stack CDK, API Gateway plus Lambda router untuk webhook masuk, dan gateway ECS Fargate untuk channel yang butuh koneksi panjang. State-nya di S3, jadi memory dan session tetap hidup meski microVM-nya mati.",
        "notes_en": [
            "The integration is a monkey-patch that swaps anthropic.Anthropic for anthropic.AnthropicBedrock, so all inference goes through Bedrock with SigV4 and IAM while upstream Hermes source stays unmodified.",
            "Channels: Telegram, Slack, Discord and Feishu over webhook; WeChat through the Fargate gateway.",
            "Caveat: region-gated, see the Jakarta section.",
        ],
        "notes_id": [
            "Integrasinya berupa monkey-patch yang menukar anthropic.Anthropic dengan anthropic.AnthropicBedrock, jadi semua inference lewat Bedrock dengan SigV4 dan IAM, sementara source Hermes di upstream tidak diubah.",
            "Channel: Telegram, Slack, Discord, dan Feishu via webhook; WeChat lewat gateway Fargate.",
            "Catatan: terikat region, lihat bagian Jakarta.",
        ],
    },
    {
        "url": "https://github.com/JiaDe-Wu/sample-hermes-agent-on-aws-with-bedrock",
        "name": "JiaDe-Wu/sample-hermes-agent-on-aws-with-bedrock",
        "chips": ["MIT", "19★"],
        "en": "The sample the Hermes docs themselves link to: CloudFormation creates the VPC, IAM role, EC2 instance and Bedrock configuration in one click. Its native Bedrock provider work has been merged upstream, so the deployment installs from the official PyPI release rather than a fork. Shortest path from zero to a working Hermes on EC2.",
        "id": "Sample yang ditautkan langsung oleh dokumentasi Hermes: CloudFormation bikin VPC, IAM role, instance EC2, dan konfigurasi Bedrock dalam satu klik. Kerja provider Bedrock native-nya sudah di-merge ke upstream, jadi deploy-nya install dari rilis PyPI resmi, bukan fork. Jalur terpendek dari nol ke Hermes yang jalan di EC2.",
        "notes_en": [],
        "notes_id": [],
    },
]

EXTRA_SAMPLE = {
    "en": 'There is also <a href="https://github.com/aws-samples/sample-hermes-agents-on-agentcore">aws-samples/sample-hermes-agents-on-agentcore</a>, younger and thinner, useful if you want more than one Hermes agent inside the same AgentCore account.',
    "id": 'Ada juga <a href="https://github.com/aws-samples/sample-hermes-agents-on-agentcore">aws-samples/sample-hermes-agents-on-agentcore</a>, lebih baru dan lebih tipis, berguna kalau kamu mau lebih dari satu Hermes agent di akun AgentCore yang sama.',
}

ARTICLES = [
    {"url": "https://builder.aws.com/content/38mhAVkwQuKrVJdfAwLImOok2UL",
     "en": "<strong>Deploy OpenClaw on AWS: choose the right options for your AI workload</strong> — the AWS-side comparison of Lightsail, EC2, Bedrock AgentCore and EKS in one table. Start here.",
     "id": "<strong>Deploy OpenClaw on AWS: choose the right options for your AI workload</strong> — perbandingan versi AWS untuk Lightsail, EC2, Bedrock AgentCore, dan EKS dalam satu tabel. Mulai dari sini."},
    {"url": "https://builder.aws.com/content/3CQFzc91nM9sGkfHRbpjo4eXojf",
     "en": "<strong>Deploying OpenClaw on Amazon EC2</strong> — a developer walkthrough of the single-template deployment, roughly 15 minutes, wired to Claude models.",
     "id": "<strong>Deploying OpenClaw on Amazon EC2</strong> — walkthrough developer untuk deploy satu template, sekitar 15 menit, disambungkan ke model Claude."},
    {"url": "https://builder.aws.com/content/3Fq2MlB9BRdm3UY5DjJbqhcTIQ9",
     "en": "<strong>Deploying OpenClaw in a Kubernetes Sandbox</strong> — EKS with tiered runtime isolation, from standard containers through gVisor to Kata Containers, on Graviton.",
     "id": "<strong>Deploying OpenClaw in a Kubernetes Sandbox</strong> — EKS dengan isolasi runtime bertingkat, dari container biasa, gVisor, sampai Kata Containers, di Graviton."},
    {"url": "https://builder.aws.com/content/3IVkpVl1RXBb9lX2a6Q1Wy6CKfA",
     "en": "<strong>Deploying Hermes Agent on AWS</strong> — EC2 plus Bedrock, Route 53 DNS, Let's Encrypt provisioning, then checking that memory and self-written skills survive across sessions.",
     "id": "<strong>Deploying Hermes Agent on AWS</strong> — EC2 plus Bedrock, DNS Route 53, provisioning Let's Encrypt, lalu mengecek memory dan skill yang ditulis sendiri tetap ada antar sesi."},
]

TERRAFORM = [
    {"url": "https://github.com/infrahouse/terraform-aws-openclaw",
     "en": "<strong>infrahouse/terraform-aws-openclaw</strong> — Apache-2.0, the only one that reads like a real module: ALB, Cognito authentication, EFS persistence, multi-provider LLM support. 20 stars, last touched November 2026.",
     "id": "<strong>infrahouse/terraform-aws-openclaw</strong> — Apache-2.0, satu-satunya yang terasa seperti modul sungguhan: ALB, autentikasi Cognito, persistensi EFS, dukungan multi-provider LLM. 20 bintang, terakhir disentuh November 2026."},
    {"url": "https://github.com/qodex-ai/openclaw-worker",
     "en": "<strong>qodex-ai/openclaw-worker</strong> — MIT, one-command deploy with HTTPS, Route 53 DNS and encrypted S3 backups. 4 stars, September 2026.",
     "id": "<strong>qodex-ai/openclaw-worker</strong> — MIT, deploy satu perintah dengan HTTPS, DNS Route 53, dan backup S3 terenkripsi. 4 bintang, September 2026."},
    {"url": "https://github.com/janobarnard/openclaw-aws",
     "en": "<strong>janobarnard/openclaw-aws</strong> and <a href=\"https://github.com/mamonaco1973/aws-openclaw\">mamonaco1973/aws-openclaw</a> — single-author examples in Terraform, and Terraform plus Packer against Bedrock. Fine as references, not as dependencies.",
     "id": "<strong>janobarnard/openclaw-aws</strong> dan <a href=\"https://github.com/mamonaco1973/aws-openclaw\">mamonaco1973/aws-openclaw</a> — contoh satu penulis, pakai Terraform, dan Terraform plus Packer ke Bedrock. Oke sebagai referensi, bukan sebagai dependency."},
]

# ------------------------------------------------------------------ rendering


def esc(text):
    return html.escape(text, quote=False)


def table_block(headers, rows, lang, idx=0):
    head = "".join(f"<th scope=\"col\">{c[lang]}</th>" for c in headers)
    body = []
    for row in rows:
        cells = "".join(f"<td>{c[lang]}</td>" for c in row)
        body.append(f"<tr>{cells}</tr>")
    hint_id = f"tbl-hint-{idx}-{lang}"
    caption = f"<p class=\"table-hint\" id=\"{hint_id}\" hidden>{esc(LABEL[lang]['hint'])}</p>"
    return (
        f"{caption}\n<div class=\"table-wrap\" role=\"region\" tabindex=\"0\" aria-labelledby=\"{hint_id}\">"
        f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table></div>"
    )


def card_block(item, lang):
    chips = "".join(f"<span class=\"chip\">{esc(c)}</span>" for c in item["chips"])
    notes = item.get(f"notes_{lang}") or []
    note_html = ""
    if notes:
        items = "".join(f"<li>{esc(n)}</li>" for n in notes)
        note_html = f"<ul>{items}</ul>"
    return (
        "<div class=\"card\">"
        f"<h3><a href=\"{item['url']}\">{esc(item['name'])}</a></h3>"
        f"<div class=\"meta-chips\">{chips}</div>"
        f"<p>{esc(item[lang])}</p>{note_html}</div>"
    )


def list_block(entries, lang, ordered=False):
    tag = "ol" if ordered else "ul"
    body = "".join(f"<li>{esc(e[lang]) if not e.get('html') else e[lang]}</li>" for e in entries)
    return f"<{tag}>{body}</{tag}>"


def build(lang):
    s = []

    s.append("<header class=\"hero\">")
    s.append(f"<p class=\"eyebrow\">{esc(EYEBROW[lang])}</p>")
    s.append(f"<h1>{esc(TITLE[lang])}</h1>")
    s.append(f"<p class=\"lede\">{esc(LEDE[lang])}</p>")
    s.append("</header>")

    # 1. What AWS ships
    t = {"en": "What AWS itself ships", "id": "Yang disediakan AWS sendiri"}
    s.append(f"<h2 id=\"first-party\">{esc(t[lang])}</h2>")
    headers = [
        {"en": "Surface", "id": "Permukaan"},
        {"en": "What it actually is", "id": "Isinya sebenarnya"},
    ]
    rows = [
        [
            {"en": '<a href="https://aws.amazon.com/campaigns/openclawonaws/">OpenClaw on AWS campaign page</a>',
             "id": '<a href="https://aws.amazon.com/campaigns/openclawonaws/">Halaman kampanye OpenClaw on AWS</a>'},
            {"en": "AWS marketing entry point. Splits single-instance deployment into Lightsail, EC2 and EC2 Mac instances, with an enterprise contact path beside them.",
             "id": "Pintu masuk versi marketing AWS. Deploy single-instance dipisah jadi Lightsail, EC2, dan EC2 Mac, dengan jalur kontak enterprise di sebelahnya."},
        ],
        [
            {"en": '<a href="https://docs.aws.amazon.com/lightsail/latest/userguide/amazon-lightsail-quick-start-guide-openclaw.html">Lightsail quick start (AWS docs)</a>',
             "id": '<a href="https://docs.aws.amazon.com/lightsail/latest/userguide/amazon-lightsail-quick-start-guide-openclaw.html">Quick start Lightsail (dokumentasi AWS)</a>'},
            {"en": "Official tutorial that creates an OpenClaw Lightsail instance from the console. Lowest-effort path to a personal gateway.",
             "id": "Tutorial resmi yang bikin instance Lightsail berisi OpenClaw dari console. Jalur paling ringan kalau cuma butuh gateway pribadi."},
        ],
        [
            {"en": '<a href="https://aws.amazon.com/marketplace/pp/prodview-gsldfjccyzp6c">OpenClaw AMI (Marketplace)</a>',
             "id": '<a href="https://aws.amazon.com/marketplace/pp/prodview-gsldfjccyzp6c">AMI OpenClaw (Marketplace)</a>'},
            {"en": "Self-hosted OpenClaw platform as a 1-click AMI, setup UI on port 9000 of the instance. Quick EC2 test, not a repeatable deployment.",
             "id": "Platform OpenClaw self-hosted dalam bentuk AMI 1-click, UI setup-nya di port 9000 instance. Cocok buat tes EC2 cepat, bukan untuk deployment yang bisa diulang."},
        ],
        [
            {"en": '<a href="https://aws.amazon.com/marketplace/pp/prodview-2yccdxfxqc6mc">Hermes Agent — AI Assistant with Tool Use</a>',
             "id": '<a href="https://aws.amazon.com/marketplace/pp/prodview-2yccdxfxqc6mc">Hermes Agent — AI Assistant with Tool Use</a>'},
            {"en": 'Nous Research Hermes Agent packaged for Marketplace. There is a second memory-focused listing (<a href="https://aws.amazon.com/marketplace/pp/prodview-y5xgoi7s7qrh4">Self-Improving Autonomous AI Agent with Memory</a>) and a bundle with n8n on one instance (<a href="https://aws.amazon.com/marketplace/pp/prodview-4fzuhic4bbmi">Hermes AI Agent + n8n</a>).',
             "id": 'Hermes Agent dari Nous Research yang dikemas untuk Marketplace. Ada listing kedua yang fokus ke memory (<a href="https://aws.amazon.com/marketplace/pp/prodview-y5xgoi7s7qrh4">Self-Improving Autonomous AI Agent with Memory</a>) dan bundel dengan n8n di satu instance (<a href="https://aws.amazon.com/marketplace/pp/prodview-4fzuhic4bbmi">Hermes AI Agent + n8n</a>).'},
        ],
        [
            {"en": '<a href="https://hermes-agent.nousresearch.com/marketplace/aws-manager">aws-manager plugin</a>',
             "id": '<a href="https://hermes-agent.nousresearch.com/marketplace/aws-manager">plugin aws-manager</a>'},
            {"en": "Hermes Marketplace plugin that drives live AWS from inside the agent: deployments, stack status, CloudFormation outputs, S3 origins. Useful when Hermes operates the account it runs in.",
             "id": "Plugin Hermes Marketplace yang menggerakkan AWS langsung dari dalam agent: deployment, status stack, output CloudFormation, origin S3. Berguna kalau Hermes ikut mengoperasikan akun tempat dia jalan."},
        ],
    ]
    s.append(table_block(headers, rows, lang, idx=1))

    # 2. Deployment options
    t = {"en": "Deployment options, honestly compared", "id": "Opsi deployment, dibandingkan apa adanya"}
    s.append(f"<h2 id=\"options\">{esc(t[lang])}</h2>")
    headers = [
        {"en": "Option", "id": "Opsi"},
        {"en": "Best for", "id": "Paling cocok untuk"},
        {"en": "Reality check", "id": "Kenyataannya"},
    ]
    rows = [
        [
            {"en": "Lightsail", "id": "Lightsail"},
            {"en": "One personal assistant, fast", "id": "Satu asisten pribadi, cepat"},
            {"en": "Fixed instance bundle. Cheapest way to stop babysitting a VPS.",
             "id": "Bundle instance sudah tetap. Cara termurah berhenti mengurus VPS sendiri."},
        ],
        [
            {"en": "EC2 (single instance)", "id": "EC2 (single instance)"},
            {"en": "Personal or small-team gateway with real IAM", "id": "Gateway pribadi atau tim kecil dengan IAM sungguhan"},
            {"en": "Where most people actually land. Attach an IAM role, run it under systemd or Docker, keep it off the public internet behind SSM or a tailnet.",
             "id": "Tempat kebanyakan orang berakhir. Pasang IAM role, jalankan di bawah systemd atau Docker, jangan taruh di internet publik, cukup lewat SSM atau tailnet."},
        ],
        [
            {"en": "EKS + Helm", "id": "EKS + Helm"},
            {"en": "Multi-tenant fleets, isolation per user", "id": "Fleet multi-tenant, isolasi per user"},
            {"en": "Only worth it with OpenClaw Enterprise (MIT control plane, Helm charts, EKS deploy guides). Real operational surface: node groups, IRSA, ingress.",
             "id": "Baru sepadan dengan OpenClaw Enterprise (control plane MIT, Helm chart, panduan deploy EKS). Permukaan operasionalnya nyata: node group, IRSA, ingress."},
        ],
        [
            {"en": "Bedrock AgentCore", "id": "Bedrock AgentCore"},
            {"en": "Serverless, per-session microVMs", "id": "Serverless, microVM per sesi"},
            {"en": "The Hermes AgentCore sample is the most interesting architecture here: a Firecracker microVM per session, CDK stacks, S3-backed workspace. Not in every region yet.",
             "id": "Sample Hermes di AgentCore arsitektur paling menarik di sini: satu Firecracker microVM per sesi, stack CDK, workspace di S3. Tapi belum ada di semua region."},
        ],
        [
            {"en": "Fargate / Lambda", "id": "Fargate / Lambda"},
            {"en": "Nothing you should copy", "id": "Tidak ada yang perlu ditiru"},
            {"en": "A long-lived agent with a local workspace and channel sockets fights both models. The AgentCore sample uses Fargate only as an edge gateway for long-lived connections.",
             "id": "Agent yang hidup terus dengan workspace lokal dan socket channel memang tidak cocok di dua model ini. Sample AgentCore memakai Fargate hanya sebagai gateway tepi untuk koneksi panjang."},
        ],
    ]
    s.append(table_block(headers, rows, lang, idx=2))

    # 3. Samples
    t = {"en": f"The {len(SAMPLES)} deployable samples worth cloning", "id": f"{len(SAMPLES)} sample deployable yang layak di-clone"}
    s.append(f"<h2 id=\"samples\">{esc(t[lang])}</h2>")
    for item in SAMPLES:
        s.append(card_block(item, lang))
    s.append(f"<p>{EXTRA_SAMPLE[lang]}</p>")

    # 4. Native Bedrock
    t = {"en": "Both agents speak Bedrock natively", "id": "Dua-duanya bicara Bedrock secara native"}
    s.append(f"<h2 id=\"bedrock\">{esc(t[lang])}</h2>")
    s.append("<p>" + ({"en": "This is what makes the whole AWS story work: it removes API keys from the picture. Auth is the AWS SDK credential chain, so an instance role is enough.",
                       "id": "Ini yang bikin seluruh cerita AWS-nya masuk: API key hilang dari gambaran. Auth-nya pakai AWS SDK credential chain, jadi cukup IAM role di instance."})[lang] + "</p>")
    s.append("<p>" + ({"en": "OpenClaw ships a Bedrock Converse streaming provider plus a separate <a href=\"https://docs.openclaw.ai/providers/bedrock-mantle\">Bedrock Mantle</a> provider for the OpenAI-compatible endpoint that serves open models.",
                       "id": "OpenClaw punya provider Bedrock Converse streaming, plus provider terpisah <a href=\"https://docs.openclaw.ai/providers/bedrock-mantle\">Bedrock Mantle</a> untuk endpoint yang kompatibel OpenAI dan melayani model terbuka."})[lang] + "</p>")
    s.append("<pre><code># OpenClaw: provider metadata\n"
             "# provider: amazon-bedrock\n# api:      bedrock-converse-stream\n# auth:     aws-sdk  (env vars, shared config, or instance role)\n\n"
             "# On EC2 the instance role is invisible to env-marker detection,\n# so discovery has to be turned on explicitly:\n"
             "openclaw config set plugins.entries.amazon-bedrock.config.discovery.enabled true\n"
             "openclaw config set plugins.entries.amazon-bedrock.config.discovery.region ap-southeast-3\n"
             "openclaw models list</code></pre>")
    s.append("<p>" + ({"en": "Discovery calls <code>bedrock:ListFoundationModels</code> and <code>bedrock:ListInferenceProfiles</code> and caches for an hour. Bare foundation-model IDs are only listed when Bedrock reports on-demand support; models that are profile-only appear as their <code>us.</code> or <code>global.</code> profiles instead, since those profiles carry different data-residency behaviour. You can still add a hidden model by hand under <code>models.providers[\"amazon-bedrock\"].models</code>.",
                       "id": "Discovery memanggil <code>bedrock:ListFoundationModels</code> dan <code>bedrock:ListInferenceProfiles</code>, lalu cache satu jam. Model ID polos hanya muncul kalau Bedrock melaporkan dukungan on-demand; model yang cuma lewat inference profile akan tampil sebagai profile <code>us.</code> atau <code>global.</code>, karena profile-profile itu punya perilaku data residency yang berbeda. Model tersembunyi tetap bisa ditambah manual di <code>models.providers[\"amazon-bedrock\"].models</code>."})[lang] + "</p>")
    s.append("<p>" + ({"en": "Hermes Agent routes each model family through the API that serves it best instead of forcing everything down one path.",
                       "id": "Hermes Agent mengarahkan tiap keluarga model lewat API yang paling cocok, bukan memaksa semuanya lewat satu jalur."})[lang] + "</p>")
    s.append("<pre><code># Hermes Agent: Bedrock provider\n"
             "cd ~/.hermes/hermes-agent &amp;&amp; python -c \"import pm; pm.sync_venv(['bedrock'], explicit=True)\"\n"
             "hermes model        # More providers... -&gt; AWS Bedrock -&gt; region -&gt; model\n\n"
             "# config.yaml afterwards\n# model:\n#   default: us.anthropic.claude-sonnet-4-6\n#   provider: bedrock\n# bedrock:\n#   region: ap-southeast-3</code></pre>")
    headers = [
        {"en": "Model family", "id": "Keluarga model"},
        {"en": "Route", "id": "Jalur"},
        {"en": "Why it matters", "id": "Kenapa penting"},
    ]
    rows = [
        [
            {"en": "Anthropic Claude", "id": "Anthropic Claude"},
            {"en": "Anthropic SDK (<code>AnthropicBedrock</code>)", "id": "Anthropic SDK (<code>AnthropicBedrock</code>)"},
            {"en": "Prompt caching, thinking budgets and adaptive thinking are not exposed through Converse.",
             "id": "Prompt caching, thinking budget, dan adaptive thinking tidak tersedia lewat Converse."},
        ],
        [
            {"en": "OpenAI models with a bare <code>openai.*</code> ID", "id": "Model OpenAI dengan ID polos <code>openai.*</code>"},
            {"en": "Bedrock Mantle OpenAI Responses endpoint", "id": "Endpoint OpenAI Responses di Bedrock Mantle"},
            {"en": "Mantle serves the bare in-region ID; <code>bedrock-runtime</code> rejects it.",
             "id": "Mantle yang melayani ID polos in-region; <code>bedrock-runtime</code> menolaknya."},
        ],
        [
            {"en": "The same models with a <code>us.</code> or <code>global.</code> profile ID", "id": "Model yang sama dengan profile ID <code>us.</code> atau <code>global.</code>"},
            {"en": "Native Converse API", "id": "Converse API native"},
            {"en": "Cross-region profiles only exist on <code>bedrock-runtime</code>.", "id": "Profile lintas region hanya ada di <code>bedrock-runtime</code>."},
        ],
        [
            {"en": "Nova, DeepSeek, Llama, GPT-OSS and the rest", "id": "Nova, DeepSeek, Llama, GPT-OSS, dan lainnya"},
            {"en": "Native Converse API", "id": "Converse API native"},
            {"en": "Guardrails, inference profiles and streaming all supported.", "id": "Guardrails, inference profile, dan streaming semuanya didukung."},
        ],
    ]
    s.append(table_block(headers, rows, lang, idx=3))
    s.append("<p>" + ({"en": "Minimum IAM for either agent: <code>bedrock:InvokeModel</code>, <code>bedrock:InvokeModelWithResponseStream</code>, <code>bedrock:ListFoundationModels</code>, <code>bedrock:ListInferenceProfiles</code>. Reference: <a href=\"https://docs.openclaw.ai/providers/bedrock\">OpenClaw Bedrock provider</a> and <a href=\"https://hermes-agent.nousresearch.com/docs/guides/aws-bedrock\">Hermes AWS Bedrock guide</a>.",
                       "id": "IAM minimum untuk keduanya: <code>bedrock:InvokeModel</code>, <code>bedrock:InvokeModelWithResponseStream</code>, <code>bedrock:ListFoundationModels</code>, <code>bedrock:ListInferenceProfiles</code>. Referensi: <a href=\"https://docs.openclaw.ai/providers/bedrock\">provider Bedrock OpenClaw</a> dan <a href=\"https://hermes-agent.nousresearch.com/docs/guides/aws-bedrock\">panduan AWS Bedrock Hermes</a>."})[lang] + "</p>")

    # 5. Articles
    t = {"en": f"{len(ARTICLES)} articles worth reading", "id": f"{len(ARTICLES)} artikel yang layak dibaca"}
    s.append(f"<h2 id=\"articles\">{esc(t[lang])}</h2>")
    s.append(list_block([{**a, "html": True} for a in ARTICLES], lang))

    # 6. Terraform
    t = {"en": "Community Terraform: read before trusting", "id": "Terraform komunitas: baca dulu sebelum dipercaya"}
    s.append(f"<h2 id=\"terraform\">{esc(t[lang])}</h2>")
    s.append(list_block([{**x, "html": True} for x in TERRAFORM], lang))
    s.append("<div class=\"callout\">"
             + ({"en": f"<h3>OpenClaw Enterprise is the scale path</h3><p><a href=\"https://github.com/openclaw/openclaw-enterprise\">openclaw/openclaw-enterprise</a> is MIT-licensed, actively developed, and ships EKS deployment guides for its Helm installation, including private-only cluster API access and cleanup. That is the only route to per-user isolation that is not hand-rolled.</p>",
                 "id": f"<h3>OpenClaw Enterprise adalah jalur skala</h3><p><a href=\"https://github.com/openclaw/openclaw-enterprise\">openclaw/openclaw-enterprise</a> berlisensi MIT, aktif dikembangkan, dan menyertakan panduan deploy EKS untuk instalasi Helm-nya, termasuk akses API cluster private-only dan prosedur cleanup. Ini satu-satunya jalur isolasi per user yang tidak perlu dirakit sendiri.</p>"})[lang]
             + "</div>")

    # 7. Jakarta
    t = {"en": "Jakarta reality check", "id": "Cek kenyataan Jakarta"}
    s.append(f"<h2 id=\"jakarta\">{esc(t[lang])}</h2>")
    s.append("<div class=\"callout warn\">"
             + ({"en": "<h3>ap-southeast-3 covers EC2 and Lightsail, not AgentCore</h3><p>Checked against AWS regional availability data on 18 November 2026: Amazon Bedrock and Amazon Lightsail both report available in <code>ap-southeast-3</code>. Amazon Bedrock AgentCore reports planned, not available.</p><p>So the EC2 and Lightsail paths run in Jakarta today with Bedrock as the model back end. The AgentCore-based Hermes sample needs a neighbouring region until AgentCore lands, which makes it an explicit cross-region data-processing decision rather than a default.</p>",
                 "id": "<h3>ap-southeast-3 mencakup EC2 dan Lightsail, bukan AgentCore</h3><p>Dicek ke data ketersediaan region AWS pada 18 November 2026: Amazon Bedrock dan Amazon Lightsail keduanya berstatus tersedia di <code>ap-southeast-3</code>. Amazon Bedrock AgentCore berstatus direncanakan, belum tersedia.</p><p>Jadi jalur EC2 dan Lightsail bisa jalan di Jakarta hari ini, dengan Bedrock sebagai backend modelnya. Sample Hermes berbasis AgentCore perlu region tetangga sampai AgentCore masuk, dan itu keputusan cross-region data processing yang harus dipilih sadar, bukan default.</p>"})[lang]
             + "</div>")
    s.append("<p>" + ({"en": "One more Jakarta-shaped detail: the CloudFormation launch buttons in both aws-samples repositories point at fixed regions and a single template bucket. For <code>ap-southeast-3</code> you re-host the template in your own bucket, launch from there, and verify which models are actually available in-region before picking default model IDs.",
                       "id": "Satu detail lain soal Jakarta: tombol launch CloudFormation di kedua repo aws-samples menunjuk region tetap dan satu bucket template. Untuk <code>ap-southeast-3</code> kamu perlu host ulang template-nya di bucket sendiri, launch dari sana, dan cek model mana yang benar-benar tersedia in-region sebelum menentukan model default."})[lang] + "</p>")

    # 8. Recommendation
    t = {"en": "What I would actually do", "id": "Yang sebenarnya akan aku lakukan"}
    s.append(f"<h2 id=\"choice\">{esc(t[lang])}</h2>")
    recs = [
        {"en": "<strong>Jakarta, EC2, Bedrock.</strong> Launch a Graviton instance from the aws-samples CloudFormation sample, re-hosted for <code>ap-southeast-3</code>. IAM role for Bedrock, SSM for access, no inbound ports. Shortest path that satisfies a Jakarta-only constraint today.",
         "id": "<strong>Jakarta, EC2, Bedrock.</strong> Jalankan instance Graviton dari sample CloudFormation aws-samples, di-host ulang untuk <code>ap-southeast-3</code>. IAM role untuk Bedrock, akses lewat SSM, tanpa inbound port. Jalur terpendek yang memenuhi batasan Jakarta-only hari ini."},
        {"en": "<strong>Keep the AgentCore sample on the shelf.</strong> It is the better long-term architecture for per-user isolation, but it is not deployable in Jakarta yet, and moving the CDK stacks to a neighbouring region is a data-residency decision, not a config change.",
         "id": "<strong>Simpan sample AgentCore dulu.</strong> Arsitekturnya lebih baik untuk isolasi per user jangka panjang, tapi belum bisa deploy di Jakarta, dan memindahkan stack CDK ke region tetangga itu keputusan data residency, bukan sekadar ganti config."},
        {"en": "<strong>Skip EKS unless multi-tenancy is the actual requirement.</strong> One agent per person on its own instance is cheaper and easier to reason about than a cluster with per-user cells, and OpenClaw's own security guidance says a shared gateway is not a trust boundary.",
         "id": "<strong>Lewati EKS kecuali multi-tenancy memang kebutuhan.</strong> Satu agent per orang di instance sendiri lebih murah dan lebih gampang dipikirkan daripada cluster dengan cell per user, dan panduan keamanan OpenClaw sendiri bilang gateway bersama bukan batas kepercayaan."},
        {"en": "<strong>Borrow the Terraform module only for the AWS-native edge.</strong> <code>infrahouse/terraform-aws-openclaw</code> is worth reading for the ALB plus Cognito pattern, but a personal gateway behind SSM does not need an ALB.",
         "id": "<strong>Pakai modul Terraform hanya untuk sisi AWS-native-nya.</strong> <code>infrahouse/terraform-aws-openclaw</code> layak dibaca untuk pola ALB plus Cognito, tapi gateway pribadi di belakang SSM tidak butuh ALB."},
    ]
    s.append(list_block([{**r, "html": True} for r in recs], lang, ordered=True))

    # 9. Sources
    s.append(f"<h2 id=\"sources\">{esc(LABEL[lang]['sources'])}</h2>")
    src = [
        {"en": 'AWS, <a href="https://aws.amazon.com/campaigns/openclawonaws/">Deploy OpenClaw on AWS: choose the best fit for you</a>.',
         "id": 'AWS, <a href="https://aws.amazon.com/campaigns/openclawonaws/">Deploy OpenClaw on AWS: choose the best fit for you</a>.'},
        {"en": 'AWS Docs, <a href="https://docs.aws.amazon.com/lightsail/latest/userguide/amazon-lightsail-quick-start-guide-openclaw.html">Get started with OpenClaw on Lightsail</a>.',
         "id": 'Dokumentasi AWS, <a href="https://docs.aws.amazon.com/lightsail/latest/userguide/amazon-lightsail-quick-start-guide-openclaw.html">Get started with OpenClaw on Lightsail</a>.'},
        {"en": 'AWS Samples, <a href="https://github.com/aws-samples/sample-OpenClaw-on-AWS-with-Bedrock">sample-OpenClaw-on-AWS-with-Bedrock</a> (MIT-0, 418 stars, pushed 18 Nov 2026).',
         "id": 'AWS Samples, <a href="https://github.com/aws-samples/sample-OpenClaw-on-AWS-with-Bedrock">sample-OpenClaw-on-AWS-with-Bedrock</a> (MIT-0, 418 bintang, push terakhir 18 Nov 2026).'},
        {"en": 'AWS Samples, <a href="https://github.com/aws-samples/sample-host-hermesagent-on-amazon-bedrock-agentcore">sample-host-hermesagent-on-amazon-bedrock-agentcore</a> (MIT-0, 45 stars, pushed 24 Jul 2026).',
         "id": 'AWS Samples, <a href="https://github.com/aws-samples/sample-host-hermesagent-on-amazon-bedrock-agentcore">sample-host-hermesagent-on-amazon-bedrock-agentcore</a> (MIT-0, 45 bintang, push terakhir 24 Jul 2026).'},
        {"en": 'Nous Research, <a href="https://hermes-agent.nousresearch.com/docs/guides/aws-bedrock">Hermes Agent — AWS Bedrock</a>.',
         "id": 'Nous Research, <a href="https://hermes-agent.nousresearch.com/docs/guides/aws-bedrock">Hermes Agent — AWS Bedrock</a>.'},
        {"en": 'OpenClaw Docs, <a href="https://docs.openclaw.ai/providers/bedrock">Amazon Bedrock provider</a> and <a href="https://docs.openclaw.ai/providers/bedrock-mantle">Bedrock Mantle</a>.',
         "id": 'Dokumentasi OpenClaw, <a href="https://docs.openclaw.ai/providers/bedrock">provider Amazon Bedrock</a> dan <a href="https://docs.openclaw.ai/providers/bedrock-mantle">Bedrock Mantle</a>.'},
        {"en": "AWS Builder Center, the four deployment articles linked above.",
         "id": "AWS Builder Center, empat artikel deployment yang ditautkan di atas."},
        {"en": 'AWS regional availability data for Amazon Bedrock, Amazon Lightsail and Amazon Bedrock AgentCore in <code>ap-southeast-3</code>, retrieved 18 November 2026.',
         "id": 'Data ketersediaan region AWS untuk Amazon Bedrock, Amazon Lightsail, dan Amazon Bedrock AgentCore di <code>ap-southeast-3</code>, diambil 18 November 2026.'},
        {"en": "GitHub API repository metadata for star counts, licenses and last-push dates, retrieved 18 November 2026.",
         "id": "Metadata repo via GitHub API untuk jumlah bintang, lisensi, dan tanggal push terakhir, diambil 18 November 2026."},
    ]
    s.append(list_block([{**x, "html": True} for x in src], lang, ordered=True))
    return "\n".join(s)


def masthead(lang):
    cur = "index.html" if lang == "en" else "index-id.html"
    other = LABEL[lang]
    return (
        '<header class="masthead">\n'
        '  <div class="page masthead-inner">\n'
        '    <p class="wordmark">Irfan\'s AI agents</p>\n'
        '    <nav aria-label="Registry and language">\n'
        f'      <a href="{REGISTRY}">Registry</a>\n'
        f'      <a href="{cur}" aria-current="page">{esc(LABEL[lang]["lang_name"])}</a>\n'
        f'      <a href="{other["other_href"]}">{esc(other["other_name"])}</a>\n'
        '    </nav>\n'
        '  </div>\n'
        '</header>'
    )


def footer(lang):
    return (
        '<footer class="foot">\n'
        '  <div class="page foot-inner">\n'
        f'    <p>{esc(LABEL[lang]["footer"])}</p>\n'
        f'    <p class="foot-meta">here.now slug {SLUG} · '
        f'<a href="{REGISTRY}">Registry</a></p>\n'
        '  </div>\n'
        '</footer>'
    )


def page(lang):
    lang_attr = "en" if lang == "en" else "id"
    title = html.escape(TITLE[lang])
    lede = html.escape(LEDE[lang])
    return f"""<!doctype html>
<html lang="{lang_attr}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{lede}">
<link rel="icon" href="data:,">
<link rel="stylesheet" href="assets/site.css">
</head>
<body>
<a class="skip" href="#main">{esc(SKIP[lang])}</a>
{masthead(lang)}
<main id="main" class="page">
{build(lang)}
</main>
{footer(lang)}
<script src="assets/site.js"></script>
</body>
</html>
"""


def write_assets():
    assets = OUT / "assets"
    (assets / "fonts").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(HERE / "assets" / "site.css", assets / "site.css")
    shutil.copyfile(HERE / "assets" / "site.js", assets / "site.js")
    shutil.copyfile(FONT_SRC, assets / "fonts" / "InterVariable-latin.woff2")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "index.html").write_text(page("en"), encoding="utf-8")
    (OUT / "index-id.html").write_text(page("id"), encoding="utf-8")
    write_assets()
    print(f"wrote {OUT}/index.html, index-id.html and assets/ "
          f"(site.css, site.js, fonts/InterVariable-latin.woff2)")


if __name__ == "__main__":
    main()
