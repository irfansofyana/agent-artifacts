# Sandboxes for AI agents on AWS Jakarta: three options for WeKnora

Decision document, 17 November 2026. Every component runs in `ap-southeast-3` (Jakarta), and every price comes from the AWS Price List API for that Region, retrieved the same day. This page complements the CubeSandbox research note on the main page.

## Decision summary

| | Option 1 · CubeSandbox | Option 2 · E2B Embed | Option 3 · Nitro Sandboxes | Option 4 · OpenSandbox |
|---|---|---|---|---|
| What it is | Tencent's E2B-compatible sandbox control plane on KVM.[14][19] | The complete E2B stack on one machine, Apache-2.0, no license key.[51][55] | AWS per-pod Firecracker microVMs through a RuntimeClass.[49] | A general-purpose sandbox platform for AI apps, an Agentic AI Foundation project, Apache-2.0.[69][65] |
| Isolation model | One microVM per sandbox with its own kernel.[19] | One Firecracker microVM per sandbox inside a single machine.[51] | One microVM per pod, enforced by the Nitro hypervisor.[49] | Containers on Kubernetes by default, Firecracker microVMs with FastSandbox.[66][67] |
| API | E2B-compatible REST plus official SDKs.[30] | The same API and SDK as E2B Cloud.[51][60] | No sandbox API, only CRDs and a RuntimeClass.[49][56] | Its own lifecycle API (OpenAPI in `specs/`), multi-language SDKs, the `osb` CLI, and MCP.[66][65] |
| WeKnora code change | None, the `cube` backend exists.[32] | None, the `e2b` backend exists.[32] | Yes, a new backend adapter.[40] | Yes, a new adapter or an E2B-compatible gateway in front.[32][68] |
| Snapshot, pause, resume | In the control plane; cross-node is preview.[14][9] | Yes, including pause and resume with memory preserved.[51] | No equivalent.[49] | Yes, and with FastSandbox memory and disk are preserved.[66][67] |
| Scale | Multi-node, one cluster.[15][17] | One machine by design, Auto Scaling group of one.[51][60] | Many nodes, managed by EKS.[49] | Multi-node and Kubernetes-native, with resource pools and batch creation.[66] |
| Sandbox cost per month | $4,191 (eval) to $8,880.[24][25] | $238 (m7i.xlarge) to $475 (m7i.2xlarge).[24][27] | $967 (two nodes) to $3,545 (four nodes).[24][25] | $779 (two nodes, managed node group) to $850 (Auto Mode).[24][25] |
| Upside | E2B API plus AgentHub for OpenClaw assistants.[5][14] | Cheapest entry point, Dockerfile templates, no cluster.[51] | Strongest per-pod isolation with the lowest operating cost.[49] | Ingress, per-sandbox egress, credential vault, and optional microVMs, all Kubernetes-native.[65][66] |
| Drawback | Needs bare-metal nodes and the Kubernetes path is preview.[16][11] | One machine, no persistent volume, one team per install.[45][62] | Requires WeKnora code changes and loses snapshot and pause.[40] | Needs new integration, the microVM mode is alpha, and the E2B gateway is very young.[67][68] |

## Recommendation

**Start with Option 2.** E2B Embed speaks the API WeKnora already understands with zero code changes, keeps snapshot plus pause and resume, and runs on an ordinary instance in Jakarta with no bare metal involved.[51][60][32] Sandbox cost starts around $238 per month, but that is a 16 GB node which the compose documentation rates for roughly eight small sandboxes at the default memory pool, so a multi-agent plan should start at a 32 GB node or larger.[24][63]

**Option 1 is the platform path when you need multiple nodes.** CubeSandbox offers the same API in a cluster that can grow, and it has the most mature agent-hosting story through AgentHub.[14][5] The price is bare-metal nodes and a Kubernetes path that is still preview.[16][11]

**Option 4 is the shared-platform candidate, not this week's replacement for Embed.** OpenSandbox is the only option that is Kubernetes-native, multi-node, and already carries ingress, per-sandbox egress, and a credential vault, with microVMs as an option. Its price is new integration work in WeKnora and tolerance for components that are still alpha in places.[66][67][68]

**One important correction to the earlier premise.** I previously wrote as if WeKnora, Hermes, and OpenClaw all spoke the E2B protocol. That is not true: WeKnora speaks E2B, while Hermes and OpenClaw have their own backend lists that do not include E2B. Running them inside sandboxes is therefore per-agent integration work with its own templates, not a free side effect of a shared API.[32]

