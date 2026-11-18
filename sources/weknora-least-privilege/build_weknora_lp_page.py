#!/usr/bin/env python3
"""Generate the WeKnora least-privilege issue map page (ID + EN) from one data source."""
import html, os, json, re

OUT = os.path.expanduser("~/.hermes/cache/scratch/weknora-least-privilege")
os.makedirs(os.path.join(OUT, "assets"), exist_ok=True)

BASE = "https://github.com/Tencent/WeKnora/issues/"

def link(n, label=None):
    return f'<a href="{BASE}{n}">#{n}</a>' + (f" {label}" if label else "")

# ---------------------------------------------------------------- data model
# layer: (id, title_id, title_en)
LAYERS = [
    ("l0", "Layer 0 · Identitas &amp; keanggotaan", "Layer 0 · Identity &amp; membership"),
    ("l1", "Layer 1 · ACL level knowledge base", "Layer 1 · Knowledge-base level ACL"),
    ("l2", "Layer 2 · Dokumen &amp; chunk", "Layer 2 · Document &amp; chunk"),
    ("l3", "Layer 3 · Konsumsi lewat agent &amp; MCP", "Layer 3 · Consumption through agents &amp; MCP"),
    ("l4", "Layer 4 · Kredensial mesin", "Layer 4 · Machine credentials"),
    ("l5", "Layer 5 · Lintas layer", "Layer 5 · Cross-cutting"),
]

