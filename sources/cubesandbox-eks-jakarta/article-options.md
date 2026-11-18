# Sandbox untuk AI agent di AWS Jakarta: tiga opsi untuk WeKnora

Dokumen keputusan, 17 November 2026. Semua komponen ada di region `ap-southeast-3` (Jakarta), dan semua angka harga diambil dari AWS Price List API region tersebut pada tanggal yang sama. Halaman ini melengkapi catatan riset CubeSandbox di halaman utama.

## Ringkasan keputusan

| | Opsi 1 · CubeSandbox | Opsi 2 · E2B Embed | Opsi 3 · Nitro Sandboxes | Opsi 4 · OpenSandbox |
|---|---|---|---|---|
| Apa itu | Control plane sandbox buatan Tencent, kompatibel E2B, di atas KVM.[14][19] | Seluruh stack E2B di satu mesin, Apache-2.0, tanpa license key.[51][55] | Per-pod Firecracker microVM milik AWS, lewat RuntimeClass.[49] | Platform sandbox umum buat aplikasi AI, proyek Agentic AI Foundation, Apache-2.0.[69][65] |
| Model isolasi | Satu microVM per sandbox, satu kernel per sandbox.[19] | Satu Firecracker microVM per sandbox di dalam satu mesin.[51] | Satu microVM per pod, ditegakkan Nitro hypervisor.[49] | Container di Kubernetes sejak awal, dan microVM Firecracker kalau memakai FastSandbox.[66][67] |
| API | E2B-compatible REST plus SDK resmi.[30] | API dan SDK yang sama dengan E2B Cloud.[51][60] | Tidak ada API sandbox, hanya CRD dan RuntimeClass.[49][56] | API lifecycle sendiri (OpenAPI di `specs/`) plus SDK multi-bahasa, CLI `osb`, dan MCP.[66][65] |
| Patch kode WeKnora | Tidak ada, backend `cube` sudah ada.[32] | Tidak ada, backend `e2b` sudah ada.[32] | Ya, perlu adapter backend baru.[40] | Ya, perlu adapter baru atau gateway E2B-compatible di depan.[32][68] |
| Snapshot, pause, resume | Ada di control plane, cross-node masih preview.[14][9] | Ada, termasuk pause dan resume dengan memori tersimpan.[51] | Tidak ada padanannya.[49] | Ada, dan di FastSandbox memori serta disk ikut tersimpan.[66][67] |
| Skala | Multi-node, satu klaster.[15][17] | Satu mesin by design, ASG of one.[51][60] | Banyak node, dikelola EKS.[49] | Multi-node, K8s-native, ada resource pool dan batch creation.[66] |
| Biaya sandbox per bulan | $4.191 (eval) sampai $8.880.[24][25] | $238 (m7i.xlarge) sampai $475 (m7i.2xlarge).[24][27] | $967 (2 node) sampai $3.545 (4 node).[24][25] | $779 (2 node, managed node group) sampai $850 (Auto Mode).[24][25] |
| Kelebihan | API E2B plus AgentHub untuk assistant OpenClaw.[5][14] | Titik masuk termurah, template dari Dockerfile, tanpa cluster.[51] | Isolasi per pod paling kuat dengan biaya operasi paling rendah.[49] | Ingress, egress per sandbox, credential vault, dan microVM opsional, semuanya K8s-native.[65][66] |
| Kelemahan | Butuh node bare metal, jalur Kubernetes masih preview.[16][11] | Satu mesin, tanpa volume persisten, satu team per install.[45][62] | Wajib ubah kode WeKnora dan kehilangan snapshot serta pause.[40] | Butuh integrasi baru, mode microVM masih alpha, dan gateway E2B-nya masih sangat muda.[67][68] |

## Rekomendasi

