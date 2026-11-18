# Scandinavian restyle of agent-artifacts

Status: in progress (branch `design/scandinavian`, not pushed).

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

## Follow-ups

- The five here.now artifacts (cubesandbox-eks-jakarta, codex-security-gitlab,
  weknora-least-privilege, uaef-getting-started, hermes-openclaw-aws) still carry
  their own designs; they live in scratch build directories, not here.
- Preview before pushing: publish the built site to here.now and let Irfan look at it
  on his phone, then push to Pages.