**Option 3 only if native Kubernetes isolation is a hard requirement.** Nitro Sandboxes give the strongest and cheapest-to-operate per-pod isolation, but they have no sandbox API, so WeKnora needs a new adapter, and snapshot and pause have no equivalent.[49][40]

## Option 1 · CubeSandbox on EKS Jakarta

What it needs:

- An EKS cluster on version 1.24 or later, Helm 3.10 or later, and a working StorageClass.[16]
- Control-plane nodes of at least 4 vCPU and 8 GB, preferably three nodes in production.[16]
- **Bare-metal** compute nodes, because sandboxes need real KVM on `/dev/kvm`.[16][18] Available in Jakarta: `c7i.metal-24xl`, `m7i.metal-24xl`, and `i7i.metal-24xl` among others.[24]
- An XFS data disk at `/data/cubelet` for the copy-on-write path, with a dedicated disk rather than the default 25 GB loopback.[16][7]
- Images mirrored from Tencent's registry into ECR Jakarta, because cross-border pulls are slow and expensive.[1][28]
- MySQL, Redis, and MinIO either shipped by the chart or replaced with RDS and ElastiCache in the same Region.[17][26]
- Wildcard DNS for the `<port>-<sandboxId>.<domain>` pattern, or the path and header modes instead.[17]

WeKnora code change: **none.** The `cube` backend already exists, complete with default endpoint, domain, and TTL.[32] The one thing to confirm is that the template image carries `envd` on port 49983 so Cube's build probe passes, which is why WeKnora ships the `weknora-sandbox:main-cube` image.[32]

Sandbox cost estimate, on-demand, excluding the WeKnora application itself:[24][25][26][27][28][29]

| Line | Evaluation (one metal node) | Small production (two metal nodes) |
|---|---|---|
| EKS control plane | $73 | $73 |
| Control node `m7i.2xlarge` | $368 | $1,104 (three nodes, HA) |
| Compute node `c7i.metal-24xl` | $3,606 | $7,211 |
| EBS gp3 (data and PVCs) | $65 | $221 |
| ElastiCache Valkey `cache.r7g.large` | in-cluster Redis instead | $153 |
| NAT gateway and data | $49 | $61 |
| NLB and LCU | $20 | $22 |
| S3 and ECR | $11 | $36 |
| **Total per month** | **$4,191** | **$8,880** |

For Hermes, WeKnora, and OpenClaw, this option covers the most ground: all of them can speak the same E2B API, and AgentHub already provides a pattern for running long-lived OpenClaw assistants inside sandboxes.[14][5]

## Option 2 · E2B Embed on one EC2 instance in Jakarta

E2B Embed runs the whole E2B stack on one machine, and there is an official Terraform module for AWS. `terraform apply` creates one Ubuntu 24.04 instance along with a VPC, an Elastic IP, a security group, an IAM role, an S3 bucket, and a launch template; the instance answers `GET /health` about three minutes after apply returns.[51][45]

What it needs:

- An instance type that exposes `/dev/kvm`: a nested-virtualization type or an x86-64 `.metal` type.[45][22] The module defaults to `m8i.xlarge`, and **m8i is not available in Jakarta**, so override it to `m7i.xlarge`, `c7i.xlarge`, or `r7i.xlarge`, all of which exist in this Region.[45][47][24]
- The module sets `cpu_options { nested_virtualization = "enabled" }` for non-metal types and skips it for metal types. It also validates that the chosen type is actually offered in the selected zone.[48][47]
- A 50 GB encrypted gp3 root volume by default, which is a parameter worth raising because templates and snapshots live locally.[47][45]
- TLS in front, because Embed serves plain HTTP with no certificate of its own; an ALB with ACM is the simplest answer.[51]
- Only ports 3000, 3001, and 3002 need to be reachable by SDK clients. Port 5008 is an unauthenticated control API and must be firewalled.[46]
- A default ceiling of 200 sandboxes per node and 3 simultaneous starts, which is a configured limit rather than a density promise.[46]
- Real density comes from the hugepage pool, not from that 200. A sandbox reserves its whole guest memory in the pool when it starts, idle or not, and `HUGEPAGES=2048` gives a 4 GiB pool, which is about eight 512 MiB sandboxes.[63]
- The compose documentation's floor is 12 GiB RAM and 20 GiB free disk. Pausing holds disk equal to the sandbox's memory and is refused if the disk cannot take it, while a snapshot needs that sandbox's memory a second time while it is taken.[63]
- The stack pulls images and binaries from the internet: Docker Hub, `us-docker.pkg.dev`, `storage.googleapis.com`, `github.com`, and `raw.githubusercontent.com`. All public with no token, but the pulls cross borders, so this is an outbound dependency to account for in a closed network.[63]
- Per-initiative quota lives in the Postgres `default_limits` and `project_limits` tables with `concurrent_sandboxes` and `max_length_hours` columns, so one node can serve several projects with their own allowances.[63]

