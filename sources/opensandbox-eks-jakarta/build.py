#!/usr/bin/env python3
"""Build the bilingual OpenSandbox on EKS Jakarta page.

Reads no host paths. Writes ./site next to this file, or $OPENSANDBOX_SITE_DIR.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = Path(os.environ.get("OPENSANDBOX_SITE_DIR", ROOT / "site"))
FONT_SRC = Path(
    os.environ.get(
        "OPENSANDBOX_FONT",
        Path.home()
        / ".hermes/skills/productivity/herenow-artifact-publisher/root-index/assets/inter-latin-wght-normal.woff2",
    )
)
CSS_SRC = Path(
    os.environ.get(
        "OPENSANDBOX_CSS",
        Path.home()
        / ".hermes/skills/productivity/herenow-artifact-publisher/templates/scandinavian-page.css",
    )
)

# Checked 19 Nov 2026 against the ap-southeast-3 offer files. 730 hours.
FACTS = {
    "tag": "release-1.2.1",
    "published": "13 Nov 2026",
    "checked": "19 Nov 2026",
    "pilot": "777",
    "prod": "1,174",
    "eks": "73.00",
    "system_pilot": "367.92",
    "system_prod": "367.92",
    "worker_pilot": "300.47",
    "worker_prod": "600.94",
    "gp3_pilot": "9.60",
    "gp3_prod": "19.20",
    "nat": "43.07",
    "ipv4_pilot": "7.30",
    "ipv4_prod": "10.95",
    "alb": "18.40",
    "rds": "39.99",
    "ecr": "0.50",
    "extra_worker": "305",
    "metal": "3,606",
    "extended": "365",
    "extended_delta": "292",
}


def src(n: int) -> str:
    return f'<a href="#source-{n}">[{n}]</a>'


SOURCES = [
    ("OpenSandbox README, release-1.2.1", "https://github.com/opensandbox-group/OpenSandbox/blob/release-1.2.1/README.md"),
    ("OpenSandbox 1.2.1 release", "https://github.com/opensandbox-group/OpenSandbox/releases/tag/release-1.2.1"),
    ("Kubernetes deployment guide", "https://open-sandbox.ai/deployment"),
    ("Server chart values, 1.2.1", "https://github.com/opensandbox-group/OpenSandbox/blob/release-1.2.1/manifests/charts/server/values.yaml"),
    ("Ingress gateway values, 1.2.1", "https://github.com/opensandbox-group/OpenSandbox/blob/release-1.2.1/manifests/charts/ingress-gateway/values.yaml"),
    ("MCP server", "https://open-sandbox.ai/sdks/mcp"),
    ("SDK capability matrix, release-1.2.1", "https://raw.githubusercontent.com/opensandbox-group/OpenSandbox/release-1.2.1/docs/sdks/index.md"),
    ("Examples index, release-1.2.1", "https://raw.githubusercontent.com/opensandbox-group/OpenSandbox/release-1.2.1/docs/examples/index.md"),
    ("Fast Sandbox", "https://open-sandbox.ai/architecture/fast-sandbox"),
    ("ACK deployment notes, release-1.2.1", "https://github.com/opensandbox-group/OpenSandbox/blob/release-1.2.1/docs/deployment/ack.md"),
    ("EKS Kubernetes version lifecycle", "https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html"),
    ("EC2 nested virtualization", "https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html"),
    ("Umbrella release signing gap", "https://github.com/opensandbox-group/OpenSandbox/issues/2463"),
    ("EC2 price list, ap-southeast-3", "https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/ap-southeast-3/index.json"),
    ("EKS price list, ap-southeast-3", "https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEKS/current/ap-southeast-3/index.json"),
    ("VPC price list, ap-southeast-3", "https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonVPC/current/ap-southeast-3/index.json"),
    ("RDS price list, ap-southeast-3", "https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonRDS/current/ap-southeast-3/index.json"),
    ("ELB price list, ap-southeast-3", "https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AWSELB/current/ap-southeast-3/index.json"),
    ("ECR price list, ap-southeast-3", "https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonECR/current/ap-southeast-3/index.json"),
]


def sources_html() -> str:
    items = []
    for i, (title, url) in enumerate(SOURCES, start=1):
        items.append(
            f'<li id="source-{i}"><a href="{url}">{title}</a></li>'
        )
    return "<ol>\n" + "\n".join(items) + "\n</ol>"


def shell(lang: str, title: str, description: str, body: str) -> str:
    current_en = ' aria-current="page"' if lang == "en" else ""
    current_id = ' aria-current="page"' if lang == "id" else ""
    skip = "Skip to content" if lang == "en" else "Langsung ke isi"
    checked = "Checked" if lang == "en" else "Dicek"
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<link rel="stylesheet" href="assets/page.css">
</head>
<body>
<a class="skip" href="#main">{skip}</a>
<header class="masthead">
  <div class="page">
    <p class="wordmark">{title}</p>
    <nav aria-label="Language">
      <a href="index.html"{current_en}>English</a>
      <a href="index-id.html"{current_id}>Bahasa Indonesia</a>
    </nav>
  </div>
</header>
<main id="main" class="page">
{body}
</main>
<footer class="foot">
  <div class="page">
    <p>{checked} {FACTS["checked"]}. OpenSandbox {FACTS["tag"]}.</p>
    <p><a href="diagrams/eks-jakarta.html">Diagram</a></p>
  </div>
</footer>
<script>
document.querySelectorAll(".table-wrap").forEach(function (wrap) {{
  var table = wrap.querySelector("table");
  if (!table) return;
  var hint = document.createElement("p");
  hint.className = "swipe";
  hint.textContent = "{'Swipe sideways to read the table.' if lang == 'en' else 'Geser ke samping untuk membaca tabel.'}";
  wrap.insertBefore(hint, table);
  function fit() {{
    hint.hidden = wrap.scrollWidth <= wrap.clientWidth + 1;
  }}
  fit();
  window.addEventListener("resize", fit);
}});
</script>
</body>
</html>
"""


