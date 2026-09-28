# Shared Agent Artifacts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the local agent-artifacts site as one mobile-responsive, dark/paper terminal publication with working existing artifacts and a repo-owned authoring contract, without publishing it.

**Architecture:** Node's built-in modules generate static root/home and `artifacts/<slug>/index.html` from reusable HTML templates, `artifacts.json`, and per-page source fragments. Shared CSS/JS owns the shell and themes; carefully scoped artifact modules retain special interactions and diagram assets. GitHub Pages would continue serving plain committed files only after a separate release approval.

**Tech Stack:** Static HTML/CSS, Node.js ESM and `node:test`, Playwright browser smoke checks (development-only), existing JSON registry; no client-side framework or runtime backend.

**Spec:** `docs/superpowers/specs/2026-09-28-shared-artifact-design-system-design.md`

## Global Constraints

- Work in `/home/irfansofyana/repos/agent-artifacts` on a local branch; **do not push, deploy, or change `main`** in this milestone.
- Preserve the current 33 manifest slugs and `artifacts/<slug>/` URLs; preserve titles, descriptions, dates, content, citations, anchors, code examples, nested assets, and functional controls unless a reviewed exception is recorded.
- The ZIP `/home/irfansofyana/.hermes/attachments/Irfan Devs Design System.zip` supplies the phosphor/terminal tokens and paper palette; verify font redistribution terms before vendoring font files.
- Desktop uses option A's full terminal window and scrollable reading pane; mobile uses natural document scrolling with no horizontal page overflow; diagram/table/code regions pan horizontally.
- A visible `Theme: Dark` / `Theme: Paper` button appears on home and artifact pages and persists the selected theme across those pages. Dark is the initial default. Honor reduced motion.
- Keep `artifacts.json` as the registry and retain the Explore interaction: latest item derived by date, newest/oldest/title sorting, substring search, results/empty/error states, slash and Escape shortcuts.
- Preserve standalone Archify HTML/SVG and Mermaid assets; demonstrate real touch/drag or a usable full-size pan path, not merely a CSS overflow claim.
- Local preview and tests are acceptance evidence; publication requires a later explicit go-ahead and separate repository/live verification.

## File Map and Interfaces

- `package.json`: explicit `build`, `validate`, `test`, `preview`, `test:browser` commands; `playwright` development-only if needed.
- `scripts/site-model.mjs`: `readSite(root)` validates registry and source/asset paths; returns `{artifacts}` with stable slug/title/description/date/url/content paths.
- `scripts/render-site.mjs`: `renderHome(model)`, `renderArtifact(entry, fragment)` and `buildSite(root)`; side-effecting output only in `buildSite`.
- `scripts/validate-site.mjs`: validate manifest/source/output counts, internal links, regenerated output drift, required shell hooks, mobile diagram affordances.
- `templates/home.html`, `templates/artifact.html`, `templates/example-content.html`: semantic build-time templates; content slot and optional TOC/module slots, no global legacy CSS in content fragments.
- `src/artifacts/<slug>/content.html`, optional `module.css`, `module.js`: canonical per-page source; nested `artifacts/<slug>/assets/` and `diagrams/` remain at their current URLs.
- `assets/design-system.css`, `assets/site.css`, `assets/site.js`, optional verified-license `assets/fonts/*`: tokens, shared layout, progressive enhancement; `site.css` may import tokens but not old conflicting global rules.
- `tests/*.test.mjs` and `tests/browser/*.mjs`: Node logic/contract tests and real browser smoke tests.
- `SKILL.md`, `AGENTS.md`, `README.md`: repo-owned agent contract and human workflow. Installed skill `github-pages-artifact-publisher` will be updated only **after** the repo contract works locally.
- `docs/migration-ledger.md`: 33-row source-to-output review ledger, exceptions, interactive/diagram checks.

**Generator contract:** `readSite(root,{allowLegacy:false})` returns validated entries; `renderArtifact(entry, fragment)` receives a trusted, reviewed HTML fragment (not arbitrary runtime user input), escapes metadata, and inserts common chrome; `buildSite(root,{allowLegacy:false})` writes generated pages. During Tasks 2–7, explicit `allowLegacy:true` builds render migrated sources and leave still-unmigrated output files untouched, so each batch remains previewable; final build/validator prohibit legacy fallback. All build inputs belong in this repo and build output must be reproducible. `--check` validation fails rather than silently rewriting output. Basic reading and links work without client JavaScript.

## Review Focus — pin these in owning tasks

