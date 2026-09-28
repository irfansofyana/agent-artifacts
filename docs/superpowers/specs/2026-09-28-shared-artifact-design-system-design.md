# Shared artifact design system — design

## Intent and approval context

Irfan wants the public agent-artifacts site to feel like his supplied **irfansp.dev Design System**, rather than a collection of unrelated pages. The homepage and every existing and future artifact should share a recognizable page shell and content layout. Specialized diagrams and interactive modules must keep working. Most reading happens on mobile. First deliver a **local-only preview for Irfan's approval**, without pushing to GitHub or publishing the live site.

Agreed visual direction: the design-system ZIP's **full phosphor-green terminal window** (option A), not the open-page variant. A labeled dark/paper theme button must be available on the home and each artifact page. The paper palette comes from the ZIP, not an invented white theme. The shared static template and agent instructions belong in this repository; the installed artifact-publishing skill should reference the same contract.

## Baseline and scope

The repository currently serves plain files from the `main` branch root on GitHub Pages. `artifacts.json` registers 33 HTML pages under stable `artifacts/<slug>/` URLs. Only three currently reference `assets/site.css`; nearly all others have independent inline styling, and several include their own scripts or external dependencies. Existing standalone diagram files include Archify-style HTML/SVG and Mermaid-based HTML, including nested assets linked from artifact pages. The current home uses a distinct serif/sans editorial visual system.

**In scope:** home, all 33 registered artifact pages including smoke-test/example pages, shared responsive styling, dark/paper switching, diagram and widget presentation, a local static build/validation workflow, documentation and a repo-owned agent skill, and updating the installed publishing skill to follow the new contract. Preserve existing research claims, citations, linked files, major information hierarchy, interactive behavior, slugs, and public URLs. A manifest-to-files inventory must account for every registered page and nested asset.

**Out of scope for this local milestone:** pushing or publishing, domain/GitHub Pages changes, fact-checking or rewriting all research claims, replacing Archify/Mermaid engines, a client-side SPA, a new backend, or forcing each specialized widget into identical component markup. No content should silently disappear during migration.

## Architecture and source of truth

Use a **small dependency-light, deterministic Node static generator** in the repository, not a runtime shell injector or copy-pasted page chrome. Keep the repository's existing Pages-serving root: `index.html`, `artifacts.json`, `assets/`, and `artifacts/<slug>/index.html` are generated/served outputs; local source inputs and templates live in clearly named source/template directories. Running the build locally reproduces those outputs; validation detects output drift. No framework or server-side rendering is required in production.

The repo owns:

- Design-system assets derived from the supplied ZIP: the provided color/spacing/type/effect tokens and a focused shared stylesheet for the site. Verify redistribution terms for the bundled Fira Code and JetBrains Mono fonts before committing copies; obtain appropriately licensed upstream font files if needed, otherwise use a documented fallback. Preserve provenance and identify deliberate adaptations. Avoid importing the entire React UI kit or its runtime just to render static articles.
- A reusable home template and artifact template with the same terminal window/chrome, breadcrumb/navigation, metadata, content area, optional section TOC, labeled theme button, and footer/status bar. Semantic HTML remains usable with JavaScript disabled; JavaScript adds enhancement, not basic reading/navigation.
- Per-artifact source content plus optional, explicitly registered page-level CSS/JS and nested media/diagrams. Content source is not a second full HTML document with competing global `html/body/:root` rules. Specialized modules are scoped or isolated, rather than letting old CSS overwrite the shared shell.
- `artifacts.json` as the registry for stable slug, title, description, date, URL, and any narrowly justified extra metadata required to render pages. The generator validates manifest entries against source and emitted files.
- A minimal `SKILL.md` and project instructions/README with a concrete artifact authoring recipe, template contract, responsive/diagram rules, local commands, validation, and publishing gates. The existing installed publishing skill points back to the repo contract; it must not continue recommending free-form standalone HTML as the default.

The generation interface should be documented by a complete example. Inputs such as title/description/date/sections, a content fragment, and optional module assets should be explicit; no untracked implicit filename conventions for required metadata. Escaping and URL/path validation protect generated markup. An ordinary artifact can be added without hand-editing the site shell.

## Visual and interaction rules

The supplied ZIP is the canonical visual reference: near-black green-tinted page and terminal surfaces, phosphor `#36ff7a`, amber for actions, gold for labels, cyan for links, green-tinted body text, compact radii, monospace typography, output-block cards, and restrained CRT treatment. Use the ZIP's `data-theme="paper"` token remapping for light mode (`#f8f7f1` paper window, deep green emitter/ink), without scanline/glow/tilt effects there. Preserve accessible contrast and reduced-motion behavior; do not make typing commands necessary to navigate.