WeKnora code change: **none.** The `e2b` backend already exists, and its client is explicitly written for any E2B-compatible control plane rather than only E2B Cloud.[32] Two things belong in the spike: Embed separates `E2B_API_URL` from `E2B_SANDBOX_URL` while the WeKnora E2B client uses its own domain routing, and Embed's team API key has to line up with the configuration fields WeKnora exposes.[45][32]

Cost, excluding the WeKnora application itself:[24][27]

| Line | Small (m7i.xlarge, 4 vCPU) | Medium (m7i.2xlarge, 8 vCPU) |
|---|---|---|
| EC2 | $184 | $368 |
| EBS gp3 root and snapshots | $29 | $73 |
| S3 | $5 | $13 |
| ALB and LCU | $20 | $22 |
| **Total per month** | **$238** | **$475** |

The $238 in the small column assumes generous disks: a 200 GB root plus 200 GB of snapshots plus 200 GB of S3, because templates and snapshots live on that machine. With the module's 50 GB root default the figure drops to about $215. That is a capacity assumption, not an arithmetic error.[47]

A 16 GB node suits one lightweight agent. Once several initiatives run at the same time, node memory is the hard limit, because every sandbox holds its own guest memory in the hugepage pool, and pause is not documented as releasing that reservation.[63]

One more upside for your wider goal: templates are built from Dockerfiles, so a Hermes image or any other agent image becomes a template more comfortably than Cube's OCI-to-template flow, and anything that speaks E2B can point at the same control plane. Fork is not mentioned in the Embed documentation even though the runtime supports it, so that belongs on the spike checklist.[51][55]

Limitations worth stating up front:

- **No persistent data volume.** Replacing the instance gives you a fresh instance, and it takes about 14 minutes, so templates, snapshots, and paused sessions are all gone. Auto-recovery means starting from zero, not high availability.[45]
- **One team per install.** The API key is generated per install, so every application shares the same quota, uses the same admin key, and can see each other's sandboxes.[62]
- **Default quotas are small and changed through SQL.** The documentation's example raises `concurrent_sandboxes` to 100 and `max_length_hours` to 24 directly in its Postgres, which means the defaults sit well below that.[63]

Risks to accept: Embed is a single-machine product, so the Auto Scaling group of one gives auto-recovery rather than high availability, and the route to capacity across machines is BYOC or private cloud, both enterprise offerings.[51][60] It also depends on a startup, so the direction of their self-hosting roadmap is worth watching.

## Option 3 · Nitro Sandboxes on EKS Jakarta

Nitro Sandboxes run every pod in its own microVM with its own kernel, and on EKS you enable it with one line, `runtimeClassName: isolated-sandbox`.[49] The feature is available in all commercial AWS Regions at no additional charge and requires Kubernetes 1.36 or later.[49][59][58] In Jakarta, EKS Auto Mode is available, so there is no AMI to build because Auto Mode supplies the runtime class and matching nodes.[61]

What it needs:

- A cluster on 1.36 or later; version 1.36 and its features are available in all EKS Regions.[58][57]
- A node pool with instance types on the Nitro Sandboxes list, and that list **excludes `.metal` and `-flex` types**.[50] Types available in Jakarta that qualify include `m6i`, `m5`, `c5`, `c7i`, and `i7i` at `.xlarge` and above.[50][24]
- RBAC for a ServiceAccount that creates, execs into, and deletes pods in the sandbox namespace.[49]
- Use `isolated-sandbox`, not `confidential-sandbox`, because confidential mode denies `exec`, `stdin`, and logs to the parent instance, which would break WeKnora's `shell_exec` and terminal.[49]
- Avoid the `sandbox.amazonaws.com/network-isolated` annotation if the sandbox needs the internet, because it removes the network device entirely, which also kills `kubectl port-forward` and HTTP probes.[49]