1. A slug with `../`, an external or escaping manifest URL, or duplicate slug must fail validation rather than write outside `artifacts/` (Task 1).
2. A manifest title containing `<` and `&` must render as escaped text, never executable HTML (Task 2).
3. Theme storage unavailable/throwing must still leave an accessible working in-page theme switch and readable default (Task 2).
4. A phone-size Archify iframe captures swipe inside its frame: demonstrate a real pan path and full-size link rather than relying on its parent `overflow-x` (Task 7).
5. A content fragment with a preserved relative diagram link or hash anchor must still resolve after generation; CDN failure must not make the article unreadable (Tasks 6 and 7).

---

### Task 1: Registry/source model and failing tests

**Files:** Create `package.json`, `scripts/site-model.mjs`, `tests/site-model.test.mjs`; modify `scripts/add-artifact.mjs` later in Task 9, not here.

**Interfaces:** Produces `readSite(root)` and `validateEntry(entry, root)` for the renderer; consumes current `artifacts.json`. `readSite` must tolerate the migration-in-progress state via an explicit `allowLegacy` option, but strict mode requires one source fragment per registered slug.

- [ ] **Step 1: Write failing tests** with `node:test`, `assert/strict`, and temporary fixtures: valid `hello-world`, rejected duplicate slug, rejected `../escape`, rejected `https://evil.example/`, and missing content source. Asset/link resolution belongs to Task 8. Example:

```js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { validateEntry } from '../scripts/site-model.mjs';
test('rejects a path-escaping manifest URL', () => {
  assert.throws(() => validateEntry({slug:'safe',url:'../outside/',title:'x',description:'x',createdAt:'2026-09-28',type:'html'}), /url/i);
});
```

- [ ] **Step 2: Run** `node --test tests/site-model.test.mjs`; expect a module-not-found failure.
- [ ] **Step 3: Implement** `validateEntry(entry)` with strict kebab-case slug and `url === 'artifacts/' + slug + '/'`, valid ISO date and unique slugs checked in `readSite`; resolve source and asset paths beneath root with `path.relative` containment checks. Return `{...entry, sourcePath}` from `readSite(root,{allowLegacy:false})`. Add `npm` scripts using `node` commands and keep runtime dependencies empty.
- [ ] **Step 4: Re-run** the tests (green) and `node --test`; commit only these files with `git commit -m "test: validate artifact registry and source paths"`.

### Task 2: Shared terminal shell, theme and generator

**Files:** Create `templates/home.html`, `templates/artifact.html`, `assets/design-system.css`, `assets/site.css`, `assets/site.js`, `scripts/render-site.mjs`, `tests/render-site.test.mjs`; modify generated `index.html` only through build. Add verified font assets/licenses only after checking redistribution rights in font metadata/upstream licenses.

**Interfaces:** Consumes `readSite(root)`; produces `renderHome(model)`, `renderArtifact(entry,fragment)`, `buildSite(root)` and DOM hook `[data-theme-toggle]`. Template fields are explicit (`TITLE`, `DESCRIPTION`, `CONTENT`, `TOC`, `MODULE_CSS`, `MODULE_JS`); escape metadata, not trusted markup fragments.

- [ ] **Step 1: Write failing tests** that render one entry and assert common chrome, breadcrumb, main/skip target, escaped `A < B & C`, descriptive theme button, paper token stylesheet, preserved content `<a href="diagrams/architecture.html#detail">`, and renderer determinism. Example:

```js
const html = renderArtifact({title:'A < B & C',slug:'sample',description:'Guide',createdAt:'2026-09-28',type:'html',url:'artifacts/sample/'}, '<a href="diagrams/map.html#n">Map</a>');
assert.match(html, /A &lt; B &amp; C/);
assert.match(html, /data-theme-toggle/);
assert.match(html, /href="diagrams\/map.html#n"/);
```

Add a browser/unit check for throwing `localStorage` (mock getter throws) and reduced-motion styles.
- [ ] **Step 2: Run** `node --test tests/render-site.test.mjs`; expect missing module/failures.
- [ ] **Step 3: Build minimal templates** with one centered window and real link/button controls; use ZIP `tokens/*.css` as reference, preserve token provenance, apply `data-theme="paper"` remap. `site.js` reads persisted mode defensively, sets `document.documentElement.dataset.theme`, updates button label/`aria-pressed`, and writes preference inside `try/catch`. Desktop window pane gets internal scroll; phone breakpoint removes height constraint and uses document scroll. Provide focus styles and `prefers-reduced-motion` override. Keep content-readable baseline without JS.
- [ ] **Step 4: Run tests and a local sample render**, inspect DOM and dark/paper screenshots at 390px and desktop; fix wrapping/focus issues; commit `git commit -m "feat: add shared terminal artifact shell and themes"`.