# n, layer, state, kind, cov_id, cov_en, note_id, note_en
ST = "open"; CL = "closed"; PR = "merged"
ISSUES = [
    (674, "l0", ST, "issue",
     "Pemisahan tugas (system admin / auditor / operator), kontrol registrasi, integrasi LDAP / AD / SSO.",
     "Separation of duties (system admin / auditor / operator), registration control, LDAP / AD / SSO integration.",
     "Dibuka Feb 2026, belum ada respons maintainer.",
     "Opened Feb 2026, no maintainer response yet."),
    (1037, "l0", ST, "issue",
     "Panel user admin: daftar semua user, atur role, disable/delete akun.",
     "Admin user panel: list all users, assign roles, disable/delete accounts.",
     "Belum ada respons maintainer. Sekarang harus lewat SQL.",
     "No maintainer response. Today it needs raw SQL."),
    (4873, "l0", ST, "issue",
     "Manajemen member organization: batch add, pencarian by nama, override SystemAdmin.",
     "Organization member management: batch add, name-based search, SystemAdmin override.",
     "Berlabel <code>needs-triage</code>. Ada kontributor yang nawarin PR untuk bagian pencarian nama.",
     "Labeled <code>needs-triage</code>. A contributor offered a PR for the name-search part."),
    (5092, "l0", ST, "issue",
     "Provisioning tanpa SMTP: akun dibuat admin, one-time login link, hard delete.",
     "Provisioning without SMTP: admin-created accounts, one-time login links, hard delete.",
     "Untuk deployment on-prem tanpa mail server.",
     "Aimed at on-prem deployments with no mail server."),
    (5001, "l0", ST, "issue",
     "Promosi system admin pertama saat sign-up, bukan saat app restart berikutnya.",
     "Promote the first system admin at sign-up instead of the next app restart.",
     "Kecil, tapi bikin deployment baru gak bisa dikelola tanpa restart.",
     "Small, but a fresh deployment can't be administered without a restart."),
    (4200, "l0", ST, "issue",
     "System admin dikecualikan dari batas self-service creation, plus entry config <code>can_access_all_tenants</code>.",
     "Exempt system admins from the self-service creation limit, plus a config entry for <code>can_access_all_tenants</code>.",
     "Bug: kode cuma lihat <code>can_access_all_tenants</code>, bukan <code>is_system_admin</code>.",
     "Bug: the code only reads <code>can_access_all_tenants</code>, never <code>is_system_admin</code>."),
    (1303, "l0", CL, "issue",
     "Multi-tenancy dengan RBAC: role per user di dalam satu tenant.",
     "Multi-tenancy with RBAC: per-user roles inside one tenant.",
     "Ditutup tanpa implementasi. #5295 adalah lanjutannya, dipersempit ke ACL per KB.",
     "Closed without implementation. #5295 is the follow-up, narrowed to per-KB ACL."),
    (2033, "l0", CL, "PR",
     "User biasa gak otomatis punya workspace sendiri, cuma bisa diinvite.",
     "Ordinary users don't get their own workspace automatically, only via invite.",
     "Sudah jadi lewat PR #2037: <code>WEKNORA_AUTH_DEFAULT_TENANT_MODE=tenantless</code> plus flag self-service.",
     "Shipped in PR #2037: <code>WEKNORA_AUTH_DEFAULT_TENANT_MODE=tenantless</code> plus the self-service flag."),
    (2386, "l0", CL, "issue",
     "Saran konsolidasi sistem izin + batasi registrasi.",
     "Suggestions to consolidate the permission system and restrict registration.",
     "Maintainer: sudah ada mode registrasi, system admin, dan OIDC SSO.",
     "Maintainer: registration modes, system admin, and OIDC SSO already exist."),
    (4201, "l0", CL, "PR",
     "Owner gak bisa menurunkan dirinya sendiri di halaman member (transfer ownership).",
     "Owner can't demote themselves on the members page (ownership transfer).",
     "Sudah diperbaiki di PR #4213.",
     "Fixed in PR #4213."),

    (5295, "l1", ST, "issue",
     "ACL per knowledge base di dalam satu workspace: visibility <code>workspace</code> / <code>restricted</code> / <code>private</code>, tabel grant per user/role, list difilter, 404 bukan 403.",
     "Per-KB access control inside a single workspace: <code>workspace</code> / <code>restricted</code> / <code>private</code> visibility, per-user/role grant table, filtered listing, 404 instead of 403.",
     "Belum ada respons maintainer. Ini issue paling matang dari sisi desain, dan yang paling dekat sama kebutuhan kita.",
     "No maintainer response yet. Design-wise this is the most complete one, and the closest to what we need."),
    (4216, "l1", ST, "issue",
     "Role custom + autorisasi per knowledge base di dalam workspace.",
     "Custom roles plus knowledge-base-granular authorization inside the workspace.",
     "Berlabel <code>needs-triage</code>. Menyebut role masih 4 hardcoded, viewer bisa baca semua KB, dan tag bukan batas autorisasi.",
     "Labeled <code>needs-triage</code>. Notes that roles are 4 hardcoded values, a viewer reads every KB, and tags are not an authorization boundary."),
    (3626, "l1", ST, "issue",
     "Usul “Section”: di dalam satu shared space, KB bisa dibatasi ke sekelompok anggota saja.",
     "Proposes “Section”: inside one shared space, a KB can be limited to a chosen set of members.",
     "Berlabel <code>needs-triage</code>. Ada user lain yang mendukung, minta section bisa berisi user (bukan cuma space) dan hierarki bertingkat.",
     "Labeled <code>needs-triage</code>. Another user backed it and asked for user-level sections (not just space-level) plus a hierarchy."),
    (4878, "l1", ST, "issue",
     "Share KB: batch, delegated share permission, dan pengelolaan dari sisi space.",
     "KB sharing: batch, delegated share permission, and space-side management.",
     "Berlabel <code>needs-triage</code>. Sekarang share cuma bisa dari workspace pemilik dan wajib key full-access, jadi admin platform gak bisa kelola.",
     "Labeled <code>needs-triage</code>. Today sharing only works from the owning workspace with a full-access key, so platform admins can't manage it."),
    (4338, "l1", ST, "issue",
     "Editor di dalam workspace gagal ngedit KB yang dibuat orang lain, padahal lewat shared space bisa.",
     "A workspace editor can't edit KBs created by others, while the same role can via a shared space.",
     "Berlabel <code>needs-triage</code>. Sudah di-ping ke maintainer, belum dijawab.",
     "Labeled <code>needs-triage</code>. Pinged the maintainer, no answer yet."),
    (4511, "l1", CL, "issue",
     "Sudut pandang scope gak konsisten: satu key bisa search shared KB (200) tapi gagal list-nya (403).",
     "Inconsistent scope semantics: one key can search a shared KB (200) but not list it (403).",
     "Sudah ditutup. Tetap relevan kalau kita pakai key ter-scope.",
     "Closed. Still relevant if we use scoped keys."),
    (2709, "l1", CL, "issue",
     "Penerima grant admin via organization share gak dapat tombol Settings di UI.",
     "A user granted admin through an organization share gets no Settings button in the UI.",
     "Cuma frontend. Fix-nya tidak pernah di-PR kan ke upstream menurut thread-nya.",
     "Frontend only. Per the thread, the fix never landed upstream."),

    (2024, "l2", ST, "issue",
     "ACL level dokumen plus filter di retrieval (dicek di chunk, bukan disembunyikan di UI).",
     "Document-level ACL plus retrieval filtering (enforced at chunk retrieval, not hidden in the UI).",
     "Maintainer mengarahkan #2809 ke sini sebagai tempat konvergensi. Komentar terakhir (9 Nov) soal menekan visible set ke query sebelum top-k.",
     "Maintainer folded #2809 into this one. Latest comment (9 Nov) argues the visible set must be pushed into the query before top-k."),
    (2090, "l2", ST, "issue",
     "Metadata KB/file, parameter <code>metadata_filter</code> di <code>knowledge_search</code> / <code>grep_chunks</code>, plus search level file.",
     "KB/file metadata, a <code>metadata_filter</code> parameter on <code>knowledge_search</code> / <code>grep_chunks</code>, plus file-level search.",
     "Fondasi buat filter ACL di #2024. Ini juga yang nutup kasus “KB gak kelihatan tapi tetap jadi sumber”.",
     "The foundation for the ACL filtering in #2024. Also what makes the “invisible KB, still the grounding source” case expressible."),
    (2809, "l2", CL, "issue",
     "Izin per dokumen: siapa yang boleh edit, delete, dan siapa yang boleh nge-RAG dokumen itu.",
     "Per-document permissions: who may edit, delete, and who may RAG that document.",
     "Ditutup sebagai duplikat, diarahkan ke #2024.",
     "Closed as duplicate, pointed at #2024."),
    (2266, "l2", CL, "PR",
     "Guest / read-only gak punya batasan operasi dokumen (download, delete, rebuild).",
     "Guests / read-only members had no restriction on document operations (download, delete, rebuild).",
     "Sebagian sudah jalan: download butuh Editor+, operasi lain disembunyikan di UI (PR #2250).",
     "Partly shipped: download needs Editor+, other operations are hidden in the UI (PR #2250)."),
    (4779, "l2", ST, "issue",
     "Semua backend retriever gak menyimpan dimensi tenant; isolasi murni di application layer.",
     "No retriever backend stores a tenant dimension; isolation lives entirely in the application layer.",
     "Pertanyaan, belum dijawab maintainer. Penting kalau mau enforcement fail-closed.",
     "A question, unanswered. Matters if we want fail-closed enforcement."),

    (5420, "l3", ST, "issue",
     "Izin level pemakaian untuk agent, skill, dan MCP di dalam satu tenant, plus siapa yang boleh memasang MCP ke agent.",
     "Usage-level permissions for agents, skills, and MCP inside one tenant, plus who may attach an MCP server to an agent.",
     "Berlabel <code>needs-triage</code>. Tanpa ini, KB private yang dipasang ke agent tetap bocor lewat jawaban dan citation.",
     "Labeled <code>needs-triage</code>. Without it, a private KB bound to an agent still leaks through answers and citations."),
    (5284, "l3", ST, "issue",
     "MCP endpoint personal yang bertindak sebagai ownernya, bukan token statis milik tim.",
     "Personal MCP endpoints that act as their owner, instead of one static team token.",
     "Lubang paling konkret: Viewer bisa nulis KB lewat MCP, aturan “cuma creator/admin yang boleh ubah dokumen” gak berlaku di jalur MCP, audit masuk sebagai user sintetis <code>mcp-&lt;endpoint_id&gt;</code>.",
     "The most concrete hole: a Viewer can write to a KB through MCP, the “only the creator or an admin may change documents” rule isn't applied on MCP writes, and audit lands on a synthetic <code>mcp-&lt;endpoint_id&gt;</code> user."),
    (5157, "l3", ST, "issue",
     "Whitelist tool MCP per sesi IM (tool-level, hanya mengurangi).",
     "Per-IM-session MCP tool whitelist (tool-level, subtractive only).",
     "Sekarang policy tool diset global per <code>(tenant, service, tool)</code>, jadi begitu satu tool diaktifkan, semua entry point bisa memanggilnya.",
     "Today tool policy is global per <code>(tenant, service, tool)</code>, so once a tool is enabled, every entry point can call it."),
    (3598, "l3", ST, "issue",
     "MCP dynamic header dari konteks user yang sedang memakai.",
     "MCP dynamic headers from the current user's context.",
     "Berlabel <code>needs-triage</code>. Pasangan dari #2951: identitas per user, bukan header bersama.",
     "Labeled <code>needs-triage</code>. The counterpart to #2951: per-user identity instead of a shared header."),
    (3479, "l3", ST, "issue",
     "Pola integrasi agent-native: mode read-only untuk agent pemakai, audit trail, deteksi stale.",
     "Agent-native integration patterns: read-only access mode for consuming agents, audit trail, stale detection.",
     "Belum ada respons maintainer.",
     "No maintainer response yet."),
    (5079, "l3", ST, "issue",
     "Minta IM boleh membuka kemampuan agent untuk update wiki, dengan kontrol admin.",
     "Asks to let IM expose the agent's wiki-update capability, with admin control.",
     "Berlabel <code>needs-triage</code>. Arahnya kebalikan dari least privilege, tapi ini issue tempat jalur wiki-write dibahas.",
     "Labeled <code>needs-triage</code>. It points the other way from least privilege, but it's where the wiki-write path is discussed."),
    (2951, "l3", ST, "issue",
     "MCP dengan static header di shared agent seharusnya gak pakai header si pemilik.",
     "An MCP service with static-header auth on a shared agent shouldn't use the sharer's header.",
     "Kalau server MCP-nya bikin keputusan izin dari header, semua pemakai shared agent jadi punya izin si pemilik.",
     "If the MCP server derives authorization from that header, every user of the shared agent inherits the owner's rights."),
    (5193, "l3", CL, "issue",
     "Mode read-only: enforcement-nya benar, pesan asisten ke user yang salah.",
     "Read-only mode: enforcement is correct, the assistant's explanation to the user was wrong.",
     "Sudah ditutup. Bukti bahwa enforcement read-only memang jalan untuk operasi tulis.",
     "Closed. Evidence that read-only enforcement does work for write operations."),

    (3276, "l4", ST, "issue",
     "API key bisa diatur per KB: retrieve / ingest / manage_kbs, plus field <code>permission</code> di response list.",
     "Per-KB API key permissions: retrieve / ingest / manage_kbs, plus a <code>permission</code> field in list responses.",
     "Diusulkan ditegakkan di <code>RequireKBAccess</code>, jadi Admin dari KB-nya sendiri pun gak bisa nge-bypass batas key.",
     "Proposed to be enforced in <code>RequireKBAccess</code>, so even an Admin of the KB can't bypass the key's limit."),
    (5561, "l4", ST, "issue",
     "KB-scoped API key ditolak 403 waktu memilih dokumen eksplisit (<code>knowledge_ids</code>) di agent-chat.",
     "A KB-scoped API key gets 403 when selecting explicit documents (<code>knowledge_ids</code>) in agent-chat.",
     "Berlabel <code>needs-triage</code>. Jalur scope-nya belum konsisten.",
     "Labeled <code>needs-triage</code>. The scoping path isn't consistent yet."),
    (3572, "l4", ST, "issue",
     "Identitas end-user dipindah dari level workspace ke level per API key.",
     "Move end-user identity config from the workspace level down to each API key.",
     "Berlabel <code>needs-triage</code>. Masih tahap diskusi boundary.",
     "Labeled <code>needs-triage</code>. Still a discussion about boundaries."),
    (3351, "l4", CL, "PR",
     "MCP server dengan banyak API key, masing-masing dengan cakupan KB berbeda.",
     "An MCP server with multiple API keys, each scoped to different KBs.",
     "Selesai lewat PR #3371: MCP server bawaan backend Go, tiap workspace bisa bikin endpoint sendiri dengan token dan daftar KB sendiri. MCP server Python-nya deprecated.",
     "Resolved by PR #3371: a Go built-in MCP server where each workspace creates endpoints with its own token and allowed-KB list. The Python MCP server is deprecated."),
    (2413, "l4", CL, "PR",
     "API key per request buat isolasi multi-tenant di MCP server.",
     "Per-request API keys for multi-tenant isolation on the MCP server.",
     "Sama, selesai lewat PR #3371.",
     "Same resolution, via PR #3371."),
    (2603, "l4", CL, "issue",
     "Endpoint buat update daftar KB dari API key ter-scope yang sudah ada.",
     "An endpoint to update the KB allow-list of an existing scoped API key.",
     "Sudah ditutup (owner-only). Kita gak perlu bikin key baru tiap nambah KB.",
     "Closed (owner-only). We don't need a new key every time a KB is added."),
    (3402, "l4", CL, "issue",
     "Audit gak bisa membedakan key mana yang memicu sebuah aksi.",
     "Audit couldn't tell which API key triggered an action.",
     "Sudah ditutup.",
     "Closed."),
    (4228, "l4", CL, "issue",
     "OAuth MCP gak bisa melayani user dari aplikasi yang dibikin di depan WeKnora: gak ada browser, gak ada pre-registered client.",
     "OAuth MCP can't serve users of an application sitting in front of WeKnora: no browser, no pre-registered clients.",
     "Ditutup, PR #4229. Relevan cuma kalau kita naruh WeKnora di belakang aplikasi lain.",
     "Closed, PR #4229. Only relevant if we put WeKnora behind another application."),

    (3747, "l5", ST, "issue",
     "Masking di semua tahap (masuk, retrieval, output), label klasifikasi dokumen, larangan copy/download/export, audit, lifecycle, dan rule library.",
     "Masking at every stage (ingest, retrieval, output), document classification labels, copy/download/export restrictions, audit, lifecycle, and a rule library.",
     "Berlabel <code>needs-triage</code>. Paling luas, paling mahal. Masuk akal dikerjakan setelah ACL-nya ada.",
     "Labeled <code>needs-triage</code>. Broadest and costliest. Makes sense only after the ACL layer exists."),
    (3317, "l5", ST, "issue",
     "Long-term memory belum punya operator surface, padahal dipakai untuk principal yang gak punya akun (user IM, pengunjung embed, user API).",
     "Long-term memory has no operator surface, yet it's built for principals without an account (IM users, embed visitors, API users).",
     "Fase 1 sudah merge (PR #4954), follow-up-nya ditawarkan kontributor.",
     "Phase 1 merged (PR #4954); the follow-up was claimed by a contributor."),
    (4958, "l5", ST, "issue",
     "Extension point policy deny-only untuk akses KB: cuma bisa memveto, gak pernah memberi izin.",
     "A pluggable deny-only policy extension point for KB access: it can only veto, never grant.",
     "Diusulkan dengan patch siap pakai. Gak menutup celah ACL, tapi berguna sebagai jaring pengaman di luarnya.",
     "Proposed with a ready patch. Doesn't close the ACL gap, but works as a safety net outside it."),
    (3426, "l5", CL, "issue",
     "Laporan audit keamanan: 76 temuan plus 11 cacat fungsional.",
     "Security audit write-up: 76 findings plus 11 functional defects.",
     "PR #3425 ditutup tanpa merge; maintainer minta sisa temuan dipecah jadi issue terpisah. Gak ketemu evidence-nya dijalankan.",
     "PR #3425 was closed unmerged; the maintainer asked for the remaining findings to be split into separate issues. No evidence of that happening."),
]