**Mulai dari Opsi 2.** E2B Embed memberi API yang sudah dimengerti WeKnora tanpa satu baris pun perubahan kode, mempertahankan snapshot serta pause dan resume, dan berjalan di instance biasa di Jakarta tanpa bare metal.[51][60][32] Biaya sandbox-nya mulai sekitar $238 per bulan, tapi angka itu untuk satu node 16 GB yang menurut dokumen compose hanya cukup untuk sekitar delapan sandbox kecil dengan pool memori defaultnya, jadi rencana multi-agent harus dimulai dari node 32 GB atau lebih besar.[24][63]

**Opsi 1 adalah jalur platform kalau butuh multi-node.** CubeSandbox memberi API yang sama tapi dalam klaster yang bisa tumbuh, dan dia yang punya cerita agent hosting paling matang lewat AgentHub.[14][5] Harga yang dibayar adalah node bare metal dan status preview pada jalur Kubernetes.[16][11]

**Opsi 4 adalah kandidat platform bareng, bukan pengganti Embed untuk minggu ini.** OpenSandbox satu-satunya yang K8s-native, multi-node, dan sudah membawa ingress, egress per sandbox, serta credential vault, dan mode microVM-nya opsional. Harganya adalah integrasi baru ke WeKnora dan toleransi terhadap komponen yang masih alpha di beberapa bagian.[66][67][68]

**Satu koreksi penting soal premis awal.** Gw sebelumnya menulis seolah WeKnora, Hermes, dan OpenClaw semuanya bicara protokol E2B. Itu tidak benar: WeKnora yang bicara E2B, sedangkan Hermes dan OpenClaw punya daftar backend sendiri yang tidak memuat E2B. Jadi kalau mereka dijalankan di dalam sandbox, itu kerja integrasi per agent dengan template sendiri, bukan efek samping gratis dari API yang sama.[32]

**Opsi 3 hanya kalau isolasi native Kubernetes jadi syarat keras.** Nitro Sandboxes memberi isolasi per pod paling kuat dan paling murah dikelola, tapi tidak punya API sandbox, jadi WeKnora perlu adapter baru, dan snapshot serta pause kehilangan padanannya.[49][40]

## Opsi 1 · CubeSandbox di EKS Jakarta

Yang perlu disiapkan:

- Klaster EKS versi 1.24 atau lebih baru, Helm 3.10 atau lebih baru, dan StorageClass yang berfungsi.[16]
- Node control plane minimal 4C8G, lebih baik tiga node untuk produksi.[16]
- Node compute **bare metal**, karena sandbox butuh KVM asli di `/dev/kvm`.[16][18] Yang tersedia di Jakarta termasuk `c7i.metal-24xl`, `m7i.metal-24xl`, dan `i7i.metal-24xl`.[24]
- Data disk XFS di `/data/cubelet` untuk jalur copy-on-write, disarankan disk khusus, bukan loopback default 25 GB.[16][7]
- Mirror image dari registry Tencent ke ECR Jakarta, karena tarikan lintas negara lambat dan mahal.[1][28]
- MySQL, Redis, dan MinIO bisa dibawa sendiri oleh chart, atau diganti RDS dan ElastiCache di region yang sama.[17][26]
- Wildcard DNS untuk pola `<port>-<sandboxId>.<domain>` atau pakai mode path dan header.[17]

Patch WeKnora: **tidak ada.** Backend `cube` sudah ada di source, lengkap dengan default endpoint, domain, dan TTL.[32] Yang perlu dipastikan hanya image template harus memuat `envd` di port 49983 supaya probe build Cube lolos, dan itu sebabnya WeKnora menyediakan image `weknora-sandbox:main-cube`.[32]

Estimasi biaya sandbox, on-demand, di luar aplikasi WeKnora sendiri:[24][25][26][27][28][29]

| Baris | Evaluasi (1 node metal) | Produksi kecil (2 node metal) |
|---|---|---|
| EKS control plane | $73 | $73 |
| Node control `m7i.2xlarge` | $368 | $1.104 (3 node, HA) |
| Node compute `c7i.metal-24xl` | $3.606 | $7.211 |
| EBS gp3 (data dan PVC) | $65 | $221 |
| ElastiCache Valkey `cache.r7g.large` | pakai Redis in-cluster | $153 |
| NAT gateway dan data | $49 | $61 |
| NLB dan LCU | $20 | $22 |
| S3 dan ECR | $11 | $36 |
| **Total per bulan** | **$4.191** | **$8.880** |