### Task 3: Rebuild the Explore homepage

**Files:** Modify `templates/home.html`, `assets/site.css`, `assets/site.js`; create `tests/home.test.mjs`, `tests/browser/home.mjs`.

**Interfaces:** Consumes validated `artifacts.json`; home uses the same shell, common theme button, list container and existing registry behavior, with `renderHome(model)` for static initial semantics and client-side enhancement.

- [ ] **Step 1: Write failing tests** for latest-by-date independent of registry order, newest/oldest/title sorts, substring search across title/description/slug/type/date, XSS escaping, loading/empty/error states, and `/`/Escape shortcuts. Browser test example:

```js
await page.goto(baseURL);
await page.getByRole('searchbox').fill('company brain');
assert.equal(await page.locator('[data-artifact-row]').count(), 1);
await page.getByRole('button', {name:/theme/i}).click();
assert.equal(await page.locator('html').getAttribute('data-theme'), 'paper');
```

- [ ] **Step 2: Run** `node --test tests/home.test.mjs` and browser test; expect failures on old home.
- [ ] **Step 3: Implement** a compact terminal archive rather than a command-only interface. Derive latest/count from registry, preserve readable static links on JS failure, make each row accessible, and preserve current sort/search UX. Do not add a build system *for search*: the build exists to standardize all pages.
- [ ] **Step 4: Run** Node and browser tests at desktop/mobile, inspect empty/error states, commit `git commit -m "feat: rebuild artifact registry in terminal shell"`.

### Task 4: Static article migration batch A

**Files:** Create `src/artifacts/<slug>/content.html` and optional `module.css` for each of the six slugs below; generated corresponding `artifacts/<slug>/index.html`; update `docs/migration-ledger.md`; add `tests/migration-static.test.mjs`.

**Interfaces:** Consumes `renderArtifact` from Task 2; each source fragment preserves article content and existing nested relative assets. Repeated migration test checks source/output heading, anchor, outbound link, code, and table counts with reviewed differences recorded in ledger.

- [ ] **Step 1: Write failing migration assertions** for the six original pages; parse original at git baseline (`git show 2cddb02:artifacts/<slug>/index.html`) and compare section headings, ids, href/src targets, code blocks, citations. Example: `assert.deepEqual(extractLinks(generated), extractLinks(original))` after normalizing only shell links. Expect missing source fragments.
- [ ] **Step 2: Run** `node --test tests/migration-static.test.mjs`; expect six missing-fragment failures.
- [ ] **Step 3: Extract article HTML, map global style to shared semantic classes or scoped CSS, and record exceptions** for each. Source fragments follow this shape (the actual body is copied from the corresponding original, not replaced with sample prose):

```html
<article data-artifact-content>
  <section id="executive-summary" class="artifact-section">
    <h2>1. Executive Summary</h2>
    <!-- Move the complete existing section content here unchanged. -->
  </section>
</article>
```
  - [ ] `amp-coding-agent-deep-research`
  - [ ] `bedrock-mantle-vs-runtime-2026-07-09`
  - [ ] `build-first-agentic-ai-roadmap`
  - [ ] `deepseek-harness-brief`
  - [ ] `goal-loop-engineering`
  - [ ] `headroom-how-it-works`
- [ ] **Step 4: Build, test six routes**, inspect one long article in both themes and 390px, commit `git commit -m "feat: migrate first static artifact batch"`.

### Task 5: Static article migration batch B

**Files:** Six new `src/artifacts/<slug>/content.html`, generated outputs, ledger; extend `tests/migration-static.test.mjs`.

**Interfaces:** Same per-article source contract as Task 4; source content must not contain global `html/body/:root` selectors or a second `<!doctype>`.

- [ ] **Step 1: Add failing baseline-to-generated heading/ID/asset/link assertions** for the listed six slugs; include `hello-world` local back-link and `signal-panel` example behavior.
- [ ] **Step 2: Run** `node --test tests/migration-static.test.mjs`; expect six new failures.
- [ ] **Step 3: Migrate and ledger-review**:
  - [ ] `headroom-litellm-eks-runbook`
  - [ ] `hello-world`
  - [ ] `hermes-dashboard-inspiration`
  - [ ] `litellm-bedrock-model-evaluation-playbook-2026-08-04`
  - [ ] `matt-pocock-skills-ai-assisted-engineering-playbook`
  - [ ] `matt-pocock-skills-learning-guide`