# workarounds: (need_id, need_en, how_id, how_en, hole_id, hole_en, refs)
WORK = [
    ("Memisahkan siapa yang boleh melihat knowledge base mana",
     "Separating who can see which knowledge base",
     "Pecah KB ke workspace terpisah: workspace berperan seperti folder, dan KB yang ada di workspace lain tidak muncul di daftar. Untuk memberi akses tanpa memindahkan orang, share KB ke shared space (organization) dengan permission <code>viewer</code> atau <code>editor</code>, dan beri role <code>Viewer</code> di workspace tujuan untuk yang cuma perlu bertanya.",
     "Split KBs across workspaces: a workspace acts like a folder, and a KB living in another workspace never shows up in your list. To grant access without moving people, share the KB into a shared space (organization) with <code>viewer</code> or <code>editor</code> permission, and hand out the <code>Viewer</code> role in the target workspace to those who only need to ask.",
     "Granularitasnya jadi per workspace, bukan per orang per KB. Satu share berlaku untuk seluruh anggota space, dan orang yang butuh akses harus pindah workspace. Jejak audit ikut terpecah per workspace.",
     "Granularity becomes per workspace, not per person per KB. One share covers every member of the space, and anyone who needs access has to switch workspaces. The audit trail splits per workspace too.",
     [5295, 4216, 3626]),
    ("Boleh dipakai lewat agent, tapi tidak boleh dilihat",
     "Consumable through an agent, but not visible",
     "Share agent-nya saja, KB-nya tetap di workspace pemilik. Penerima hanya bisa bertanya lewat agent itu, dan KB-nya tidak ikut muncul di workspace penerima.",
     "Share the agent only, and keep the KB in the owning workspace. The recipient can only query through that agent, and the KB never appears in their workspace.",
     "Ini batas antarmuka, bukan batas keamanan. Isi KB tetap bisa dipancing lewat jawaban, citation, dan preview file, dan belum ada mekanisme yang membatasi siapa yang boleh menjalankan agent tersebut.",
     "This is an interface boundary, not a security boundary. KB content can still be teased out through answers, citations, and file previews, and nothing yet restricts who may run that agent.",
     [5420, 5284]),
    ("Kredensial mesin dengan scope paling sempit",
     "Machine credentials with the narrowest scope",
     "Tenant API key sekarang capability-scoped dan bisa dibatasi ke daftar KB tertentu, dengan guard di level route (<code>DenyAPIKeyPrincipal</code>, <code>api_key_gate</code>). Lebih rapi: pakai MCP endpoint bawaan per workspace, satu endpoint punya token sendiri, KB scope sendiri, rate limit sendiri, dan tool write mati secara default. Tokennya bisa dirotasi.",
     "Tenant API keys are now capability-scoped and can be restricted to a specific list of KBs, with route-level guards (<code>DenyAPIKeyPrincipal</code>, <code>api_key_gate</code>). Cleaner still: use the built-in per-workspace MCP endpoints, where each endpoint has its own token, its own KB scope, its own rate limit, and write tools off by default. Tokens are rotatable.",
     "Capability key masih global per key, jadi pola “KB A read-only, KB B writable” dengan satu key belum bisa. Di jalur <code>knowledge_ids</code>, key yang di-scope KB masih ditolak 403. Dan token endpoint adalah identitas endpoint, bukan orang: siapa pun yang memegangnya mendapat semua yang endpoint itu izinkan.",
     "Capabilities are still global per key, so “KB A read-only, KB B writable” with one key isn't expressible. On the <code>knowledge_ids</code> path a KB-scoped key is still rejected with 403. And an endpoint token identifies the endpoint, not a person: whoever holds it gets everything the endpoint allows.",
     [3276, 5561, 5284]),
    ("Membatasi apa yang boleh ditulis agent",
     "Limiting what an agent is allowed to write",
     "Agent punya level akses <code>read-only</code>, <code>confirm-before-change</code>, dan <code>automatic-write</code>, plus HITL approval, run yang disuspend, dan scoped grant (PR #4250, #4490). Di MCP endpoint, tool group write mati secara default, dan di IM tool write memang sudah dicabut.",
     "Agents have <code>read-only</code>, <code>confirm-before-change</code>, and <code>automatic-write</code> access levels, plus HITL approval, suspended runs, and scoped grants (PR #4250, #4490). On MCP endpoints the write tool group is off by default, and IM already strips write tools.",
     "Level itu milik satu sesi percakapan, bukan grant organisasi, jadi tidak bisa dipakai sebagai kebijakan tetap. Dan jalur wiki-write lewat tool agent lokal masih tidak memeriksa siapa pemilik KB-nya.",
     "Those levels belong to a chat session, not to an organization-wide grant, so they can't serve as standing policy. And the wiki-write path through local agent tools still doesn't check who owns the KB.",
     [5420, 5079]),
    ("Tahu siapa yang mengubah apa",
     "Knowing who changed what",
     "Wiki page revision dan chunk revision menyimpan <code>last_edit_source</code> (pipeline, agent, user, atau revert) dan <code>last_editor_id</code>. Ada activity audit trail per KB, audit log per tenant, dan audit log platform.",
     "Wiki page revisions and chunk revisions store <code>last_edit_source</code> (pipeline, agent, user, or revert) and <code>last_editor_id</code>. There is a per-KB activity trail, a per-tenant audit log, and a platform audit log.",
     "Aksi yang dijalankan agent di dalam satu workspace tidak bisa diatribusikan ke anggota tertentu. Lewat MCP endpoint, auditnya mencatat user sintetis, jadi penelusurannya berhenti di endpoint.",
     "Actions an agent runs inside one workspace can't be attributed to a specific member. Through an MCP endpoint the audit records a synthetic user, so tracing stops at the endpoint.",
     [5284]),
    ("Onboarding dan registrasi yang terkendali",
     "Controlled onboarding and registration",
     "Mode registrasi bisa dipilih (<code>invite_only</code>, <code>invite_register</code>, <code>DISABLE_REGISTRATION</code>), ada tenantless provisioning dengan self-service workspace yang dikunci flag, OIDC SSO, akun yang dibuat admin, sampai reset password dengan pencabutan sesi.",
     "Registration modes are selectable (<code>invite_only</code>, <code>invite_register</code>, <code>DISABLE_REGISTRATION</code>), there is tenantless provisioning with a gated self-service workspace flag, OIDC SSO, admin-created accounts, and password reset with session revocation.",
     "Batch invite dan panel manajemen user belum ada, jadi provisioning massal tetap manual atau lewat API sendiri. System admin pertama juga masih butuh restart app.",
     "Batch invites and a user-management panel don't exist yet, so bulk provisioning stays manual or scripted against the API. The first system admin still needs an app restart.",
     [1037, 4873, 5001, 5092]),
    ("Menegakkan kebijakan sendiri (compliance, deny rule)",
     "Enforcing your own policy (compliance, deny rules)",
     "Ada extension point policy deny-only dengan patch siap pakai yang bisa didaftarkan di choke point autorisasi yang sudah ada (16 file, +506/−3). Alternatif lebih kasar: jalankan RBAC dalam mode audit-only lewat <code>tenant.enable_rbac=false</code> saat mau migrasi.",
     "There is a deny-only policy extension point with a ready patch that registers into the existing authorization choke points (16 files, +506/−3). A blunter option: run RBAC in audit-only mode with <code>tenant.enable_rbac=false</code> during a migration.",
     "Deny-only: hanya bisa memveto, tidak bisa memberi izin, dan belum upstream, jadi harus dipakai di fork. Mode audit-only bukan penegakan.",
     "Deny-only: it can veto but never grant, and it isn't upstream, so it has to live in a fork. Audit-only mode is not enforcement.",
     [4958, 4216]),
    ("Satu MCP OAuth server dipakai di banyak workspace",
     "One MCP OAuth server shared across workspaces",
     "Bikin satu row <code>mcp_services</code> dengan <code>is_builtin=true</code> langsung di database. Row itu muncul di semua workspace, dan token OAuth disimpan per <code>(tenant, principal, service)</code>, jadi setiap user tetap memakai token miliknya di workspace masing-masing.",
     "Insert one <code>mcp_services</code> row with <code>is_builtin=true</code> directly in the database. It shows up in every workspace, and OAuth tokens are stored per <code>(tenant, principal, service)</code>, so every user keeps their own token in their own workspace.",
     "Belum ada cara resmi provisioning-nya (config, env, atau API system admin), rotasi secret harus lewat SQL, tombol Authorize tidak muncul untuk row builtin, dan agent baru default-nya tidak memasang MCP apa pun.",
     "There is no supported way to provision it (config, env, or SystemAdmin API), secret rotation needs raw SQL, the Authorize button never appears for a builtin row, and new agents attach no MCP by default.",
     [5618]),
]