Untuk Hermes, WeKnora, dan OpenClaw, opsi ini yang paling lengkap: semuanya bisa bicara API E2B yang sama, dan AgentHub sudah menyediakan pola untuk menjalankan assistant OpenClaw sebagai proses panjang umur di dalam sandbox.[14][5]

## Opsi 2 · E2B Embed di satu EC2 Jakarta

E2B Embed menjalankan seluruh stack E2B pada satu mesin, dan di AWS ada module Terraform resminya. `terraform apply` membuat satu instance Ubuntu 24.04 beserta VPC, Elastic IP, security group, IAM role, S3 bucket, dan launch template; instance menjawab `GET /health` sekitar tiga menit setelah apply selesai.[51][45]

Yang perlu disiapkan:

- Instance type yang mengekspos `/dev/kvm` ke instance: tipe nested virtualization atau tipe `.metal` x86-64.[45][22] Default module adalah `m8i.xlarge`, dan **m8i tidak tersedia di Jakarta**, jadi override ke `m7i.xlarge` atau `c7i.xlarge` atau `r7i.xlarge`, yang ketiganya ada di region ini.[45][47][24]
- Module menyalakan `cpu_options { nested_virtualization = "enabled" }` untuk tipe non-metal, dan melewatinya untuk tipe metal. Dia juga memvalidasi bahwa tipe tersebut benar-benar ditawarkan di zona yang dipilih.[48][47]
- Root volume 50 GB gp3 terenkripsi secara default, dan itu parameter yang bisa dinaikkan karena template serta snapshot disimpan lokal.[47][45]
- TLS di depan karena Embed hanya bicara HTTP polos tanpa sertifikat sendiri; ALB plus ACM adalah cara paling sederhana.[51]
- Hanya port 3000, 3001, dan 3002 yang perlu dijangkau klien SDK. Port 5008 adalah control API tanpa autentikasi dan harus difirewall.[46]
- Batas default satu node 200 sandbox dan 3 mulai bersamaan, dan itu batas konfigurasi, bukan janji kepadatan.[46]
- Kepadatan nyata ditentukan pool hugepages, bukan angka 200 tadi. Satu sandbox menahan seluruh memori guest-nya di pool itu saat start, dalam keadaan idle sekalipun, dan dengan `HUGEPAGES=2048` pool-nya 4 GiB, yang berarti hanya sekitar delapan sandbox berukuran 512 MiB.[63]
- Kebutuhan minimum menurut dokumen compose adalah 12 GiB RAM dan 20 GiB disk bebas. Pause menahan disk sebesar memori sandbox dan bisa ditolak kalau disk tidak cukup, sementara snapshot butuh memori sandbox itu untuk kedua kalinya selama proses pengambilan.[63]
- Stack ini menarik image dan binary dari internet: Docker Hub, `us-docker.pkg.dev`, `storage.googleapis.com`, `github.com`, dan `raw.githubusercontent.com`. Semuanya publik tanpa token, tapi tarikannya lintas negara, jadi ini dependency keluar yang perlu dihitung untuk lingkungan tertutup.[63]
- Kuota per inisiatif diatur lewat tabel `default_limits` dan `project_limits` di Postgres-nya, dengan kolom `concurrent_sandboxes` dan `max_length_hours`, jadi satu node bisa melayani beberapa proyek dengan jatah masing-masing.[63]

Patch WeKnora: **tidak ada.** Backend `e2b` sudah ada, dan client-nya memang dirancang untuk control plane apa pun yang kompatibel E2B, bukan hanya cloud E2B.[32] Dua hal yang harus diuji di spike: Embed memisahkan `E2B_API_URL` dan `E2B_SANDBOX_URL`, sementara client E2B di WeKnora memakai domain routing sendiri, dan model team API key Embed perlu dicocokkan ke field konfigurasi WeKnora.[45][32]

