# CubeSandbox on EKS Jakarta: microVM sandboxes for agent infrastructure

Research note, 17 November 2026. Every price and regional availability figure comes from the official AWS price list for `ap-southeast-3`, retrieved the same day.

## Short answer

It runs on EKS Jakarta, and almost every dependency is already available in this region.[24][25][26][27][28][29] Three things define the shape of the architecture:

1. Compute nodes must be **bare metal**, because CubeSandbox needs real KVM on `/dev/kvm`.[16][18]
2. The container images still come from Tencent's registry, so they must be mirrored into ECR Jakarta.[1]
3. The Kubernetes deployment path is officially **preview**.[11]

For the "sandbox as agent infrastructure" use case, the model fits: these sandboxes are designed to host long-running agent processes, not just one-shot code execution.[14][19] For Hermes and WeKnora, though, the practical route is the E2B-compatible SDK plus our own templates, not the AgentHub feature.[5][30]

## What CubeSandbox is

CubeSandbox is a MicroVM sandbox service built on RustVMM and KVM, claiming cold starts under 60ms and under 5MB of memory overhead per sandbox.[20][19] Every sandbox gets its own kernel, so there is no shared-kernel escape surface the way there is with containers.[19] It is Apache-2.0 licensed, the latest release is v0.8.0 (12 November 2026), and the core was validated at scale in Tencent Cloud production before open-sourcing.[20][9][14]

What matters for us: the API is compatible with the E2B SDK, so agent code already written against E2B only needs a new endpoint URL.[20][30]

The components split into two layers.[19]

**Control plane** (stateless, all state in Redis):

- `CubeAPI`, the E2B-compatible REST gateway on port 3000.[16][30]
- `CubeMaster`, cluster scheduler and metadata holder, port 8089.[19][17]
- `CubeOps`, ops backend and WebUI, port 3010.[17]
- `CubeProxy`, the HTTP/HTTPS reverse proxy on ports 80/443 that routes traffic to the right sandbox.[19][17]
- `cube-lifecycle-manager`, which handles pause and resume, defaulting to two replicas with leader election.[17]

**Data plane** (per node):

- `Cubelet` on port 9999, managing the sandbox lifecycle on one node.[19][18]
- `CubeShim`, a containerd Shim v2 implementation bridging the runtime and the MicroVM.[19]
- `CubeHypervisor`, the RustVMM and KVM based VMM.[19]
- `CubeVS`, an eBPF virtual switch with three TC programs for SNAT, DNAT, and policy.[19]
- `CubeEgress`, an OpenResty-based L7 egress proxy with domain filtering, credential injection, and auditing.[19][12]
- `CubeCoW`, the copy-on-write engine using the `FICLONE` ioctl for O(1) snapshots and clones.[19][7]

## Architecture on EKS Jakarta

The pattern I would use: one EKS cluster in `ap-southeast-3`, the `cube-system` namespace, the control plane as ordinary Deployments, and the compute plane as DaemonSets on a dedicated bare-metal node group with a taint.[15][17]

A few details drive the design:

- Compute nodes carry the `cube.tencent.com/compute=true:NoSchedule` taint, and `cube-node` runs on the host network by default.[16][17]
- `cube-node` is privileged and uses hostPath, so a scheduling mistake is expensive.[17][18]
- The data disk at `/data/cubelet` **must be XFS**, because the CoW path needs reflink.[16][7] If you do not mount one, the chart creates a 25GB loopback image by default.[16][18]
- The internal sandbox CIDR defaults to `172.16.0.0/18` and must not overlap the cluster Service CIDR; a preflight hook fails fast on a conflict.[1][17]
- MySQL, Redis, and MinIO can be shipped by the chart as StatefulSets, or pointed at managed services via `mysql.host`, `redis.host`, and `volumeS3.*`.[17][1]

![CubeSandbox architecture on EKS Jakarta](diagram-light.png)

## Why compute nodes must be bare metal

This is the part that decides both cost and operations. The bootstrap validates `/dev/kvm`, and the documentation is explicit: physical machines need VT-x or AMD-V enabled, while cloud VMs need PVM.[18]

PVM is a page-table-based nested virtualization framework, and installing it means swapping the host kernel for the OpenCloudOS `kvm_pvm` kernel, adding the `nopti pti=off` boot arguments, and rebooting the node.[16][1] That process touches GRUB, udev, and fstab, and uninstalling the Helm release does not undo any of it.[18][17] On an EKS managed node group that is not realistic, because the AMI is managed by AWS.

So there are two options: a bare-metal node group, or instances that officially support nested virtualization.

AWS supports nested virtualization on the M7i, C7i, R7i, I7i, and I7ie families, enabled through CPU options at launch.[22] But AWS itself recommends bare metal for workloads that are performance or latency sensitive, and the entire CubeSandbox pitch is about sub-100ms latency.[22][19] On top of that, the chart assumes PVM automatically on any node that is not bare metal.[16] To me that is an experiment at best, not a production path.

What is available in Jakarta and relevant:[24]