# gaps: (title_id, title_en, desc_id, desc_en)
GAPS = [
    ("Jalur wiki-write lewat agent lokal gak dicek kepemilikannya",
     "The wiki-write path through local agents isn't ownership-checked",
     "Tool wiki di agent gak memvalidasi siapa pemilik KB sebelum menulis. Gak ada issue yang mencatat ini, dan #5079 justru minta arah sebaliknya, membuka write di IM.",
     "The agent's wiki tools don't validate KB ownership before writing. No issue tracks this, and #5079 asks for the opposite direction by opening write access in IM."),
    ("Enforcement “boleh dipakai lewat agent, gak boleh kelihatan” belum lengkap",
     "End-to-end enforcement of “consumable through an agent, not listable” is incomplete",
     "Sisi list dan 404 sudah ada di proposal #5295, tapi kebocoran lewat jawaban, citation, preview file, dan scope KB milik shared agent belum punya issue khusus.",
     "The listing and 404 side exists in the #5295 proposal, but leakage through answers, citations, file previews, and a shared agent's KB scope has no dedicated issue."),
    ("Attribusi audit untuk aksi yang dijalankan agent",
     "Audit attribution for actions run by an agent",
     "Audit per API key sudah ditutup di #3402 dan #5284 menyebut user sintetis untuk MCP, tapi belum ada yang mengusulkan audit per anggota untuk run agent di dalam satu workspace.",
     "Per-API-key audit was closed in #3402 and #5284 mentions the synthetic MCP user, but nothing proposes per-member audit for agent runs inside a single workspace."),
    ("Belum ada satu choke point autorisasi",
     "There is no single authorization choke point",
     "#4958 mendekati, tapi bentuknya veto per deployment. Semua jalur (list, IM, MCP, agent, wiki) masih memutuskan sendiri-sendiri, jadi tiap fitur baru berpotensi bikin jalur bocor baru.",
     "#4958 comes closest, but it's a per-deployment veto. Every path (list, IM, MCP, agent, wiki) still decides on its own, so each new feature can open a new leak."),
]