def en() -> str:
    f = FACTS
    s = sources_html()
    return f"""
<p class="eyebrow">OpenSandbox {f["tag"]}, AWS ap-southeast-3</p>
<h1>OpenSandbox on EKS Jakarta</h1>
<p class="lede">OpenSandbox is a sandbox API you run yourself. A small EKS cluster in Jakarta, on the default container runtime, is about ${f["pilot"]}/month. A two-AZ layout is about ${f["prod"]}/month, before PPN and traffic.</p>
<p>Bahasa Indonesia: <a href="index-id.html">versi Indonesia</a>.</p>

<h2 id="what">What it is</h2>
<p>OpenSandbox gives an agent an isolated Linux environment to run commands, edit files, and, if you put the tools in the image, drive a browser or a desktop. Your application talks to one lifecycle API. The server can sit on Docker for a laptop, or on Kubernetes for a cluster. The API does not change.{src(1)}</p>
<p>This page is pinned to {f["tag"]}, published {f["published"]}. The docs site still shows <code>release-1.1.0</code> as the example checkout. Use the stable tag, not <code>main</code>.{src(2)}{src(3)}</p>
<p>It is Apache-2.0, and it is a project of the Agentic AI Foundation.{src(1)}</p>

<h2 id="features">What the API gives you</h2>
<p>On {f["tag"]}, the five language SDKs can create a sandbox, reconnect to it, renew it, pause and resume it, and kill it. They can run commands, read and write files, read metrics, set an egress policy, and use Credential Vault. Snapshots, templates, volumes, and pools are in the SDK too. Whether pause, snapshots, and templates actually work depends on the runtime behind the server, not on the client.{src(7)}</p>
<ul>
<li>Inbound traffic on Kubernetes goes through the ingress gateway. Sandbox pods are ClusterIP-only, so the gateway is required, not optional.{src(3)}</li>
<li>Outbound access is a per-sandbox policy. Credential Vault can call an external service without putting the real secret in the sandbox.{src(1)}</li>
<li>Pools and batch create are for running many trials at once. C# is the SDK that does not have Client Pool.{src(7)}</li>
</ul>
<p>Fast Sandbox is a separate runtime, not a second product. A create that names a template is routed to Firecracker microVMs inside pre-warmed pods, and the sandbox id starts with <code>fsb-</code>. Image-based creates stay on ordinary Kubernetes pods. The SDK does not change.{src(9)}</p>

<h2 id="clients">How other apps use it</h2>
<p>Anything that can call the lifecycle API can use the cluster. The server does not care that it is running on EKS.</p>
<ul>
<li>Your own service uses a SDK: Python (<code>opensandbox</code>), TypeScript (<code>@alibaba-group/opensandbox</code>), Java or Kotlin, Go, or C# (<code>Alibaba.OpenSandbox</code>). Python is the quick-start language. Go is the one you would pick for a long-running backend.{src(1)}{src(7)}</li>
<li>A person or a script uses the <code>osb</code> CLI. <code>pip install opensandbox-cli</code>.{src(1)}</li>
<li>An agent that already speaks MCP uses <code>opensandbox-mcp</code>. Documented setups are Claude Code and Cursor, over stdio or HTTP. Any other MCP client can use the same server. The tools cover create, connect, kill, renew, run a command, and text files. Pools, snapshots, templates, and Credential Vault stay on the SDK or the CLI.{src(6)}</li>
</ul>
<p>A second, different use is running an agent inside the sandbox. The examples do that for Claude Code, Codex CLI, Gemini CLI, OpenCode, Qwen Code, Kimi CLI, OpenClaw, LangGraph, Google ADK, Playwright, Chrome, a desktop, and VS Code Web. Those are workloads. The client is still the SDK or MCP server that created the sandbox.{src(8)}</p>
<p>Point the client at the lifecycle host and the API key. For the CLI that is <code>osb config set connection.domain</code>. For MCP it is <code>--domain</code> and <code>--api-key</code>.{src(1)}{src(6)}</p>

<h2 id="architecture">Architecture</h2>
<p>The diagram is the small Jakarta layout: clients outside the region, a load balancer, the three control-plane pods, sandbox pods, ECR for images, and optional Postgres. EKS 1.35 or 1.36 is the cluster boundary. Fast Sandbox is not in this drawing.</p>
<figure class="diagram">
  <iframe title="OpenSandbox on EKS Jakarta" src="diagrams/eks-jakarta.html"></iframe>
  <figcaption><a href="diagrams/eks-jakarta.html">Open the diagram</a></figcaption>
</figure>
<h3>Components</h3>
<ul>
<li>Lifecycle server, one replica, port 80. It refuses to start without an API key. Upgrades use <code>Recreate</code>, so the API blips.{src(3)}{src(4)}</li>
<li>Controller, which reconciles <code>BatchSandbox</code>, <code>Pool</code>, and <code>SandboxSnapshot</code>. It is small. It is not what sizes the node.{src(3)}</li>
<li>Ingress gateway, two replicas, each requesting 1 CPU and 4 GiB, limit 2 CPU and 8 GiB, listening on port 28888. The chart service is ClusterIP on port 80.{src(5)}</li>
<li>Sandbox pods in the <code>opensandbox</code> namespace. <code>execd</code> is inside the sandbox image. An egress sidecar is added only when the create request sets <code>networkPolicy</code>.{src(4)}</li>
</ul>
<h3>What you have to bring</h3>
<ul>
<li>EKS 1.35 or 1.36 in <code>ap-southeast-3</code>. OpenSandbox only needs Kubernetes 1.22+. Do not create 1.34: standard support ends 2 Dec 2026, and extended support is $0.50/hour, ${f["extended"]}/month, instead of ${f["eks"]}.{src(3)}{src(11)}{src(15)}</li>
<li>Helm 3, from a git checkout of {f["tag"]}. Charts are not published as standalone packages.{src(3)}</li>
<li>ECR in Jakarta. The chart default registry is <code>sandbox-registry.cn-zhangjiakou.cr.aliyuncs.com</code>. Do not pull that from this region. Mirror <code>server</code>, <code>controller</code>, <code>ingress</code>, <code>execd</code>, and <code>egress</code> from Docker Hub or GHCR, and pin the digest. Current umbrella releases are not Cosign-signed the way the old per-component releases were.{src(1)}{src(4)}{src(13)}</li>
<li>An API key secret, a DNS name for <code>server.gateway.host</code>, and a load balancer in front of the server and the gateway.</li>
<li>Optional RDS PostgreSQL in the same region, if a reschedule must not drop sandbox state. The chart default is one server and no database.{src(3)}</li>
<li>EBS gp3 if a sandbox mounts a volume. The basic path does not need it beyond the node disks.</li>
</ul>

<h2 id="example">Example</h2>
<p>Python, against a server you already started. The same calls work against the EKS host once the domain and API key point there.{src(1)}</p>
<pre><code>from opensandbox import Sandbox

sandbox = await Sandbox.create("alpine")
try:
    result = await sandbox.commands.run("echo 'Hello OpenSandbox!'")
finally:
    await sandbox.destroy()</code></pre>
<p>The CLI form:</p>
<pre><code>osb config set connection.domain &lt;lifecycle-host&gt;
osb config set connection.protocol https
osb config set connection.api_key &lt;api-key&gt;
osb sandbox create --image python:3.12 --timeout 30m
osb command run &lt;sandbox-id&gt; -- python -c "print(1 + 1)"</code></pre>

<h2 id="deploy">Deploy on EKS Jakarta</h2>
<p>Leave <code>fast-sandbox</code> off. Their cloud guide wants bare-metal nodes with <code>/dev/kvm</code>, and every node in that pool has to be the same CPU model. One <code>c7i.metal-24xl</code> in Jakarta is about ${f["metal"]}/month before disks. AWS nested virtualization can expose <code>/dev/kvm</code> on <code>m7i</code>, <code>c7i</code>, <code>r7i</code>, and <code>i7i</code> at no extra charge, and <code>m8i</code> / <code>c8i</code> are not in the Jakarta price list, but OpenSandbox has not published an EKS recipe for that path.{src(10)}{src(12)}{src(14)}</p>
<ol>
<li>Create the cluster on 1.35 or 1.36, in <code>ap-southeast-3</code>, with a private subnet if you can accept a NAT.</li>
<li>Two managed node groups. System nodes run the server, controller, and gateway. A pilot fits on one <code>m7i.2xlarge</code>, which matches the single server replica. Workers run sandbox pods only, tainted, starting at one <code>c7i.2xlarge</code>.</li>
<li>Mirror the five images into ECR at <code>{f["tag"]}</code> and create a pull secret or a node role that can read that registry.</li>
<li>Create namespaces <code>opensandbox-system</code> and <code>opensandbox</code>. The chart does not create the workload namespace.{src(3)}</li>
<li>Check out {f["tag"]}, run <code>helm dependency build</code> in <code>manifests/charts</code>, and install the umbrella chart with <code>ingress-gateway.enabled=true</code> and the image repositories pointed at ECR. Store the API key in a Secret and reference it from the server values. Set <code>server.gateway.host</code> to the name clients will use.</li>
<li>Put an ALB or NLB in front of the server and the gateway. Confirm <code>/health</code> before pointing a client at it.</li>
<li>Add RDS only when you need state to survive a pod reschedule. Keep <code>server.replicaCount</code> at 1. A second replica is not general high availability.{src(3)}</li>
</ol>

<h2 id="cost">Cost</h2>
<p>On-demand, 730 hours, USD, excluding PPN. Retrieved {f["checked"]} from the <code>ap-southeast-3</code> offer files. A price-list row is not a quota. ALB LCU, NAT data, internet egress, CloudWatch, and Support are not in the floor.{src(14)}{src(15)}{src(16)}{src(17)}{src(18)}{src(19)}</p>
<div class="table-wrap" role="region" aria-label="Monthly cost" tabindex="0">
<table>
<thead>
<tr><th>Line</th><th>Pilot</th><th>Small 2-AZ</th></tr>
</thead>
<tbody>
<tr><td>EKS control plane, $0.10/hour</td><td>{f["eks"]}</td><td>{f["eks"]}</td></tr>
<tr><td>System nodes</td><td>{f["system_pilot"]} (1× m7i.2xlarge)</td><td>{f["system_prod"]} (2× m7i.xlarge)</td></tr>
<tr><td>Sandbox workers</td><td>{f["worker_pilot"]} (1× c7i.2xlarge)</td><td>{f["worker_prod"]} (2× c7i.2xlarge)</td></tr>
<tr><td>gp3, $0.096/GB-month</td><td>{f["gp3_pilot"]} (100 GB)</td><td>{f["gp3_prod"]} (200 GB)</td></tr>
<tr><td>NAT, $0.059/hour</td><td>0</td><td>{f["nat"]}</td></tr>
<tr><td>Public IPv4, $0.005/hour</td><td>{f["ipv4_pilot"]} (2)</td><td>{f["ipv4_prod"]} (3, assumed)</td></tr>
<tr><td>ALB, $0.0252/hour</td><td>{f["alb"]}</td><td>{f["alb"]}</td></tr>
<tr><td>RDS db.t4g.small + 20 GB gp3</td><td>0</td><td>{f["rds"]}</td></tr>
<tr><td>ECR, 5 GB</td><td>{f["ecr"]}</td><td>{f["ecr"]}</td></tr>
<tr><td>Floor</td><td>{f["pilot"]}</td><td>{f["prod"]}</td></tr>
</tbody>
</table>
</div>
<p>The three public IPv4 addresses on the 2-AZ row are an address-count assumption: one for the NAT, two for an internet-facing load balancer across two AZs. The hourly rates are from the offer files.</p>
<p>Each extra private <code>c7i.2xlarge</code> plus 50 GB gp3 is about ${f["extra_worker"]}/month. How many sandboxes fit depends on the CPU and memory in the create request, not on the chart.</p>
<p>The NAT hour is the line that surprises people, not the gigabytes. 100 GB through the NAT is $5.90. The gateway existing at all is ${f["nat"]}/month before any sandbox traffic. EKS itself is ${f["eks"]} even with two nodes.</p>
<p>If you do not want to tune the chart's 8 GiB limits, replace the two <code>m7i.xlarge</code> system nodes with two <code>m7i.2xlarge</code>. That adds about $368/month. Kubernetes schedules on requests, so the cheaper pair fits if the server and the two gateway pods are spread.</p>
<p>If a cluster is left on 1.34 past 2 Dec 2026, the control plane moves to extended support and the ${f["eks"]} line becomes ${f["extended"]}, a ${f["extended_delta"]} increase, with no change in OpenSandbox.{src(11)}{src(15)}</p>

<h2 id="sources">Sources</h2>
{s}
"""