- [ ] **Step 4: Build, test six routes**, inspect the smoke page and a table-heavy page on mobile, commit `git commit -m "feat: migrate second static artifact batch"`.

### Task 6: Static article migration batch C and existing Archify links

**Files:** Six new `src/artifacts/<slug>/content.html`, generated outputs, ledger, `tests/migration-static.test.mjs`; retain `artifacts/slack-bot-private-mcp-per-user/diagrams/*.html` and all their relative paths.

**Interfaces:** Existing `diagrams/architecture.html`, `connect.html`, `call.html` continue resolving from the article and directly. The article's diagram figure must include an accessible iframe title, swipe/pan affordance, and full-size anchor.

- [ ] **Step 1: Add failing comparisons** for the six articles and exact `diagrams/*.html` URLs; test the relative iframe source and its full-size `<a>` resolve from `/artifacts/slack-bot-private-mcp-per-user/`.
- [ ] **Step 2: Run** `node --test tests/migration-static.test.mjs`; expect missing sources/diagram affordance failures.
- [ ] **Step 3: Migrate and ledger-review**:
  - [ ] `openclaw-enterprise-deployment`
  - [ ] `openclaw-enterprise-operating-model`
  - [ ] `signal-panel`
  - [ ] `slack-bot-private-mcp-per-user`
  - [ ] `web-search-for-ai-agents-2026`
  - [ ] `wedding-venue-comparison-2026-07-02`
- [ ] **Step 4: Build, test routes and local diagram HTTP responses**, inspect architecture page on phone and desktop, commit `git commit -m "feat: migrate final static articles and Archify links"`.

### Task 7: Interactive and diagram article migration (15 explicit pages)

**Files:** `src/artifacts/<slug>/content.html`, optional `module.js`/`module.css`, generated output for each listed slug; update ledger; create `tests/browser/interactive.mjs`, `tests/browser/diagrams.mjs`.

**Interfaces:** `module.js` runs after static content exists, scopes selectors to `[data-artifact-content]`, and does not redefine global shell state. Preserve original functional controls, deep links, and localStorage behaviors of courses; Archify HTML and Mermaid remain as linked/embedded modules. A page with third-party CDN failure still has readable article content and an error/fallback for diagrams.

- [ ] **Step 1: Write failing browser cases before migration**, one named assertion per listed artifact's primary interaction; for Mermaid, check an SVG appears after module load (or a readable fallback when CDN blocked); for Archify, use a mobile touch viewport to drag/pan the actual iframe/full-size diagram and assert content beyond the initial clipping becomes reachable. Test theme persistence from home to an artifact and exception when storage throws.
- [ ] **Step 2: Run** `node tests/browser/interactive.mjs` and `node tests/browser/diagrams.mjs`; record baseline interactions and initial failures. Use `git show 2cddb02:artifacts/<slug>/index.html` for content comparison, not the edited output.
- [ ] **Step 3: Migrate and test each module immediately**; split commits by independently reviewable behavior families (learning tools, filterable research, architecture guides), not one blind mass commit:
  - [ ] `ai-agent-git-worktrees`
  - [ ] `aws-ai-practitioner-journey`
  - [ ] `company-brain-technical-deep-dive` (Mermaid and Archify nested assets)
  - [ ] `deep-agents-typescript-guide` (highlight + Mermaid, anchors)
  - [ ] `deepagents-use-case-atlas-2026` (search/filter)
  - [ ] `ecs-fargate-terraform-field-guide`
  - [ ] `firstmate-pi-herdr-gitlab-runbook`
  - [ ] `forex-day-trading-starter` (calculator/progress)
  - [ ] `frontier-llm-prompt-field-guide-2026`
  - [ ] `graphify-daily-coding-field-guide`
  - [ ] `langchain-agent-engineer-fieldbook` (course progress)
  - [ ] `langgraph-learning-resources-2026` (filter)
  - [ ] `litellm-coding-agents` (tabs/copy)
  - [ ] `mcp-evaluation-private-stack-2026`
  - [ ] `orca-ai-development-runbook`
- [ ] **Step 4: Run browser checks after every family**, both themes and 390px; `tests/browser/diagrams.mjs` must prove a real Archify panning route and full-size link. Verify no iframe scroll trap, JS errors, or page overflow. Record any intentionally changed interaction in ledger and commit the family with `git commit -m "feat: migrate interactive artifact family"` (specific family in actual message).

