---
name: agent-artifacts-authoring
description: Use when creating or updating an artifact on Irfan's agent-artifacts website with its shared static design system.
---

# Agent Artifacts — authoring contract

This repository is the source of truth. Read `AGENTS.md` and `README.md` before editing. Work locally first; **publication requires Irfan's approval**. Do not directly replace a generated `artifacts/<slug>/index.html` with standalone HTML.

## Shared layout

`templates/home.html` and `templates/artifact.html` own the terminal-window chrome. `assets/design-system.css` contains design tokens; `assets/site.css` and `assets/site.js` own layout and theme behavior. Source lives in `src/artifacts/<slug>/content.html`; optional `module.css` and `module.js` live beside it. `npm run build` generates the homepage and every artifact page. Preserve stable URLs and registry entries in `artifacts.json`.

Write a **body fragment**, not a full HTML document. Use headings, anchors, accessible labels, semantic tables and links; never duplicate the shell or theme button. Use `templates/example-content.html` as a starting point. The dark/paper **theme** button is shared and persists. Module CSS must be scoped under `.legacy-content` or `[data-artifact-content]`, use design-system tokens, and not redefine global `html`, `body`, or `:root`.

The renderer supplies a shared TOC for articles with enough anchored sections. Do not leave a second legacy side navigation or a two-column grid reserving room for one the shell hides. Articles without a TOC must use the full article width. Verify actual article and inner-content widths on desktop as well as mobile; a clean document `scrollWidth` does not detect a 190px-wide article trapped in a 1000px grid.

## Mobile and specialized content

**Mobile** first: at 320px and 390px, a single vertically scrolling page without document-wide horizontal overflow. Put wide tables/code/diagrams in swipeable containers with keyboard-accessible overflow. Give dense tables a sensible minimum table and minimum column width so labels do not collapse into vertical letters; keep horizontal scroll inside the wrapper rather than the document, give the scroll container keyboard focus and an accessible label, and show a brief visible swipe hint when columns extend offscreen. Preserve interactive controls and visible focus. For **Archify** and other large diagrams, keep the real HTML module under `artifacts/<slug>/diagrams/`, link it relatively, embed it where appropriate, allow internal touch-pan, and provide a full-size link. Mermaid should have readable text/source when its external script cannot load. Never flatten a functional diagram into an image only.

Check foreground/background contrast for prose, inline code, code block text and diagrams in **both dark and paper themes**; normal text needs at least 4.5:1. An accent token such as `--phosphor` is not a safe background behind muted text: use a theme-aware opaque surface such as `--bg-chrome`, keep accent for highlights, and test the computed colors in a browser at mobile widths. When updating a module, test representative populated tables and code, not only the shared shell.

## Public-content privacy gate (mandatory)

**Do not publish** company-confidential data, a private person's name or other personal info, a private file, or any credential. This applies even if the page is useful or publication was generally approved. Before committing or pushing, inspect **every publication surface**: title, slug, description and other registry metadata; article prose, code, links, diagrams, labels and examples; asset filenames, screenshots/images (including visible UI and EXIF), PDFs and their embedded metadata; generated HTML and build output. Look for internal company names/projects, customer or employee details, private URLs/repo paths, email/phone/address/location, financial or health information, API keys and tokens. Publicly documented third-party names and the site's deliberate publisher credit are not private-person disclosures; verify the source and context.

If anything sensitive appears, **stop**: omit it or anonymize it in both source and generated output, then re-run build, tests and a manual review of the rendered page and assets. If safe anonymization would destroy the artifact, do not publish it. Do not paste sensitive values into review comments, test logs, commit messages or this skill. Automated secret scans are only a supplement: they cannot prove a page is safe. A general approval to publish never waives this gate.

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

Pass the mandatory privacy gate above, then check broken links and accessibility. Request **explicit publication approval** for a new artifact; when approved, commit source, registry, generated pages and any assets together, push normally (no force), read back exact committed paths, then verify the live GitHub Pages URL. A successful push alone is not a live deployment.