ORDER = [
    ("#5295 — fondasi ACL per knowledge base",
     "#5295 — the per-KB ACL foundation",
     "Desainnya paling lengkap dan paling dekat sama kebutuhan kita. Kalau maintainer tetap diam, nilai sendiri apakah mau kirim patch ke issue itu atau maintain fork dengan risiko drift di bagian access, session, IM, dan MCP.",
     "The design is the most complete and closest to what we need. If maintainers stay silent, decide whether to send a patch there or maintain a fork, accepting drift risk in access, session, IM, and MCP."),
    ("#3276 dan #5284 — lubang akses mesin",
     "#3276 and #5284 — machine-access holes",
     "Dua-duanya kecil dan berdiri sendiri. #3276 menyelaraskan scope API key dengan per-KB permission, #5284 menutup tulis lewat MCP dan attribusi audit-nya.",
     "Both are small and self-contained. #3276 aligns API-key scope with per-KB permissions, #5284 closes MCP writes and their audit attribution."),
    ("#5420 lalu #2024 + #2090 — level pemakaian dan dokumen",
     "#5420, then #2024 + #2090 — usage and document level",
     "Urutannya penting: ACL KB harus ada dulu, baru izin pemakaian agent/MCP, baru filter level dokumen yang butuh metadata.",
     "Order matters: KB ACL first, then agent/MCP usage permissions, then document-level filtering, which needs metadata."),
]