- `c7i.metal-24xl` at about $4.94 per hour, 96 vCPU.
- `m5.metal` at about $5.76 per hour.
- `m7i.metal-24xl` at about $6.05 per hour.
- `m6i.metal` at about $7.68 per hour.
- `i7i.metal-24xl` at about $10.86 per hour, with local NVMe.
- `i4i.metal` at about $13.17 per hour.

An operational caveat people miss: bare metal instances cannot be stopped and started, only rebooted, and they do not support hibernation.[24] Elasticity is a different class than regular instances, which means scaling compute means provisioning another 96 vCPU host.

## Dependencies and availability in Jakarta

**On the compute host:** KVM, the kernel module, XFS with reflink, cgroup v2, bpffs, glibc 2.31 or newer, and root or privileged access.[1][7] Both x86_64 and ARM64 are supported, but the PVM path is x86_64 only.[7]

**Internal services:** MySQL 8, Redis 7, and an S3-compatible object store for volumes and artifacts, all of which the chart can ship or you can replace with managed services.[17][1] JuiceFS is optional, still preview, and needs FUSE on every node plus a shared metadata store and object store.[9]

**Managed equivalents in Jakarta:** EKS and S3 both have an `ap-southeast-3` price list.[25][27] ElastiCache and ECR are available in the same region.[26][28] EBS gp3, NAT Gateway, and ELB show up there too.[24][29] So MySQL to RDS, Redis to ElastiCache, and MinIO to S3 are all viable in this region.

**What is not automatically there:** the CubeSandbox images are pulled from `cube-sandbox-int.tencentcloudcr.com`.[1] That is not an AWS dependency, and cross-border pulls are both slow and expensive, so mirroring into ECR Jakarta has to be counted as an installation step rather than an optional nicety.[28]

**External at runtime:** sandboxes need a domain for the URL pattern `<port>-<sandboxId>.<domain>`, defaulting to `cube.app`, and clients must resolve wildcard DNS.[16][17] If you would rather not deal with a wildcard, there are path-based and E2B header-based modes. For egress, `allow_internet_access` defaults to `true`, and the L7 rules in CubeEgress are default-deny for traffic that passes through the proxy.[12] Which means domain allowlisting for LLM APIs and everything else is configuration work, not something that is safe out of the box.

## Cost estimate

On-demand Linux pricing, Shared tenancy, Jakarta region, before tax. Metal compute is the line item that dominates everything.

**Evaluation scenario, one metal compute node:**[24][25]

- EKS control plane: $73 per month.
- Control node `m7i.xlarge`: $184 per month.
- Compute `c7i.metal-24xl`: $3,606 per month.
- EBS gp3 260 GB: $25 per month.
- NAT gateway plus 50 GB: $46 per month.
- S3 100 GB plus ECR 30 GB: $6 per month.
- Total around **$3,900 per month**.

**Small production scenario, two metal compute nodes with an HA control plane:**[24][25]

- EKS control plane: $73 per month.
- Three control nodes `m7i.2xlarge`: $1,104 per month.
- Two compute `c7i.metal-24xl`: $7,211 per month.
- EBS gp3 1.3 TB: $125 per month.
- ElastiCache Valkey `cache.r7g.large` plus a replica: $307 per month.
- NAT, NLB, S3 1 TB, ECR 100 GB: $127 per month.
- Total around **$8,950 per month**, excluding RDS MySQL.

The rates themselves are unremarkable: EKS at $0.10 per cluster-hour, gp3 at $0.096 per GB-month, S3 Standard at $0.025 per GB-month match other regions. The metal nodes are what make it expensive.[25][24][27]

## How to use it

Installation goes through Helm, and the order matters.[16][15]

```bash
# 1. Label nodes by role
kubectl label nodes <control-node> cube.tencent.com/cube-control=true --overwrite
kubectl label nodes <compute-node> cube.tencent.com/cube-node=true --overwrite
kubectl taint nodes <compute-node> cube.tencent.com/compute=true:NoSchedule --overwrite

# 2. Values
cp deploy/kubernetes/chart/runtime-values.example.yaml runtime-values.yaml

# 3. Install
helm upgrade --install cube ./deploy/kubernetes/chart \
  -n cube-system --create-namespace -f runtime-values.yaml --wait --timeout 90m
```

On bare-metal nodes, point `bootstrap.pvmHostKernel.enabled` and `cubeNode.pvmGuestKernel.enabled` at `false` so the PVM path stays off.[1][3] Then verify with `helm test`, which checks `/dev/kvm`, the cubelet socket, and the node's network runtime among other things.[16][17]

Templates are built from an OCI image, and the requirement is that the image starts an HTTP server on a fixed port with a probe endpoint returning 2xx, via `cubemastercli tpl create-from-image --expose-port --probe --probe-path`.[7] Clients use `CUBE_API_URL=http://<cubeapi>:3000` plus `CUBE_TEMPLATE_ID`, or the E2B SDK with `E2B_API_URL` pointed at CubeProxy.[30][7]