Desktop: one centered terminal window with chrome and an inner scrolling reading pane; the shell can have a max width near the provided 1100px reference and a viewport-aware height. Long artifact pages get an optional sticky section TOC **inside the reading pane**. Home includes featured/latest output, searchable and sortable registry, and clear links. Use real buttons/links and text labels; the terminal is a visual language, not a fake CLI gate.

Mobile: the window occupies available width with compact chrome and **normal document vertical scrolling**, not a 90vh nested-scroll trap. TOC collapses to a labeled, keyboard-accessible section selector/disclosure. Type and tap targets remain readable; no page-level horizontal overflow at narrow phone widths. Wide code, tables, charts, and diagrams get their own horizontally swipeable/focusable viewport with a visible cue; provide an explicit full-size/original link for complex diagrams. Preserve keyboard access and an accessible name for scroll regions.

The **Theme: Dark / Theme: Paper** control is a visible, labeled button on the home and every artifact page. Dark is the initial default; user choice persists across site pages (e.g. localStorage, with safe failure fallback), and first paint should avoid a theme flash where feasible. Theme-switching updates the shared shell and content primitives consistently. Embedded/standalone diagrams either receive a compatible theme or sit on a deliberate neutral, high-contrast canvas; do not blanket-invert generated SVG/diagram HTML.

## Existing-artifact migration and exception policy

Migrate all 33 pages against an inventory. Extract article structure into the shared template, retire page-global style rules, and map recurring patterns (headings, callouts, code, tables, sources, references) to semantic shared styles. Preserve ids and deep links, outbound sources, code examples, content order, downloads, and interactive behavior. Interactive courses, search/filter pages, calculators, and other bespoke views may keep scoped scripts/CSS or become self-contained modules **inside** the common article shell. Document exceptions and test them; do not hide an entire legacy article in a nested iframe merely to claim uniformity.

Preserve nested diagram and supporting files at stable paths. Existing Archify HTML/SVG pages and Mermaid diagrams remain working artifacts/assets and must be rendered or linked from the migrated article; they are not flattened into screenshots. For iframe-based diagrams, test whether touch gestures are captured inside the iframe; a CSS overflow wrapper alone is not proof of swipeability. Provide a tested horizontal-pan interaction at mobile widths and an obvious open-full-size action. Standalone diagram views must themselves be navigable on mobile, including zoom/pan where already supplied. Full-size URLs and relative asset links survive the build.

Do not silently rewrite old content for branding. Move layout, navigation, and visual hierarchy to the shared system while leaving research prose and citations intact except for necessary accessibility/structure repairs. Keep a migration ledger with all 33 slugs and any exceptions.

## Verification and local preview

Before seeking approval of the completed local redesign:

1. Build the site locally, serve it on loopback, and verify the home plus **every** manifest URL and linked local asset resolves, with no missing/extra artifact page relative to the 33-page baseline. No push/deploy.
2. Deterministic generator tests cover manifest validation, slug/path escaping, generated home/article shell, theme hooks, and preservation of nested relative links. A clean rebuild should produce the same tracked output.
3. Browser checks at phone and desktop viewports cover no document-width overflow, working search/sort, theme button and cross-page persistence, TOC/anchors, keyboard/focus/reduced motion, and console/network errors. Verify both themes on representative pages and sample screenshots.
4. Exercise real Archify HTML iframe pages and Mermaid embeds at narrow widths: touch/drag to inspect offscreen content, full-size navigation, and diagram legibility. Exercise existing interactive artifacts (not only static examples) to detect broken event handlers or CSS collisions.
5. Diff extracted content against originals for section titles, links, citations, code blocks, interactive controls, and asset references, with explicit review of exceptions. Report any intentional content change.
6. Verify the repo-owned skill/instructions from a fresh artifact example: follow the documented commands to add one page locally, build, validate, and preview without hand-copying chrome. Verify installed publishing guidance matches the new repo contract.

The acceptance handoff is a durable local branch and local preview/screenshots with a concise migration/verification report. Irfan reviews it before any publication. No public URL should be reported as newly published until a later explicit approval, push, and live-site read-back.

## Risks and decisions

- **Global CSS collisions:** migrate page styles to scoped modules or wrappers, validate each page rather than applying an overriding stylesheet blindly.
- **Iframe touch capture / giant Archify HTML:** verify actual gestures and same-origin asset paths; keep original diagram route accessible.
- **Double-scroll on mobile:** disable fixed-height pane and sticky desktop TOC at the mobile breakpoint.
- **Theme mismatch inside embedded modules:** support explicit theme handoff where safe, or use a neutral diagram surface with readable labels; no color inversion hack.
- **Existing third-party CDN dependencies:** preserve functionality, identify external dependencies in the migration ledger, and verify failure behavior instead of claiming everything is offline-capable.
- **Build/publish contract:** local build cannot mutate a public repo or live site by itself; publication remains a separate reviewed step.