WeKnora code change: **yes, and this is real work.** Nitro Sandboxes are not a sandbox control plane, so a new adapter must implement `RemoteSandboxClient`: 15 required methods covering provider, capabilities, health, create, connect, get, list, delete, exec, and file operations, plus declarations across 10 capability flags so unsupported features degrade automatically.[40] What cannot be preserved is snapshot and pause or resume; terminals have to be built on exec, the desktop needs its own path, and per-domain egress policy has no equivalent.[38][40] For Hermes and OpenClaw, this route means building your own orchestration on top of the CRDs and RuntimeClass, for example with agent-sandbox.[56]

Cost, excluding the WeKnora application itself and excluding development effort:[24][25][28][29]

| Line | Small (2 × m6i.2xlarge) | Medium (4 × m6i.4xlarge) |
|---|---|---|
| EKS control plane | $73 | $73 |
| Sandbox nodes | $701 | $2,803 |
| EKS Auto Mode management fee | $84 | $336 |
| EBS gp3 root and PVCs | $77 | $230 |
| NAT gateway | private subnets with VPC endpoints instead | $55 |
| ALB and LCU | $22 | $25 |
| S3 and ECR | $11 | $23 |
| **Total per month** | **$967** | **$3,545** |

This is the cheapest option to operate and the strongest on isolation, but it is also the only one that requires changing WeKnora code while giving up three of the capabilities that make sandboxes valuable for agents.[49][40]

## Option 4 · OpenSandbox on EKS Jakarta

OpenSandbox is a general-purpose sandbox platform for AI applications: a project under the Agentic AI Foundation, Apache-2.0 licensed, written in Go, and actively developed.[69][65] Its surface is broad, with SDKs for Python, JavaScript, Java and Kotlin, C#, and Go, the `osb` terminal CLI, an MCP server for clients such as Claude Code and Cursor, and OpenAPI contracts in `specs/` as the source of truth.[65][66]

What separates it from the three options above is that it is Kubernetes-native by design. Its control plane is a FastAPI lifecycle server, and its runtime is either Docker for a single host or Kubernetes, with a workload provider of `BatchSandbox` or `kubernetes-sigs/agent-sandbox`, plus an optional FastSandbox integration for template-backed Firecracker microVMs.[66][67]

The lifecycle API already covers most of what we need: create from an image, snapshot, or template, pause, resume, renew, delete, resolve a port endpoint, plus `resourceLimits` for CPU, memory, GPU, and writable-layer disk, `volumes` for host paths and PVCs, and a per-sandbox `networkPolicy`.[66]

Two modes matter, and they are different products:

- **Container mode.** Runs on ordinary EKS nodes in Jakarta, with no KVM and no bare metal. Isolation is container-level, enforced by Kubernetes, and can be strengthened with a RuntimeClass.[66]
- **MicroVM mode through FastSandbox.** One microVM per sandbox with its own kernel, starting from a snapshot that preserves memory and disk state. It requires a Linux host with KVM, `/dev/net/tun`, cgroup v2, and an XFS state directory with reflink, and its CRD and Fast-Path API are still `v1alpha2`, meaning alpha.[67]

For your needs beyond WeKnora, this comes closest to a real agent sandbox platform: an ingress gateway for inbound traffic, per-sandbox egress policy with DNS and nftables rules, a credential vault so real credentials never enter the sandbox, resource pools and batch creation for evaluation or RL, and examples that run coding agents, browsers, and desktops inside sandboxes.[65][66]

What has to be counted as cost:

- **WeKnora has no OpenSandbox backend.** The server knows `docker`, `cube`, `e2b`, `host`, and `disabled`, so this means a new adapter, or an E2B-compatible gateway in front of OpenSandbox.[32]
- Such a gateway exists, with adapters for both `agent-sandbox` and OpenSandbox, but the project has 10 stars and is still shaped like a design document, so it does not belong on a production critical path yet.[68]
- A lost Fastlet Pod destroys the live instances inside it, and persistent storage for FastSandbox is explicitly out of scope.[67]
- The latest umbrella releases carry a tracked signing and provenance gap, so image verification deserves real attention.[65]