Biaya, di luar aplikasi WeKnora sendiri:[24][27]

| Baris | Kecil (m7i.xlarge, 4 vCPU) | Sedang (m7i.2xlarge, 8 vCPU) |
|---|---|---|
| EC2 | $184 | $368 |
| EBS gp3 root dan snapshot | $29 | $73 |
| S3 | $5 | $13 |
| ALB dan LCU | $20 | $22 |
| **Total per bulan** | **$238** | **$475** |

Angka $238 di kolom kecil memakai asumsi disk yang luas, 200 GB root plus 200 GB snapshot plus 200 GB S3, karena template dan snapshot disimpan di mesin itu sendiri. Kalau memakai default module yaitu root 50 GB, angkanya turun ke sekitar $215. Selisih ini soal asumsi kapasitas, bukan kesalahan hitung.[47]

Node 16 GB cocok untuk satu agent ringan. Begitu beberapa inisiatif jalan bersamaan, memori node menjadi batas kerasnya, karena setiap sandbox menahan memori guest-nya sendiri di pool hugepages, dan pause tidak disebut melepaskan cadangan itu.[63]

Kelebihan lain untuk kebutuhan lu di luar WeKnora: template dibangun dari Dockerfile, jadi image Hermes atau agen lain bisa dijadikan template dengan cara yang lebih nyaman dibanding alur OCI ke template Cube, dan siapa pun yang bicara E2B bisa menunjuk ke control plane yang sama. Fork belum disebut di dokumen Embed meskipun ada di runtime-nya, jadi itu satu hal yang perlu dicek di spike.[51][55]

Keterbatasan yang perlu diakui di muka:

- **Tidak ada volume data persisten.** Mengganti instance sama dengan mendapat instance baru, dan prosesnya sekitar 14 menit, jadi template, snapshot, dan session yang sedang di-pause ikut hilang. Auto-recovery berarti mulai dari nol, bukan high availability.[45]
- **Satu team per install.** Kunci API dibuat per instalasi, jadi semua aplikasi berbagi kuota yang sama, memakai kunci admin yang sama, dan bisa melihat sandbox satu sama lain.[62]
- **Kuota defaultnya kecil dan diubah lewat SQL.** Contoh di dokumen menaikkan `concurrent_sandboxes` ke 100 dan `max_length_hours` ke 24 langsung ke Postgres-nya, yang berarti default-nya jauh di bawah itu.[63]

Risiko yang harus diakui: Embed adalah produk satu mesin, jadi Auto Scaling group berisi satu instance itu auto-recovery, bukan high availability, dan jalan untuk melipatgandakan kapasitas lintas mesin adalah BYOC atau private cloud yang bersifat enterprise.[51][60] Selain itu ini menyandarkan diri pada startup, jadi arah roadmap self-host mereka perlu dipantau.

## Opsi 3 · Nitro Sandboxes di EKS Jakarta

Nitro Sandboxes menjalankan setiap pod di microVM sendiri dengan kernel sendiri, dan di EKS pengaktifannya satu baris `runtimeClassName: isolated-sandbox`.[49] Fitur ini tersedia di semua commercial region AWS tanpa biaya tambahan, dan butuh klaster Kubernetes 1.36 atau lebih baru.[49][59][58] Di Jakarta, EKS Auto Mode tersedia, jadi tidak perlu membangun AMI sendiri karena Auto Mode menyediakan runtime class dan node yang sesuai.[61]

Yang perlu disiapkan:

- Klaster 1.36 atau lebih baru, dan versi 1.36 serta fitur-fiturnya tersedia di semua region EKS.[58][57]
- Node pool dengan instance yang masuk daftar Nitro Sandboxes, dan daftarnya **mengecualikan tipe `.metal` dan tipe `-flex`**.[50] Yang tersedia di Jakarta dan memenuhi syarat antara lain `m6i`, `m5`, `c5`, `c7i`, dan `i7i` pada ukuran `.xlarge` ke atas.[50][24]
- RBAC untuk ServiceAccount yang membuat, mengeksekusi, dan menghapus pod di namespace sandbox.[49]
- Pakai mode `isolated-sandbox`, bukan `confidential-sandbox`, karena mode confidential menolak `exec`, `stdin`, dan log dari parent instance, yang berarti `shell_exec` dan terminal WeKnora tidak akan berjalan.[49]
- Jangan memakai anotasi `sandbox.amazonaws.com/network-isolated` kalau sandbox perlu internet, karena anotasi itu mencabut perangkat jaringan sepenuhnya sehingga `kubectl port-forward` dan probe HTTP mati.[49]

Patch WeKnora: **ya, dan ini pekerjaan nyata.** Nitro Sandboxes bukan control plane sandbox, jadi harus ada adapter baru yang mengimplementasikan `RemoteSandboxClient`: 15 method wajib untuk provider, capability, health, create, connect, get, list, delete, exec, dan operasi berkas, plus deklarasi 10 capability flag agar fitur yang tidak didukung degradasi otomatis.[40] Yang tidak bisa dipertahankan adalah snapshot dan pause serta resume, terminal harus dibuat sendiri lewat exec, desktop butuh jalur sendiri, dan policy egress per domain tidak ada padanannya.[38][40] Untuk Hermes dan OpenClaw, jalur ini berarti membangun orkestrasi sendiri di atas CRD dan RuntimeClass, misalnya dengan agent-sandbox.[56]

Biaya, di luar aplikasi WeKnora sendiri dan di luar biaya pengembangan:[24][25][28][29]

| Baris | Kecil (2 × m6i.2xlarge) | Sedang (4 × m6i.4xlarge) |
|---|---|---|
| EKS control plane | $73 | $73 |
| Node sandbox | $701 | $2.803 |
| Biaya management EKS Auto Mode | $84 | $336 |
| EBS gp3 root dan PVC | $77 | $230 |
| NAT gateway | pakai subnet privat dengan VPC endpoint | $55 |
| ALB dan LCU | $22 | $25 |
| S3 dan ECR | $11 | $23 |
| **Total per bulan** | **$967** | **$3.545** |

Opsi ini yang paling murah untuk dioperasikan dan yang paling kuat isolasinya, tapi juga satu-satunya yang meminta kita mengubah kode WeKnora sekaligus kehilangan tiga kemampuan yang justru jadi nilai jual sandbox untuk agent.[49][40]

## Opsi 4 · OpenSandbox di EKS Jakarta

OpenSandbox adalah platform sandbox umum untuk aplikasi AI: proyek di bawah Agentic AI Foundation, lisensi Apache-2.0, ditulis dengan Go, dan aktif dikembangkan.[69][65] Permukaannya lengkap, ada SDK Python, JavaScript, Java dan Kotlin, C#, dan Go, CLI `osb` untuk terminal, server MCP untuk klien seperti Claude Code dan Cursor, dan kontrak OpenAPI di `specs/` sebagai sumber kebenaran.[65][66]

Yang membedakannya dari tiga opsi di atas: dia K8s-native sejak desainnya. Control plane-nya server FastAPI yang mengurus lifecycle, dan runtime-nya bisa Docker untuk satu host atau Kubernetes, dengan workload provider `BatchSandbox` bawaan atau `kubernetes-sigs/agent-sandbox`, plus integrasi opsional FastSandbox untuk microVM Firecracker berbasis template.[66][67]

API lifecycle-nya sudah mencakup hampir semua yang kita butuhkan: create dari image, snapshot, atau template, pause, resume, perpanjang umur, delete, resolve endpoint port, plus `resourceLimits` untuk CPU, memori, GPU, dan disk lapisan tulis, `volumes` untuk host path dan PVC, dan `networkPolicy` per sandbox.[66]

Dua mode yang perlu dipisahkan:

- **Mode container.** Jalan di node EKS biasa di Jakarta, tidak butuh KVM dan tidak butuh bare metal. Isolasinya container, ditegakkan lewat Kubernetes, dan bisa diperkuat dengan RuntimeClass.[66]
- **Mode microVM lewat FastSandbox.** Satu sandbox satu microVM dengan kernel sendiri, dan startup dari snapshot yang menyimpan state memori serta disk. Syaratnya host Linux dengan KVM, `/dev/net/tun`, cgroup v2, dan direktori state XFS dengan reflink, dan versi CRD serta Fast-Path API-nya masih `v1alpha2` alias alpha.[67]

Untuk kebutuhan lu di luar WeKnora, ini yang paling mendekati "platform sandbox agent": ada ingress gateway untuk trafik masuk, egress policy per sandbox dengan policy DNS dan nftables, credential vault supaya kredensial asli tidak masuk ke sandbox, resource pool dan batch creation untuk evaluasi atau RL, serta contoh menjalankan coding agent, browser, dan desktop di dalam sandbox.[65][66]

Yang harus dihitung sebagai biaya:

- **WeKnora belum punya backend OpenSandbox.** Server WeKnora mengenal `docker`, `cube`, `e2b`, `host`, dan `disabled`, jadi ini berarti adapter baru, atau menaruh gateway E2B-compatible di depannya.[32]
- Gateway seperti itu memang ada, dan punya adapter untuk `agent-sandbox` maupun OpenSandbox, tapi proyeknya masih 10 bintang dan bentuknya masih dokumen desain, jadi jangan dijadikan jalur kritis produksi dulu.[68]
- Fastlet Pod yang mati menghancurkan instance yang hidup di dalamnya, dan persistent storage untuk FastSandbox masih di luar cakupan proyek.[67]
- Rilis umbrella terbaru OpenSandbox punya celah sign dan provenance yang masih dicatat sebagai issue, jadi verifikasi image harus diperlakukan serius.[65]

Biaya, dengan pola yang sama seperti opsi Kubernetes lain, memakai node Graviton yang lebih murah:[24][25][27][28][29]

| Baris | 2 node m7g.2xlarge, managed node group | 2 node m7g.2xlarge, Auto Mode |
|---|---|---|
| EKS control plane | $73 | $73 |
| Node sandbox | $596 | $596 |
| Biaya management Auto Mode | tidak ada | $71 |
| EBS gp3 root dan PVC | $77 | $77 |
| ALB dan LCU | $22 | $22 |
| S3 dan ECR | $11 | $11 |
| **Total per bulan** | **$779** | **$850** |

Kalau nanti perlu isolasi microVM-nya, tambahkan node bare metal: satu `c7i.metal-24xl` beserta node control dan komponen platform lain jatuh sekitar $4.180 per bulan, dan dengan itu syarat XFS dan KVM-nya sama seperti CubeSandbox.[24][67]

## Biaya yang dinormalisasi

Membandingkan total bulanan antar opsi menyesatkan, karena jumlah vCPU-nya beda jauh. Yang sebenarnya mengikat kapasitas sandbox adalah memori: setiap sandbox menahan memori guest-nya sendiri, entah di pool hugepages Embed, di RAM node Kubernetes, atau di microVM. Jadi kolom yang paling jujur adalah biaya per GiB memori sandbox per bulan.

| Opsi dan konfigurasi | Total bulanan | RAM sandbox (GiB) | $ per GiB-bulan |
|---|---|---|---|
| Opsi 2 · Embed, `m7i.xlarge` | $238 | 16 | $14,9 |
| Opsi 2 · Embed, `m7i.2xlarge` | $475 | 32 | $14,8 |
| Opsi 4 · OpenSandbox container, 2 × `m7g.2xlarge`, managed node group | $779 | 64 | $12,2 |
| Opsi 4 · OpenSandbox container, 2 × `m7g.2xlarge`, Auto Mode | $850 | 64 | $13,3 |
| Opsi 3 · Nitro, 2 × `m6i.2xlarge` | $967 | 64 | $15,1 |
| Opsi 3 · Nitro, 4 × `m6i.4xlarge` | $3.545 | 256 | $13,8 |
| Opsi 1 · CubeSandbox, 1 × `c7i.metal-24xl` dan 1 node control | $4.191 | 192 | $21,8 |
| Opsi 1 · CubeSandbox, 2 × `c7i.metal-24xl` dan 3 node control | $8.880 | 384 | $23,1 |