# ---------------------------------------------------------------- css
CSS = """:root{
  --bg:#faf9f7; --surface:#ffffff; --fg:#191a1d; --muted:#565a61;
  --border:#ccc6bb; --accent:#1d5c47; --accent-soft:#e8f0ec; --code:#f1efeb;
  --measure:74ch; --radius:10px;
}
@media (prefers-color-scheme:dark){
  :root{
    --bg:#0f1113; --surface:#17191c; --fg:#e9eaec; --muted:#a6abb2;
    --border:#383d43; --accent:#78d6b2; --accent-soft:#16241f; --code:#1e2226;
  }
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{
  margin:0; background:var(--bg); color:var(--fg);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
  font-size:16.5px; line-height:1.65;
}
.wrap{max-width:calc(var(--measure) + 4rem); margin:0 auto; padding:2.5rem 1.25rem 5rem}
header.site{border-bottom:1px solid var(--border); padding-bottom:1.5rem; margin-bottom:2.5rem}
.eyebrow{font-size:.8rem; letter-spacing:.08em; text-transform:uppercase; color:var(--muted); margin:0 0 .6rem}
h1{font-size:1.95rem; line-height:1.25; margin:0 0 .75rem; letter-spacing:-.01em}
h2{font-size:1.3rem; margin:3rem 0 .9rem; padding-top:1.4rem; border-top:1px solid var(--border); letter-spacing:-.005em}
h3{font-size:1.05rem; margin:2rem 0 .5rem}
p{margin:0 0 1rem}
.lede{font-size:1.05rem; color:var(--fg)}
.muted{color:var(--muted)}
nav.switch{display:flex; flex-wrap:wrap; gap:.5rem 1.25rem; align-items:center; margin:1.25rem 0 0; font-size:.92rem}
nav.switch a{color:var(--accent); text-decoration:none; border-bottom:1px solid transparent}
nav.switch a:hover,nav.switch a:focus-visible{border-bottom-color:currentColor}
nav.switch a[aria-current="page"]{color:var(--fg); font-weight:600}
nav.switch .sep{color:var(--border)}
ul,ol{margin:0 0 1.2rem; padding-left:1.35rem}
li{margin:.45rem 0}
li>ul{margin:.4rem 0}
code{background:var(--code); padding:.12em .38em; border-radius:4px; font-size:.88em;
  font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; overflow-wrap:anywhere}
a{color:var(--accent)}
.card{background:var(--surface); border:1px solid var(--border); border-radius:var(--radius);
  padding:1.15rem 1.3rem; margin:1.5rem 0}
.card h3{margin-top:0}
.card p:last-child,.card ul:last-child{margin-bottom:0}
.note{border-left:3px solid var(--accent); background:var(--accent-soft); padding:.9rem 1.1rem;
  border-radius:0 var(--radius) var(--radius) 0; margin:1.5rem 0}
.note p:last-child{margin-bottom:0}
.badge{display:inline-block; font-size:.74rem; font-weight:600; letter-spacing:.03em;
  text-transform:uppercase; padding:.15em .5em; border-radius:999px; border:1px solid var(--border);
  color:var(--muted); white-space:nowrap}
.badge.open{color:var(--accent); border-color:var(--accent)}
.table-wrap{overflow-x:auto; margin:1.5rem 0; border:1px solid var(--border); border-radius:var(--radius)}
table{border-collapse:collapse; width:100%; font-size:.92rem; min-width:640px}
th,td{text-align:left; padding:.6rem .75rem; border-bottom:1px solid var(--border); vertical-align:top}
thead th{background:var(--code); font-size:.8rem; text-transform:uppercase; letter-spacing:.05em; color:var(--muted)}
tbody tr:last-child td{border-bottom:none}
td.num{white-space:nowrap; font-variant-numeric:tabular-nums}
.hint{font-size:.84rem; color:var(--muted); margin:-.9rem 0 1.5rem}
.hint[hidden]{display:none}
footer.site{margin-top:4rem; padding-top:1.5rem; border-top:1px solid var(--border);
  font-size:.88rem; color:var(--muted)}
.layer{margin:2.25rem 0 0}
.layer h3{margin-bottom:.35rem}
.layer .scope{color:var(--muted); font-size:.94rem; margin:0 0 .75rem}
@media (max-width:520px){
  body{font-size:16px}
  h1{font-size:1.6rem}
  .wrap{padding:1.75rem 1rem 3.5rem}
}
@media print{
  body{background:#fff}
  .table-wrap{overflow:visible; border:none}
  .hint{display:none}
}
"""

# ---------------------------------------------------------------- render
def state_badge(kind, state):
    if kind == "PR":
        return '<span class="badge">merged PR</span>'
    if state == "open":
        return '<span class="badge open">open</span>'
    return '<span class="badge">closed</span>'


def layer_issues(lid):
    return [i for i in ISSUES if i[1] == lid]