def id_page() -> str:
    f = FACTS
    s = sources_html()
    return f"""
<p class="eyebrow">OpenSandbox {f["tag"]}, AWS ap-southeast-3</p>
<h1>OpenSandbox di EKS Jakarta</h1>
<p class="lede">OpenSandbox itu sandbox API yang kamu jalankan sendiri. Cluster EKS kecil di Jakarta, dengan runtime container biasa, kira-kira ${f["pilot"]}/bulan. Layout 2 AZ kira-kira ${f["prod"]}/bulan, sebelum PPN dan traffic.</p>
<p>English: <a href="index.html">English version</a>.</p>

<h2 id="what">Apa ini</h2>
<p>OpenSandbox kasih agent sebuah environment Linux terisolasi untuk menjalankan command, mengedit file, dan, kalau tool-nya ada di image, menggerakkan browser atau desktop. Aplikasi kamu bicara ke satu lifecycle API. Server-nya bisa di Docker untuk laptop, atau di Kubernetes untuk cluster. API-nya sama.{src(1)}</p>
<p>Halaman ini dipin ke {f["tag"]}, terbit {f["published"]}. Situs dokumentasinya masih mencontohkan checkout <code>release-1.1.0</code>. Pakai tag stable, bukan <code>main</code>.{src(2)}{src(3)}</p>
<p>Lisensinya Apache-2.0, dan ini proyek Agentic AI Foundation.{src(1)}</p>

<h2 id="features">Apa yang API-nya kasih</h2>
<p>Di {f["tag"]}, kelima SDK bisa membuat sandbox, menyambung lagi, memperpanjang, pause dan resume, lalu mematikannya. Mereka bisa menjalankan command, baca dan tulis file, baca metrics, mengatur egress policy, dan memakai Credential Vault. Snapshot, template, volume, dan pool juga ada di SDK. Pause, snapshot, dan template benar-benar jalan atau tidak tergantung runtime di belakang server, bukan di client.{src(7)}</p>
<ul>
<li>Traffic masuk di Kubernetes lewat ingress gateway. Sandbox pod-nya ClusterIP saja, jadi gateway-nya wajib, bukan opsional.{src(3)}</li>
<li>Akses keluar adalah policy per sandbox. Credential Vault bisa memanggil layanan luar tanpa menaruh secret aslinya di dalam sandbox.{src(1)}</li>
<li>Pool dan batch create dipakai untuk menjalankan banyak trial sekaligus. C# adalah SDK yang tidak punya Client Pool.{src(7)}</li>
</ul>
<p>Fast Sandbox adalah runtime terpisah, bukan produk kedua. Create yang menyebut template diarahkan ke Firecracker microVM di dalam pod yang sudah dihangatkan, dan id sandbox-nya diawali <code>fsb-</code>. Create berbasis image tetap memakai pod Kubernetes biasa. SDK-nya tidak berubah.{src(9)}</p>

<h2 id="clients">Bagaimana aplikasi lain memakainya</h2>
<p>Apa pun yang bisa memanggil lifecycle API bisa memakai cluster ini. Server-nya tidak peduli bahwa dia berjalan di EKS.</p>
<ul>
<li>Service kamu sendiri memakai SDK: Python (<code>opensandbox</code>), TypeScript (<code>@alibaba-group/opensandbox</code>), Java atau Kotlin, Go, atau C# (<code>Alibaba.OpenSandbox</code>). Python adalah bahasa di quick start. Go yang lebih pas untuk backend yang hidup lama.{src(1)}{src(7)}</li>
<li>Orang atau script memakai CLI <code>osb</code>. <code>pip install opensandbox-cli</code>.{src(1)}</li>
<li>Agent yang sudah bicara MCP memakai <code>opensandbox-mcp</code>. Setup yang didokumentasikan adalah Claude Code dan Cursor, lewat stdio atau HTTP. Client MCP lain bisa memakai server yang sama. Tool-nya mencakup create, connect, kill, renew, menjalankan command, dan file teks. Pool, snapshot, template, dan Credential Vault tetap di SDK atau CLI.{src(6)}</li>
</ul>
<p>Pemakaian kedua, yang beda, adalah menjalankan agent di dalam sandbox. Contohnya melakukan itu untuk Claude Code, Codex CLI, Gemini CLI, OpenCode, Qwen Code, Kimi CLI, OpenClaw, LangGraph, Google ADK, Playwright, Chrome, desktop, dan VS Code Web. Itu workload. Client-nya tetap SDK atau MCP server yang membuat sandbox-nya.{src(8)}</p>
<p>Arahkan client ke lifecycle host dan API key. Untuk CLI itu <code>osb config set connection.domain</code>. Untuk MCP itu <code>--domain</code> dan <code>--api-key</code>.{src(1)}{src(6)}</p>

<h2 id="architecture">Arsitektur</h2>
<p>Diagram ini adalah layout Jakarta yang kecil: client di luar region, load balancer, tiga pod control plane, sandbox pod, ECR untuk image, dan Postgres opsional. EKS 1.35 atau 1.36 adalah batas cluster. Fast Sandbox tidak ada di gambar ini.</p>
<figure class="diagram">
  <iframe title="OpenSandbox di EKS Jakarta" src="diagrams/eks-jakarta.html"></iframe>
  <figcaption><a href="diagrams/eks-jakarta.html">Buka diagram</a></figcaption>
</figure>
<h3>Komponen</h3>
<ul>
<li>Lifecycle server, satu replica, port 80. Dia menolak start tanpa API key. Upgrade memakai <code>Recreate</code>, jadi API-nya sempat putus.{src(3)}{src(4)}</li>
<li>Controller, yang merekonsiliasi <code>BatchSandbox</code>, <code>Pool</code>, dan <code>SandboxSnapshot</code>. Ukurannya kecil. Bukan dia yang menentukan ukuran node.{src(3)}</li>
<li>Ingress gateway, dua replica, masing-masing request 1 CPU dan 4 GiB, limit 2 CPU dan 8 GiB, listen di port 28888. Service chart-nya ClusterIP di port 80.{src(5)}</li>
<li>Sandbox pod di namespace <code>opensandbox</code>. <code>execd</code> ada di dalam image sandbox. Egress sidecar ditambahkan hanya kalau create request mengisi <code>networkPolicy</code>.{src(4)}</li>
</ul>
<h3>Yang harus kamu sediakan</h3>
<ul>
<li>EKS 1.35 atau 1.36 di <code>ap-southeast-3</code>. OpenSandbox hanya butuh Kubernetes 1.22+. Jangan buat 1.34: standard support berakhir 2 Des 2026, dan extended support $0.50/jam, ${f["extended"]}/bulan, bukan ${f["eks"]}.{src(3)}{src(11)}{src(15)}</li>
<li>Helm 3, dari git checkout {f["tag"]}. Chart tidak diterbitkan sebagai paket terpisah.{src(3)}</li>
<li>ECR di Jakarta. Registry default chart adalah <code>sandbox-registry.cn-zhangjiakou.cr.aliyuncs.com</code>. Jangan pull itu dari region ini. Mirror <code>server</code>, <code>controller</code>, <code>ingress</code>, <code>execd</code>, dan <code>egress</code> dari Docker Hub atau GHCR, lalu pin digest-nya. Umbrella release yang sekarang tidak Cosign-signed seperti release per-komponen yang lama.{src(1)}{src(4)}{src(13)}</li>
<li>Secret API key, nama DNS untuk <code>server.gateway.host</code>, dan load balancer di depan server dan gateway.</li>
<li>RDS PostgreSQL opsional di region yang sama, kalau reschedule tidak boleh menghapus state sandbox. Default chart adalah satu server dan tanpa database.{src(3)}</li>
<li>EBS gp3 kalau sandbox memasang volume. Jalur dasar tidak membutuhkannya di luar disk node.</li>
</ul>

<h2 id="example">Contoh</h2>
<p>Python, ke server yang sudah berjalan. Panggilan yang sama jalan ke host EKS begitu domain dan API key diarahkan ke sana.{src(1)}</p>
<pre><code>from opensandbox import Sandbox

sandbox = await Sandbox.create("alpine")
try:
    result = await sandbox.commands.run("echo 'Hello OpenSandbox!'")
finally:
    await sandbox.destroy()</code></pre>
<p>Bentuk CLI-nya:</p>
<pre><code>osb config set connection.domain &lt;lifecycle-host&gt;
osb config set connection.protocol https
osb config set connection.api_key &lt;api-key&gt;
osb sandbox create --image python:3.12 --timeout 30m
osb command run &lt;sandbox-id&gt; -- python -c "print(1 + 1)"</code></pre>

<h2 id="deploy">Deploy di EKS Jakarta</h2>
<p>Biarkan <code>fast-sandbox</code> mati. Panduan cloud mereka minta node bare metal dengan <code>/dev/kvm</code>, dan semua node di pool itu harus CPU model yang sama. Satu <code>c7i.metal-24xl</code> di Jakarta kira-kira ${f["metal"]}/bulan sebelum disk. Nested virtualization AWS bisa membuka <code>/dev/kvm</code> di <code>m7i</code>, <code>c7i</code>, <code>r7i</code>, dan <code>i7i</code> tanpa biaya tambahan, dan <code>m8i</code> / <code>c8i</code> tidak ada di price list Jakarta, tapi OpenSandbox belum menerbitkan resep EKS untuk jalur itu.{src(10)}{src(12)}{src(14)}</p>
<ol>
<li>Buat cluster di 1.35 atau 1.36, di <code>ap-southeast-3</code>, dengan subnet private kalau kamu bisa menerima NAT.</li>
<li>Dua managed node group. Node system menjalankan server, controller, dan gateway. Pilot muat di satu <code>m7i.2xlarge</code>, yang sesuai dengan satu replica server. Worker hanya menjalankan sandbox pod, di-taint, mulai dari satu <code>c7i.2xlarge</code>.</li>
<li>Mirror kelima image ke ECR pada <code>{f["tag"]}</code> dan buat pull secret atau node role yang bisa membaca registry itu.</li>
<li>Buat namespace <code>opensandbox-system</code> dan <code>opensandbox</code>. Chart tidak membuat namespace workload.{src(3)}</li>
<li>Checkout {f["tag"]}, jalankan <code>helm dependency build</code> di <code>manifests/charts</code>, lalu install umbrella chart dengan <code>ingress-gateway.enabled=true</code> dan repository image mengarah ke ECR. Simpan API key di Secret dan referensikan dari values server. Isi <code>server.gateway.host</code> dengan nama yang akan dipakai client.</li>
<li>Pasang ALB atau NLB di depan server dan gateway. Pastikan <code>/health</code> jawab sebelum mengarahkan client ke sana.</li>
<li>Tambah RDS hanya kalau state harus bertahan saat pod di-reschedule. Biarkan <code>server.replicaCount</code> di 1. Replica kedua bukan high availability umum.{src(3)}</li>
</ol>

<h2 id="cost">Biaya</h2>
<p>On-demand, 730 jam, USD, belum termasuk PPN. Diambil {f["checked"]} dari offer file <code>ap-southeast-3</code>. Baris di price list bukan kuota. ALB LCU, data NAT, internet egress, CloudWatch, dan Support tidak masuk floor.{src(14)}{src(15)}{src(16)}{src(17)}{src(18)}{src(19)}</p>
<div class="table-wrap" role="region" aria-label="Biaya bulanan" tabindex="0">
<table>
<thead>
<tr><th>Baris</th><th>Pilot</th><th>2 AZ kecil</th></tr>
</thead>
<tbody>
<tr><td>EKS control plane, $0.10/jam</td><td>{f["eks"]}</td><td>{f["eks"]}</td></tr>
<tr><td>System node</td><td>{f["system_pilot"]} (1× m7i.2xlarge)</td><td>{f["system_prod"]} (2× m7i.xlarge)</td></tr>
<tr><td>Sandbox worker</td><td>{f["worker_pilot"]} (1× c7i.2xlarge)</td><td>{f["worker_prod"]} (2× c7i.2xlarge)</td></tr>
<tr><td>gp3, $0.096/GB-bulan</td><td>{f["gp3_pilot"]} (100 GB)</td><td>{f["gp3_prod"]} (200 GB)</td></tr>
<tr><td>NAT, $0.059/jam</td><td>0</td><td>{f["nat"]}</td></tr>
<tr><td>Public IPv4, $0.005/jam</td><td>{f["ipv4_pilot"]} (2)</td><td>{f["ipv4_prod"]} (3, asumsi)</td></tr>
<tr><td>ALB, $0.0252/jam</td><td>{f["alb"]}</td><td>{f["alb"]}</td></tr>
<tr><td>RDS db.t4g.small + 20 GB gp3</td><td>0</td><td>{f["rds"]}</td></tr>
<tr><td>ECR, 5 GB</td><td>{f["ecr"]}</td><td>{f["ecr"]}</td></tr>
<tr><td>Floor</td><td>{f["pilot"]}</td><td>{f["prod"]}</td></tr>
</tbody>
</table>
</div>
<p>Tiga public IPv4 di baris 2 AZ adalah asumsi jumlah alamat: satu untuk NAT, dua untuk load balancer yang menghadap internet di dua AZ. Tarif jam-nya dari offer file.</p>
<p>Setiap <code>c7i.2xlarge</code> private tambahan plus 50 GB gp3 kira-kira ${f["extra_worker"]}/bulan. Berapa sandbox yang muat tergantung CPU dan memory di create request, bukan di chart.</p>
<p>Yang biasanya mengejutkan adalah jam NAT, bukan gigabyte-nya. 100 GB lewat NAT harganya $5.90. Gateway yang sekadar ada sudah ${f["nat"]}/bulan sebelum ada traffic sandbox. EKS sendiri ${f["eks"]} bahkan dengan dua node.</p>
<p>Kalau kamu tidak ingin mengubah limit 8 GiB di chart, ganti dua system node <code>m7i.xlarge</code> dengan dua <code>m7i.2xlarge</code>. Itu menambah kira-kira $368/bulan. Kubernetes menjadwalkan berdasarkan request, jadi pasangan yang lebih murah muat kalau server dan dua pod gateway tersebar.</p>
<p>Kalau cluster dibiarkan di 1.34 lewat 2 Des 2026, control plane pindah ke extended support dan baris ${f["eks"]} menjadi ${f["extended"]}, naik ${f["extended_delta"]}, tanpa perubahan di OpenSandbox.{src(11)}{src(15)}</p>

<h2 id="sources">Sumber</h2>
{s}
"""