Tiga hal yang terbaca dari tabel ini.[24][25]

- Titik masuk termurah tetap Embed, karena tidak ada cluster yang harus dibayar. Selisih $180 sampai $250 per bulan untuk kontrol plane, ALB, dan NAT itu yang membuat opsi Kubernetes baru masuk akal setelah kapasitasnya terpakai.
- Per GiB memori, opsi berbasis Kubernetes justru paling murah, dan CubeSandbox yang bare metal paling mahal, sekitar 50 persen di atas opsi container.
- Angka ini menghitung seluruh RAM node sebagai kapasitas sandbox. Dalam praktik sisakan sekitar 10 persen untuk sistem dan komponen platform, dan pakai tabel ini sebagai perbandingan relatif, bukan janji kepadatan.

## Yang sama di semua opsi

- Host untuk aplikasi WeKnora sendiri. Dokumennya menyarankan sekitar 4 core dan 8 GB, dan itu bisa satu EC2 kecil di Jakarta atau satu node tambahan di klaster.[53]
- Postgres dan komponen parsing dokumen, yang bisa jalan sebagai container di host yang sama.
- Object storage di S3 Jakarta.[27]
- Endpoint LLM. Bedrock tersedia di region ini, jadi jalur in-region masih terbuka, atau pakai vendor luar lewat CubeEgress sebagai penjaga kredensial.[26]
- Semua biaya di atas belum termasuk pajak, biaya alamat IPv4 publik, data transfer keluar, dan biaya LLM.
- Harga diambil dari price list region, dan itu membuktikan SKU-nya ditawarkan di Jakarta, bukan bahwa kuota atau kapasitasnya langsung tersedia di akun kita.[24]

## Rencana langkah

1. Spike A, sekitar satu hari: `terraform apply` E2B Embed di `m7i.xlarge` Jakarta, taruh ALB dan ACM di depannya, arahkan backend `e2b` WeKnora ke sana, lalu ukur latensi create, pause dan resume, snapshot, dan apakah konfigurasi api serta sandbox URL cukup.[45][32]
2. Kalau spike A lolos, naikkan ke `m7i.2xlarge` atau lebih besar sesuai kepadatan yang terukur, dan jadikan ini sandbox platform default untuk WeKnora dan Hermes.[24]
3. Spike B, sekitar dua sampai tiga hari: satu node `c7i.metal-24xl` dengan CubeSandbox, untuk membandingkan cold start, kepadatan, dan perilaku snapshot terhadap Embed, sekaligus menyiapkan jalur multi-node kalau kapasitas satu mesin mulai jadi batas.[16][24]
4. Spike C, sekitar tiga sampai lima hari: OpenSandbox di EKS Jakarta dengan provider `agent-sandbox` di node Graviton biasa, untuk menguji API lifecycle-nya, ingress gateway, egress policy per sandbox, dan credential vault. Ini kandidat platform bareng untuk Hermes dan OpenClaw, dan bisa dikomposisikan dengan Nitro sebagai RuntimeClass.[66][49]
5. Tunda Opsi 3 sebagai produk sandbox sampai ada kebutuhan isolasi Kubernetes native yang benar-benar keras, karena harganya adalah perubahan kode plus kehilangan snapshot dan pause. Peran yang paling masuk akal untuk Nitro sekarang adalah lapisan isolasi di bawah platform lain.[40][49]

## Pertanyaan terbuka

- Siapa yang memegang lifecycle agent dan isolasi antar penyewa: aplikasi kita, atau control plane sandbox.
- Apakah LLM-nya harus di dalam region lewat Bedrock, atau cukup vendor luar dengan kredensial dititipkan di proxy egress.
- Kalau WeKnora memang akan di-fork, apakah adapter Nitro nanti diupstream atau dijaga internal.

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