Cost follows the same pattern as the other Kubernetes options, using cheaper Graviton nodes:[24][25][27][28][29]

| Line | Two m7g.2xlarge nodes, managed node group | Two m7g.2xlarge nodes, Auto Mode |
|---|---|---|
| EKS control plane | $73 | $73 |
| Sandbox nodes | $596 | $596 |
| EKS Auto Mode management fee | none | $71 |
| EBS gp3 root and PVCs | $77 | $77 |
| ALB and LCU | $22 | $22 |
| S3 and ECR | $11 | $11 |
| **Total per month** | **$779** | **$850** |

If the microVM mode is needed later, add a bare-metal node: one `c7i.metal-24xl` plus a control node and the rest of the platform lands around $4,180 per month, and it carries the same XFS and KVM requirements as CubeSandbox.[24][67]

## Normalized cost

Comparing monthly totals across options misleads, because the vCPU counts differ by an order of magnitude. Memory is what actually bounds sandbox capacity: every sandbox holds its own guest memory, whether in Embed's hugepage pool, in Kubernetes node RAM, or inside a microVM. The honest column is therefore cost per GiB of sandbox memory per month.

| Option and configuration | Monthly total | Sandbox RAM (GiB) | $ per GiB-month |
|---|---|---|---|
| Option 2 · Embed, `m7i.xlarge` | $238 | 16 | $14.9 |
| Option 2 · Embed, `m7i.2xlarge` | $475 | 32 | $14.8 |
| Option 4 · OpenSandbox containers, 2 × `m7g.2xlarge`, managed node group | $779 | 64 | $12.2 |
| Option 4 · OpenSandbox containers, 2 × `m7g.2xlarge`, Auto Mode | $850 | 64 | $13.3 |
| Option 3 · Nitro, 2 × `m6i.2xlarge` | $967 | 64 | $15.1 |
| Option 3 · Nitro, 4 × `m6i.4xlarge` | $3,545 | 256 | $13.8 |
| Option 1 · CubeSandbox, 1 × `c7i.metal-24xl` and one control node | $4,191 | 192 | $21.8 |
| Option 1 · CubeSandbox, 2 × `c7i.metal-24xl` and three control nodes | $8,880 | 384 | $23.1 |

Three things follow from the table.[24][25]

- Embed remains the cheapest entry point, because there is no cluster to pay for. The $180 to $250 per month of control plane, ALB, and NAT is what makes the Kubernetes options pay off only once capacity is actually used.
- Per GiB of memory, the Kubernetes-based options are the cheapest, and bare-metal CubeSandbox is the most expensive, roughly 50 percent above the container options.
- These figures count all node memory as sandbox capacity. In practice reserve about 10 percent for the system and platform components, and read the table as a relative comparison rather than a density promise.

## What every option shares

- A host for the WeKnora application itself. Its documentation suggests around 4 cores and 8 GB, which can be one small EC2 instance in Jakarta or one extra node in the cluster.[53]
- Postgres and the document-parsing components, which can run as containers on that same host.
- Object storage in S3 Jakarta.[27]
- An LLM endpoint. Bedrock is available in this Region, so an in-region path stays open, or use an external vendor with credentials held by the CubeEgress proxy.[26]
- None of the figures above include tax, public IPv4 address charges, data transfer out, or LLM spend.
- Prices come from the regional price list, which proves the SKU is offered in Jakarta, not that quota or capacity is immediately available in our account.[24]

## Next steps

1. Spike A, about one day: `terraform apply` E2B Embed on `m7i.xlarge` in Jakarta, put an ALB and ACM in front, point WeKnora's `e2b` backend at it, then measure create latency, pause and resume, snapshot, and whether the api and sandbox URL configuration is sufficient.[45][32]
2. If Spike A passes, move up to `m7i.2xlarge` or larger based on measured density, and make it the default sandbox platform for WeKnora and Hermes.[24]
3. Spike B, about two to three days: one `c7i.metal-24xl` node running CubeSandbox, to compare cold start, density, and snapshot behaviour against Embed, and to prepare the multi-node path if one machine becomes the limit.[16][24]
4. Spike C, about three to five days: OpenSandbox on EKS Jakarta with the `agent-sandbox` provider on ordinary Graviton nodes, to exercise its lifecycle API, ingress gateway, per-sandbox egress policy, and credential vault. This is the shared-platform candidate for Hermes and OpenClaw, and it composes with Nitro as a RuntimeClass.[66][49]
5. Defer Option 3 as a sandbox product until there is a genuinely hard requirement for native Kubernetes isolation, because its price is code changes plus losing snapshot and pause. Its most sensible role today is the isolation layer under another platform.[40][49]