### Task 8: Build validation, content inventory and accessible mobile regression

**Files:** Create `scripts/validate-site.mjs`, `tests/validate-site.test.mjs`, `tests/browser/site-smoke.mjs`; update `package.json`, `docs/migration-ledger.md`.

**Interfaces:** `npm run validate` exits nonzero for missing/extra manifest artifacts, missing nested assets, unsafe paths, content/anchor drift, missing shell/theme hook, generated drift. `npm run test:browser` checks every URL and selected critical interactions locally.

- [ ] **Step 1: Write failing validator fixtures** for a missing page, extra unregistered page, dead relative image/diagram link, and stale generated HTML; include a test that all 33 original slugs appear exactly once in migration ledger.
- [ ] **Step 2: Run** `node --test tests/validate-site.test.mjs`; expect failure.
- [ ] **Step 3: Implement** deterministic validation; build into a temporary directory or compare in-memory rendered HTML rather than mutating live generated files in check mode. In browser loop, visit manifest URL, assert `main` and theme button, inspect failed same-origin requests and console errors, verify document scrollWidth <= viewport+1 at 320/390/768/desktop, and exercise swipeable code/table/diagram regions.
- [ ] **Step 4: Run** `npm test && npm run validate && npm run test:browser` against loopback; confirm all 33, capture desktop/mobile screenshots in dark and paper, commit `git commit -m "test: validate full artifact migration and mobile layouts"`.

### Task 9: Repo-owned authoring skill and local publish helper

**Files:** Create `SKILL.md`, `AGENTS.md`, `templates/example-content.html`; modify `README.md`, `scripts/add-artifact.mjs`; create `tests/authoring.test.mjs`.

**Interfaces:** `node scripts/add-artifact.mjs --slug x --title ... --description ... --file content.html` writes `src/artifacts/x/content.html` and manifest entry, then instructs/executes build and validate; it does **not** push. Preserve existing slug/update behavior and document whether the helper accepts a fragment vs converts a full HTML input. Repo skill teaches only this contract; publishing is separately gated.

- [ ] **Step 1: Write a failing temporary-repo authoring test:** run helper with a new slug and fragment; assert source file, one manifest row, generated page has shell, repeated same-slug update has one row, invalid full document/unsafe slug fails without partial writes. Test `SKILL.md` includes template/theme/mobile/Archify/local-validation/publication gate references.
- [ ] **Step 2: Run** `node --test tests/authoring.test.mjs`; expect failure with old helper.
- [ ] **Step 3: Implement** helper transactionally (validate args/input before files; temporary writes or rollback on failure), add example content, update README and repo instructions with complete copy-paste local workflow and asset placement. If existing users supply full HTML, fail with a useful migration message rather than silently nesting it.
- [ ] **Step 4: Run** helper test + clean example build/validation in temp checkout; commit `git commit -m "docs: codify artifact design and local authoring skill"`.

### Task 10: Synchronize installed publisher skill, whole-branch review and local handoff

**Files:** Patch installed `github-pages-artifact-publisher/SKILL.md` and its `references/artifact-homepage-design.md` via `skill_manage` after repo contract passes; add final migration report/screenshots under a durable local location or attach them to the handoff. No push.

**Interfaces:** Publishing skill directs authors to repo-owned `SKILL.md`/template and `npm run build/validate`, updates the old “one self-contained HTML” default and two-file-commit assumptions for generated source/template assets, while retaining privacy/approval and post-push read-back safeguards for a future release.

- [ ] **Step 1: Write a failing contract check** comparing the skill's stated input/output workflow to the repo README (or a documented audit checklist): old `artifacts/<slug>/index.html` direct-copy guidance must be flagged.
- [ ] **Step 2: Run audit**, expect mismatch.
- [ ] **Step 3: Patch skill narrowly** with `skill_manage`, preserving its GitHub safety rules; add new build/source/asset/manifest commit requirements and explicitly distinguish local-preview approval from publication approval. Do not push any repo branch.
- [ ] **Step 4: Re-run audit, all tests, local server screenshots, `git diff --check`, and independent whole-branch review**; report exact local branch/commit, all 33 migration statuses, browser/diagram checks, known exceptions, and local preview instructions. Request Irfan's design signoff before any deployment.

## Execution handoff

Do not execute this plan until Irfan has reviewed it and chosen native or subagent-driven execution. In either mode, load the spec and applicable implementation skills, use TDD for new behavior, make small commits, and verify real browser behavior rather than relying only on generated markup.
