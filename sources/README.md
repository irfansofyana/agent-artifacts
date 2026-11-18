# Artifact sources

The code that generates every published artifact lives here, next to the artifact it
produces. Publishing is a **double publish**: the page goes live on here.now (and, for
pages with a Pages copy, at `irfansp.dev/agent-artifacts/`), and the generator is
committed in the same pass so the page can always be rebuilt, restyled or fixed.

## Two kinds of artifact

| Kind | Source lives in | Generated pages |
| --- | --- | --- |
| Pages artifact | `src/artifacts/<slug>/content.html` (+ optional `module.css`) | `artifacts/<slug>/index.html`, built by `npm run build` |
| here.now artifact | `sources/<slug>/*.py` (+ its article/inputs) | a directory published with the here.now `publish.sh` |

Both end up in one registry — the index at <https://artifacts.irfansp.dev/> lists every
artifact from both hosts.

## here.now artifacts

| Artifact | Live | Domain path | Generator |
| --- | --- | --- | --- |
| CubeSandbox on EKS Jakarta | <https://artifacts.irfansp.dev/cubesandbox-eks-jakarta/> | `cubesandbox-eks-jakarta` | `build_site_full.py` (bilingual) |
| Codex Security on GitLab | <https://artifacts.irfansp.dev/codex-security-gitlab/> | `codex-security-gitlab` | `build.py` |
| WeKnora least-privilege issue map | <https://artifacts.irfansp.dev/weknora-least-privilege/> | `weknora-least-privilege` | `build_weknora_lp_page.py` |
| Getting started with UAEF | <https://artifacts.irfansp.dev/uaef-getting-started/> | `uaef-getting-started` | `build.py` |
| Running Hermes and OpenClaw on AWS | <https://artifacts.irfansp.dev/hermes-openclaw-aws/> | `hermes-openclaw-aws` | `gen.py` |
| Open-source projects that use AI to fix GitLab vulnerabilities | <https://artifacts.irfansp.dev/open-source-gitlab-ai-autofix/> | `open-source-gitlab-ai-autofix` | `build.py` |

Rebuild and republish (the mount keeps the URL):

```bash
cd sources/<slug>
python3 build_site_full.py          # writes ./site (or the path printed by the script)
bash ~/.hermes/skills/here-now/scripts/publish.sh <output-dir> \
  --slug <here.now-slug> --client hermes/kai
```

`<here.now-slug>` is the generated slug from the first publish (`crystal-nebula-5886`
style) — it is recorded in the root index's `config.json → domain_paths` in the
publishing skill.

## Rules

- One directory per artifact, named exactly like the domain path.
- Commit the generator **and** the text inputs it reads (article markdown, its CSS). Skip
  large data dumps, screenshots, PDFs and fonts — the generator says where they come from.
- No absolute local paths: read the working directory from an environment variable with a
  repo-relative default (`os.environ.get("X_WORK", os.path.dirname(os.path.abspath(__file__)))`).
- Screenshot-free, secret-free, machine-independent: the mandatory privacy gate in
  `SKILL.md` applies to this directory as much as to a published page.