EXTRA_CSS = """
.diagram { margin: 28px 0 8px; }
.diagram iframe {
  width: 100%;
  height: 640px;
  border: 1px solid var(--rule);
  border-radius: 8px;
  background: var(--canvas);
}
.diagram figcaption { margin-top: 8px; font-size: 14px; }
.swipe { margin: 0 0 8px; font-size: 13px; color: var(--ink-3); }
.swipe[hidden] { display: none; }
pre code { white-space: pre-wrap; overflow-wrap: anywhere; }
@media (max-width: 600px) {
  pre { overflow-x: visible; }
  .diagram iframe { height: 520px; }
}
"""


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "assets" / "fonts").mkdir(parents=True)
    (OUT / "diagrams").mkdir()
    css = CSS_SRC.read_text()
    marker = "/* Scandinavian"
    if css.startswith(marker):
        css = css.split("*/", 1)[1].lstrip("\n")
    css = css + EXTRA_CSS
    (OUT / "assets" / "page.css").write_text(css)
    shutil.copy(FONT_SRC, OUT / "assets" / "fonts" / "InterVariable-latin.woff2")
    shutil.copy(ROOT / "diagrams" / "eks-jakarta.html", OUT / "diagrams" / "eks-jakarta.html")
    en_html = shell(
        "en",
        "OpenSandbox on EKS Jakarta",
        "What OpenSandbox is, how other apps call it, and what an EKS deploy in Jakarta costs.",
        en(),
    )
    id_html = shell(
        "id",
        "OpenSandbox di EKS Jakarta",
        "Apa itu OpenSandbox, bagaimana aplikasi lain memakainya, dan berapa biaya deploy EKS di Jakarta.",
        id_page(),
    )
    (OUT / "index.html").write_text(en_html)
    (OUT / "index-id.html").write_text(id_html)
    for name in ("index.html", "index-id.html"):
        text = (OUT / name).read_text()
        for href in ("index.html", "index-id.html", "diagrams/eks-jakarta.html", "assets/page.css"):
            if f'href="{href}"' not in text and f'src="{href}"' not in text:
                raise SystemExit(f"{name} missing {href}")
    print(OUT)


if __name__ == "__main__":
    main()
