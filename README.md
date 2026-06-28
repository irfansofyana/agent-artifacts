# agent-artifacts

Static publishing target for final AI-generated artifacts.

This repository is intentionally boring: GitHub Pages serves files directly from
the `main` branch root. Agents should not use this repository as a brainstorming
workspace. They should only publish final artifacts here.

Live site:

https://irfansp.dev/agent-artifacts/

## Structure

```txt
.
├── index.html
├── artifacts.json
├── assets/
│   └── site.css
└── artifacts/
    └── hello-world/
        └── index.html
```

## Publishing Contract

When an agent publishes a final HTML artifact:

1. Pick a stable slug, for example `litellm-cache-report`.
2. Create `artifacts/<slug>/index.html`.
3. Add or update an entry in `artifacts.json`.
4. Commit to `main`.
5. Return the public URL:

```txt
https://irfansp.dev/agent-artifacts/artifacts/<slug>/
```

## Artifact Manifest

`artifacts.json` is the lightweight registry used by the homepage.

Each entry should include:

```json
{
  "title": "Readable artifact title",
  "slug": "artifact-slug",
  "description": "One short sentence describing the artifact.",
  "createdAt": "2026-06-28",
  "type": "html",
  "url": "artifacts/artifact-slug/"
}
```