The lifecycle is what makes this interesting for agents: pause stores a snapshot and pushes CPU and RSS near zero, resume is claimed within hundreds of milliseconds, and clone and rollback work per snapshot point.[14][18] Cross-node pause and resume, however, is still preview and requires an `s3` or `jfs` backend plus identical `cpuid_hash` and `host_kernel_release` on the origin and target nodes.[9][12]

## For Hermes and WeKnora

For Hermes, the pattern that makes most sense is one Hermes image template, one sandbox per agent instance, and lifecycle managed by our own application through the SDK. The reason is that these sandboxes are explicitly designed to host long-lived agent processes and stateful services, not just one-shot code execution.[14][19] LLM credentials can be held in CubeEgress so the API key never enters the sandbox, and that capability already exists in the stable release.[14][19]

AgentHub, the feature whose example uses OpenClaw, should not be the foundation yet.[5] It is preview, and its shape is locked to a particular OpenClaw image layout: ports 18789 and 8080, `supervisorctl` wiring, and a template around 3 GB that needs 12 to 15 GB of free space per template plus snapshots.[5] Making Hermes show up as an assistant in that UI means wrapping Hermes to that contract, and that is extra work that buys nothing for production.

WeKnora is a different weight class: it needs a database, a cache, and document-parsing components. One sandbox per tenant with larger disk and memory is realistic, but template size and `/data/cubelet` capacity have to be recalculated for it.[18]

Two design questions are still open and should be settled before writing a spec: who owns the agent lifecycle (our application or AgentHub), and whether agent state lives in an S3 volume or inside the snapshot.[17]

## Risks worth admitting

- The Kubernetes deployment is preview, with acknowledged issues: pods can be evicted wrongly under node resource pressure, and compute-node upgrades recreate `cube-node`, disrupting sandboxes.[11][15]
- The host-network default has not been validated against every CNI and admission configuration. A cluster enforcing the `restricted` Pod Security Admission standard rejects `hostNetwork` pods, and an eBPF-based CNI such as Cilium can conflict with the cubevs hooks.[16]
- Compute-plane upgrades require draining, and `helm rollback` does not revert kernel, GRUB, or XFS changes, so a separate host runbook is needed.[31][18]
- Cubelet ports 9998, 9999, and 9966 are unauthenticated and bind on the host, so they must be firewalled like kubelet's 10250.[16]
- A `cube-node` rolling update on the pod network cuts network connectivity for every sandbox on that node with no self-healing, which makes draining mandatory rather than optional.[16][18]
- GPU support does not exist yet, it is still on the roadmap.[4]

## Next step

Spike a single node first, and deliberately do not wait for a perfect design. The shape: one `c7i.metal-24xl` bare-metal EC2 instance in Jakarta, a small cluster (k3s or a one-node EKS cluster), install the chart, run `helm test`, then build one Hermes template and measure cold start plus sandbox density per host.[24][16]

That spike answers the three biggest risks at once: whether KVM and its toolchain work on an Amazon Linux kernel, whether XFS reflink and CubeCoW behave as claimed, and what a realistic monthly cost per agent looks like.[16][7][24]

If it passes, move to the production spec. If KVM is a dead end, the fallback is running the compute node outside EKS with the bare-metal installer and leaving EKS for everything else.[7]

## Sources

[1] https://raw.githubusercontent.com/TencentCloud/CubeSandbox/master/deploy/kubernetes/chart/values.yaml
[3] https://raw.githubusercontent.com/TencentCloud/CubeSandbox/master/deploy/kubernetes/chart/README.md
[4] https://raw.githubusercontent.com/TencentCloud/CubeSandbox/master/README.md
[5] https://raw.githubusercontent.com/TencentCloud/CubeSandbox/master/docs/guide/digital-assistant.md
[7] https://raw.githubusercontent.com/TencentCloud/CubeSandbox/master/docs/guide/quickstart.md
[9] https://raw.githubusercontent.com/TencentCloud/CubeSandbox/master/docs/changelog/v0.8.0.md
[11] https://cubesandbox.com/changelog/v0.6.0
[12] https://cubesandbox.com/guide/network-policy
[14] https://cubesandbox.com/guide/introduction
[15] https://cubesandbox.com/guide/kubernetes
[16] https://cubesandbox.com/guide/kubernetes/install
[17] https://cubesandbox.com/guide/kubernetes/architecture.html
[18] https://cubesandbox.com/guide/kubernetes/faq.html
[19] https://cubesandbox.com/architecture/overview
[20] https://github.com/TencentCloud/CubeSandbox
[22] https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html
[24] https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/ap-southeast-3/index.json
[25] https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEKS/current/ap-southeast-3/index.json
[26] https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonElastiCache/current/ap-southeast-3/index.json
[27] https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonS3/current/ap-southeast-3/index.json
[28] https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonECR/current/ap-southeast-3/index.json
[29] https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AWSELB/current/ap-southeast-3/index.json
[30] https://cubesandbox.com/guide/tutorials/sdk/python
[31] https://cubesandbox.com/guide/kubernetes/upgrade