def render(lang):
    id_lang = lang == "id"
    T = {
        "title": "Peta issue least-privilege WeKnora di dalam satu workspace",
        "title_en": "WeKnora least-privilege issue map for a single workspace",
        "eyebrow": "Riset · Tencent/WeKnora · 17 November 2026",
        "lede": ("Semua issue di repo <code>Tencent/WeKnora</code> yang relevan kalau kita mau menerapkan least privilege "
                 "di dalam satu workspace: apa yang sudah dilaporkan orang lain, statusnya sekarang, dan bagian mana yang "
                 "belum punya issue sama sekali."),
        "lede_en": ("Every issue in the <code>Tencent/WeKnora</code> repository that matters if we want least privilege "
                    "inside a single workspace: what others already reported, where each one stands, and what has no issue at all yet."),
        "nav_doc": "Dokumen",
        "nav_lang": "Bahasa",
        "h_summary": "Ringkasan",
        "h_method": "Cara riset ini dikerjakan",
        "h_layers": "Peta per layer",
        "h_table": "Semua issue dalam satu tabel",
        "h_gaps": "Celah yang belum punya issue",
        "h_order": "Urutan yang aku saranin",
        "h_limit": "Batasan",
        "h_src": "Sumber",
    }

    def L(n):
        return link(n)

    # summary
    n_issues = len(ISSUES)
    n_open = len([i for i in ISSUES if i[3] == "issue" and i[2] == "open"])
    n_closed = len([i for i in ISSUES if i[3] == "issue" and i[2] == "closed"])
    n_pr = len([i for i in ISSUES if i[3] == "PR"])

    if id_lang:
        summary = f"""
<p>Masalah intinya satu: <strong>WeKnora belum punya ACL per resource di dalam satu workspace</strong>. Yang ada cuma
role level workspace dan mekanisme share antar-workspace. Semua issue di bawah ini adalah pecahan dari masalah itu,
tersebar di {n_issues} item: {n_open} masih open, {n_closed} sudah ditutup, {n_pr} selesai lewat PR.</p>
<p>Baca peta ini per layer, karena tiap layer punya pemilik masalahnya sendiri. Layer 0 dan 1 yang paling sering
dibahas orang, tapi lubang paling konkret sekarang justru ada di <a href="{BASE}5284">#5284</a>: siapa pun yang
memegang token MCP satu tim bisa menulis ke knowledge base di luar role-nya, dan audit-nya tidak bisa dilacak ke
orang.</p>
<div class="note">
<p>Kita sendiri sudah membuka <a href="{BASE}5618">#5618</a> tentang MCP default level platform untuk semua workspace.
Issue itu lahir justru karena ACL dalam satu workspace belum ada, jadi keputusannya jatuh ke multi-workspace.</p>
</div>
"""
    else:
        summary = f"""
<p>The core problem is one thing: <strong>WeKnora has no per-resource ACL inside a single workspace</strong>. What exists
is a workspace-level role and a cross-workspace share mechanism. Every issue below is a fragment of that problem,
spread across {n_issues} items: {n_open} still open, {n_closed} closed, {n_pr} resolved through a PR.</p>
<p>Read the map layer by layer, because each layer owns a different slice of the problem. Layers 0 and 1 get most of
the discussion, but the most concrete hole today sits in <a href="{BASE}5284">#5284</a>: anyone holding a shared team
MCP token can write to knowledge bases beyond their role, and the audit trail cannot be traced back to a person.</p>
<div class="note">
<p>We opened <a href="{BASE}5618">#5618</a> ourselves, about platform-level default MCP services for all workspaces.
It exists precisely because there is no ACL inside one workspace, which pushed the design toward multi-workspace.</p>
</div>
"""

    # layers
    layer_html = []
    for lid, tid, ten in LAYERS:
        rows = layer_issues(lid)
        head = tid if id_lang else ten
        out = [f'<section class="layer"><h3>{head}</h3><ul>']
        for n, l, state, kind, cov_id, cov_en, note_id, note_en in rows:
            cov = cov_id if id_lang else cov_en
            note = note_id if id_lang else note_en
            out.append(f'<li>{L(n)} {state_badge(kind, state)} {cov}<br><span class="muted">{note}</span></li>')
        out.append("</ul></section>")
        layer_html.append("\n".join(out))
    layers = "\n".join(layer_html)

    # table
    th = ("Issue", "Layer", "Status", "Cakupan") if id_lang else ("Issue", "Layer", "Status", "Scope")
    hint = ("Tabel bisa digeser ke samping." if id_lang else "This table scrolls sideways.")
    trs = []
    layer_name = {lid: (tid if id_lang else ten).replace(" · ", ": ") for lid, tid, ten in LAYERS}
    order = {lid: i for i, (lid, _, _) in enumerate(LAYERS)}
    rows = sorted([i for i in ISSUES], key=lambda x: (order[x[1]], x[0]))
    for n, l, state, kind, cov_id, cov_en, note_id, note_en in rows:
        cov = (cov_id if id_lang else cov_en).split(".")[0]
        label = "Open" if state == "open" else "Closed"
        if kind == "PR":
            label = "Merged PR"
        trs.append(f'<tr><td class="num">{L(n)}</td><td>{layer_name[l]}</td><td>{label}</td><td>{cov}.</td></tr>')
    table = f"""
<p class="hint" id="tbl-hint">{hint}</p>
<div class="table-wrap" tabindex="0" role="region" aria-labelledby="tbl-hint">
<table>
<thead><tr>{''.join(f'<th>{c}</th>' for c in th)}</tr></thead>
<tbody>{''.join(trs)}</tbody>
</table>
</div>
"""

    # workarounds
    hs1 = "Cara yang jalan sekarang" if id_lang else "What works today"
    hs2 = "Yang masih bocor" if id_lang else "What still leaks"
    hs3 = "Issue terkait" if id_lang else "Related issues"
    work_intro = ("Kalau ACL per resource belum ada, yang bisa dipakai hari ini adalah memindahkan granularitas ke "
                  "workspace dan memanfaatkan scope yang sudah disediakan platform. Semua di bawah ini diambil dari "
                  "CHANGELOG upstream dan teks issue, belum diuji runtime di deployment kita. Sebagian merujuk item di "
                  "luar 42 issue di atas, dan itu dipakai sebagai bukti kapabilitas, bukan bagian dari peta."
                  if id_lang else
                  "While per-resource ACL doesn't exist, what you can use today is moving granularity to the workspace "
                  "level and leaning on the scopes the platform already provides. Everything below comes from the "
                  "upstream CHANGELOG and issue text, and hasn't been exercised at runtime in our deployment. Some rows "
                  "reference items outside the 42 issues above; those are cited as evidence of a capability, not as part "
                  "of the map.")
    work_note = ("Pola multi-workspace memindahkan granularitas dari resource ke workspace: biaya admin naik dan jejak "
                 "audit pecah. Itu juga alasan yang membuat pengusul #5420 menolak split workspace, jadi pakai "
                 "workaround ini untuk menahan sementara, bukan sebagai desain akhir."
                 if id_lang else
                 "The multi-workspace pattern moves granularity from the resource to the workspace: admin cost rises and "
                 "the audit trail fragments. That's the same objection the author of #5420 raised against splitting "
                 "workspaces, so treat these workarounds as a stopgap, not a target design.")
    work_blocks = []
    for need_id, need_en, how_id, how_en, hole_id, hole_en, refs in WORK:
        need = need_id if id_lang else need_en
        how = how_id if id_lang else how_en
        hole = hole_id if id_lang else hole_en
        links = " ".join(link(n) for n in refs)
        work_blocks.append(
            f'<div class="card"><h3>{need}</h3>'
            f'<p><strong>{hs1}:</strong> {how}</p>'
            f'<p><strong>{hs2}:</strong> {hole}</p>'
            f'<p class="muted">{hs3}: {links}</p></div>')
    work = f'<p>{work_intro}</p>' + "".join(work_blocks) + f'<div class="note"><p>{work_note}</p></div>'

    # gaps
    gaps = ['<ul>']
    for tid, ten, did, den in GAPS:
        t = tid if id_lang else ten
        d = did if id_lang else den
        gaps.append(f'<li><strong>{t}.</strong> {d}</li>')
    gaps.append('</ul>')
    gaps = "\n".join(gaps)

    # order
    order_html = ["<ol>"]
    for tid, ten, did, den in ORDER:
        t = tid if id_lang else ten
        d = did if id_lang else den
        order_html.append(f'<li><strong>{t}.</strong> {d}</li>')
    order_html.append("</ol>")
    order_html = "\n".join(order_html)

    # methods / limits
    if id_lang:
        method = """
<p>Sweep dilakukan lewat GitHub API pada 17 November 2026: 34 query kata kunci (Inggris dan Mandarin) ke title dan
body issue di <code>Tencent/WeKnora</code>, 412 issue unik terjaring, sekitar 30 dibaca penuh.</p>
"""
        limits = """
<ul>
<li>Status issue diambil langsung dari GitHub API pada 17 November 2026 (WIB), bukan dari ingatan atau ringkasan.</li>
<li>Ini pembacaan tracker dan kode read-only. Belum ada pengujian runtime, jadi klaim soal perilaku (misal jalur MCP
yang bisa ditulis Viewer) disimpulkan dari kode dan deskripsi issue, bukan dari reproduksi.</li>
<li>Sweep kata kunci cakupannya luas tapi tidak dijamin lengkap. Issue baru yang muncul setelah tanggal itu belum masuk.</li>
<li>Estimasi effort, kalau ada, adalah taksiran dari membaca kode, bukan hasil pengukuran.</li>
<li>Bagian workaround disusun dari CHANGELOG upstream dan teks issue. Kami belum menjalankan WeKnora untuk membuktikan
tiap langkahnya di deployment sendiri, jadi anggap itu arah, bukan instruksi yang sudah teruji.</li>
</ul>
"""
    else:
        method = """
<p>The sweep ran against the GitHub API on 17 November 2026: 34 keyword queries (English and Chinese) over issue
titles and bodies in <code>Tencent/WeKnora</code>, 412 unique issues caught, about 30 read in full.</p>
"""
        limits = """
<ul>
<li>Issue states come straight from the GitHub API on 17 November 2026 (WIB), not from memory or a summary.</li>
<li>This is a read-only pass over the tracker and the code. Nothing was exercised at runtime, so behavioural claims
(for example, that a Viewer can write through MCP) are inferred from code and issue text, not reproduced.</li>
<li>The keyword sweep is broad but not guaranteed exhaustive. Issues filed after that date are not included.</li>
<li>Effort estimates, where present, are guesses from reading code, not measurements.</li>
<li>The workaround section is assembled from the upstream CHANGELOG and issue text. Nothing was run end to end against
our own WeKnora deployment, so treat those as direction rather than tested instructions.</li>
</ul>
"""

    src = """
<ul>
<li><a href="https://github.com/Tencent/WeKnora">github.com/Tencent/WeKnora</a>, semua issue ditautkan langsung ke nomornya.</li>
<li><a href="{base}5618">{base}5618</a> — issue yang kita buka sendiri, dipakai sebagai konteks di halaman ini.</li>
<li>Verifikasi kode yang dikutip issue memakai commit <code>7d064bc3</code> / <code>main</code> per November 2026 sesuai acuan masing-masing issue.</li>
</ul>
""".replace("{base}", BASE) if id_lang else """
<ul>
<li><a href="https://github.com/Tencent/WeKnora">github.com/Tencent/WeKnora</a>; every issue links straight to its number.</li>
<li><a href="{base}5618">{base}5618</a> — the issue we opened, used as context on this page.</li>
<li>Code references quoted in the issues point at commit <code>7d064bc3</code> / <code>main</code> as of November 2026.</li>
</ul>
""".replace("{base}", BASE)

    title = T["title"] if id_lang else T["title_en"]
    lede = T["lede"] if id_lang else T["lede_en"]

    def nav_link(href, label, current):
        cur = ' aria-current="page"' if current else ""
        return f'<a href="{href}"{cur}>{label}</a>'

    nav = (nav_link("index.html", "Bahasa Indonesia", id_lang)
           + '<span class="sep">·</span>'
           + nav_link("index-en.html", "English", not id_lang))

    labels = {
        "summary": "Ringkasan" if id_lang else "Summary",
        "method": "Bagaimana riset ini dikerjakan" if id_lang else "How this research was done",
        "layers": "Peta per layer" if id_lang else "Layer map",
        "table": "Semua issue dalam satu tabel" if id_lang else "Every issue in one table",
        "work": "Workaround yang didukung sekarang" if id_lang else "Workarounds that work today",
        "gaps": "Celah yang belum punya issue" if id_lang else "Gaps with no issue yet",
        "order": "Urutan kontribusi yang disarankan" if id_lang else "Recommended contribution order",
        "limits": "Batasan" if id_lang else "Limitations",
        "src": "Sumber" if id_lang else "Sources",
    }
    foot = ("Halaman ini merangkum status issue publik pada 17 November 2026. Ditulis dari pembacaan tracker dan kode, "
            "tanpa menjalankan WeKnora." if id_lang else
            "This page summarises public issue state as of 17 November 2026. Written from the tracker and the code, "
            "without running WeKnora.")

    return f"""<!DOCTYPE html>
<html lang="{'id' if id_lang else 'en'}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{html.escape(re.sub("<[^>]+>", "", lede)[:170], quote=True)}">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<div class="wrap">
<header class="site">
<p class="eyebrow">{T['eyebrow']}</p>
<h1>{title}</h1>
<p class="lede">{lede}</p>
<nav class="switch" aria-label="{'Navigasi dokumen dan bahasa' if id_lang else 'Document and language navigation'}">
{nav}
</nav>
</header>
<main>
<h2>{labels['summary']}</h2>
{summary}
<h2>{labels['method']}</h2>
{method}
<h2>{labels['layers']}</h2>
{layers}
<h2>{labels['table']}</h2>
{table}
<h2>{labels['work']}</h2>
{work}
<h2>{labels['gaps']}</h2>
{gaps}
<h2>{labels['order']}</h2>
{order_html}
<h2>{labels['limits']}</h2>
{limits}
<h2>{labels['src']}</h2>
{src}
</main>
<footer class="site">
<p>{foot}</p>
</footer>
</div>
<script>
(function(){{
  var h=document.getElementById('tbl-hint');
  if(!h) return;
  var w=h.nextElementSibling;
  var check=function(){{ h.hidden = w.scrollWidth <= w.clientWidth; }};
  check(); addEventListener('resize',check);
}})();
</script>
</body>
</html>
"""


with open(os.path.join(OUT, "assets", "style.css"), "w") as f:
    f.write(CSS)
for lang, name in (("id", "index.html"), ("en", "index-en.html")):
    with open(os.path.join(OUT, name), "w") as f:
        f.write(render(lang))

print("written to", OUT)
print("issues referenced:", len(ISSUES),
      "| open:", len([i for i in ISSUES if i[3] == 'issue' and i[2] == 'open']),
      "| closed:", len([i for i in ISSUES if i[3] == 'issue' and i[2] == 'closed']),
      "| merged PR:", len([i for i in ISSUES if i[3] == 'PR']))
print("layers:", {l[0]: len(layer_issues(l[0])) for l in LAYERS})
print("gaps:", len(GAPS), "| order steps:", len(ORDER))