## Open questions

- Who owns agent lifecycle and tenant isolation: our application, or the sandbox control plane.
- Whether the LLM must stay in-region through Bedrock, or an external vendor with credentials held by the egress proxy is acceptable.
- If WeKnora is forked, whether the Nitro adapter would be upstreamed later or kept internal.

## Sources

[1] https://raw.githubusercontent.com/TencentCloud/CubeSandbox/master/deploy/kubernetes/chart/values.yaml
[5] https://raw.githubusercontent.com/TencentCloud/CubeSandbox/master/docs/guide/digital-assistant.md
[7] https://raw.githubusercontent.com/TencentCloud/CubeSandbox/master/docs/guide/quickstart.md
[9] https://raw.githubusercontent.com/TencentCloud/CubeSandbox/master/docs/changelog/v0.8.0.md
[11] https://cubesandbox.com/changelog/v0.6.0
[14] https://cubesandbox.com/guide/introduction
[15] https://cubesandbox.com/guide/kubernetes
[16] https://cubesandbox.com/guide/kubernetes/install
[17] https://cubesandbox.com/guide/kubernetes/architecture.html
[18] https://cubesandbox.com/guide/kubernetes/faq.html
[19] https://cubesandbox.com/architecture/overview
[22] https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html
[24] https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/ap-southeast-3/index.json
[25] https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEKS/current/ap-southeast-3/index.json
[26] https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonElastiCache/current/ap-southeast-3/index.json
[27] https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonS3/current/ap-southeast-3/index.json
[28] https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonECR/current/ap-southeast-3/index.json
[29] https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AWSELB/current/ap-southeast-3/index.json
[30] https://cubesandbox.com/guide/tutorials/sdk/python
[32] https://raw.githubusercontent.com/Tencent/WeKnora/main/internal/sandbox/sandbox.go
[38] https://raw.githubusercontent.com/Tencent/WeKnora/main/internal/sandbox/capabilities.go
[40] https://raw.githubusercontent.com/Tencent/WeKnora/main/internal/sandbox/remote_client.go
[45] https://raw.githubusercontent.com/e2b-dev/runtime/main/embed/terraform/aws/README.md
[46] https://raw.githubusercontent.com/e2b-dev/runtime/main/embed/kubernetes/README.md
[47] https://raw.githubusercontent.com/e2b-dev/runtime/main/embed/terraform/aws/variables.tf
[48] https://raw.githubusercontent.com/e2b-dev/runtime/main/embed/terraform/aws/main.tf
[49] https://docs.aws.amazon.com/eks/latest/userguide/sandboxing.html
[50] https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nitro-sandboxes.html
[51] https://raw.githubusercontent.com/e2b-dev/runtime/main/embed/README.md
[53] https://raw.githubusercontent.com/Tencent/WeKnora/main/README.md
[55] https://github.com/e2b-dev/runtime
[56] https://agent-sandbox.sigs.k8s.io/docs/getting_started/overview
[57] https://aws.amazon.com/about-aws/whats-new/2026/06/amazon-eks-distro-kubernetes-version-1-36
[58] https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html
[59] https://aws.amazon.com/about-aws/whats-new/2026/11/nitro-sandboxes-eks-ecs-ec2
[60] https://docs.e2b.dev/byoc
[61] https://docs.aws.amazon.com/eks/latest/userguide/automode-learn-instances.html
[62] https://raw.githubusercontent.com/e2b-dev/runtime/main/embed/docs/REFERENCE.md
[63] https://raw.githubusercontent.com/e2b-dev/runtime/main/embed/compose/README.md
[65] https://raw.githubusercontent.com/opensandbox-group/OpenSandbox/main/README.md
[66] https://raw.githubusercontent.com/opensandbox-group/OpenSandbox/main/docs/architecture/index.md
[67] https://raw.githubusercontent.com/opensandbox-group/fast-sandbox/main/README.md
[68] https://github.com/e2bgateway/e2bgateway
[69] https://github.com/opensandbox-group/OpenSandbox
