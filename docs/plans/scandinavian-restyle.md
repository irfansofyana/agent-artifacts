# Scandinavian restyle of agent-artifacts

Status: **done for the repo, awaiting Irfan's go to publish.** Branch
`design/scandinavian` (commit `a03d7d8`, pushed). Preview:
<https://irfan-ai-agents.irfansp.here.now/> — the Pages site is untouched until he approves.

## Why

Irfan asked for every published artifact — the here.now site and the agent-artifacts
site — to use the Scandinavian design system, and for new pages to inherit it.
The site previously shipped a dark terminal shell (window chrome, phosphor green,
Fira Code) with 38 artifact modules carrying their own colour palettes.

## Blast radius (measured, not estimated)

- 45 generated pages: 44 artifact pages + the registry homepage.
- 38 `src/artifacts/*/module.css`, of which 28 set `text-transform: uppercase`,
  ~20 use gradients or shadows, ~120 hard-coded colour values in total.
- `tests/browser/*` asserts the shared shell (`data-theme-toggle`, `#site-main`),
  so the shell could change; `mobile-content-contrast.mjs` asserted raw computed
  colours, which no longer works with alpha ink (fixed, see below).

## Decisions

1. **Token names unchanged.** The modules alias their own names onto shell tokens
   (`--bg: var(--bg-terminal)`, `--acid: var(--phosphor)`, `--muted: var(--text-secondary)` …),
   so redefining the shell tokens restyles all 44 pages at once. New page = new tokens only.
2. **Both themes kept, names kept.** `:root` stays the dark canvas and
   `[data-theme="paper"]` the light one, because `assets/site.js` and eight browser
   tests swap and persist those names. Both are now on the same monochrome ladder
   (`#0a0a0a` / white canvas, alpha ink, no hue). Flipping the *default* to light is a
   one-line change in `site.js` plus the tests — deliberately not taken here; ask Irfan.
3. **Semantic states are re-encoded, not coloured.** Error/warning callouts used
   `--accent-error` and friends; those now collapse onto the ink ladder, so the state
   has to survive on a label or border weight. Anywhere that failed, the sweep reports it.
4. **Alpha ink is the system.** Intermediate tones are `rgb(0 0 0 / n%)` on white and
   `rgb(255 255 255 / n%)` on near-black, per the design skill. This broke the repo's
   contrast test, which compared raw computed colours and could not composite alpha.
5. **Content preserved.** No prose, anchor, URL, interactive control or relative asset
   was dropped; only presentation changed.

## Gates

```bash
npm run build && npm test && npm run validate      # 61 unit tests, validator
CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  BASE_URL="http://127.0.0.1:4173/" npm run test:browser
```

Plus a page-level colour sweep: every element of every page in both themes, listing any
colour whose channel spread marks it as a hue, any `text-transform: uppercase`, and any
document-wide horizontal overflow at 390px.

## Verification evidence

- 61/61 unit tests, validator clean, 45 pages built.
- Browser suite: home search/sort/theme, article smoke, interactive, diagrams,
  review regressions pass; mobile content contrast + table layout passes after the
  alpha-compositing fix.
- Home at 1440px: 45 rows, no overflow, min measured contrast 4.66:1 (muted meta at
  `rgb(255 255 255 / 46%)`), console clean.

## Double publish

Every published artifact now keeps its generator in this repo: Pages artifacts in
`src/artifacts/<slug>/`, here.now artifacts under `sources/<slug>/` (with the text inputs
they read), listed in `sources/README.md`. The convention is in `SKILL.md`, and the
here.now publishing skill's checklist ends with committing the generator.

## Follow-ups

- The five here.now pages still render their own designs — the repo now holds their
  generators, so restyling them is a generator edit plus a republish to the same slug.
- Open question for Irfan: keep dark as the default theme, or flip to light?
- Diagram documents under `artifacts/<slug>/diagrams/` are outside the colour gate
  (they are separate documents); check them by eye if a page's diagram looks off.
