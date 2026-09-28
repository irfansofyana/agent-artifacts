---
name: agent-artifacts-authoring
description: Use when creating or updating an artifact on Irfan's agent-artifacts website with its shared static design system.
---

# Agent Artifacts — authoring contract

This repository is the source of truth. Read `AGENTS.md` and `README.md` before editing. Work locally first; **publication requires Irfan's approval**. Do not directly replace a generated `artifacts/<slug>/index.html` with standalone HTML.

## Shared layout

`templates/home.html` and `templates/artifact.html` own the terminal-window chrome. `assets/design-system.css` contains design tokens; `assets/site.css` and `assets/site.js` own layout and theme behavior. Source lives in `src/artifacts/<slug>/content.html`; optional `module.css` and `module.js` live beside it. `npm run build` generates the homepage and every artifact page. Preserve stable URLs and registry entries in `artifacts.json`.

Write a **body fragment**, not a full HTML document. Use headings, anchors, accessible labels, semantic tables and links; never duplicate the shell or theme button. Use `templates/example-content.html` as a starting point. The dark/paper **theme** button is shared and persists. Module CSS must be scoped under `.legacy-content` or `[data-artifact-content]`, use design-system tokens, and not redefine global `html`, `body`, or `:root`.

## Mobile and specialized content

**Mobile** first: at 320px and 390px, a single vertically scrolling page without document-wide horizontal overflow. Put wide tables/code/diagrams in swipeable containers with keyboard-accessible overflow. Preserve interactive controls and visible focus. For **Archify** and other large diagrams, keep the real HTML module under `artifacts/<slug>/diagrams/`, link it relatively, embed it where appropriate, allow internal touch-pan, and provide a full-size link. Mermaid should have readable text/source when its external script cannot load. Never flatten a functional diagram into an image only.

## Local workflow

```bash
npm ci
node scripts/add-artifact.mjs --slug example-guide --title "Example Guide" --description "A concise guide." --file templates/example-content.html
npm run build
npm test
npm run validate
npm run preview
# in another shell: npm run test:browser
```

The helper validates input and writes source + registry + generated HTML locally; for an existing slug it updates one entry. Add relative assets under `artifacts/<slug>/` and test them. A full standalone HTML document is rejected: extract its body into a fragment first. The helper does not push or publish.

Review content for credentials, private/company-sensitive material, broken links and accessibility. Request **explicit publication approval** for a new artifact; when approved, commit source, registry, generated pages and any assets together, push normally (no force), read back exact committed paths, then verify the live GitHub Pages URL. A successful push alone is not a live deployment.
