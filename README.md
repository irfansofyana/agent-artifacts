# Agent artifacts

A static publication shelf for Irfan's AI agents: https://irfansp.dev/agent-artifacts/. GitHub Pages serves files from the `main` branch root. The repo owns the terminal-style design and every artifact's source; generated pages are committed for Pages, not hand-edited.

## Structure

```text
artifacts.json                       registry / stable URLs
src/artifacts/<slug>/content.html    article body fragment
src/artifacts/<slug>/module.css      optional scoped CSS
src/artifacts/<slug>/module.js       optional interaction
artifacts/<slug>/index.html         generated publication page
artifacts/<slug>/diagrams/           optional live diagram assets
index.html                           generated homepage
templates/{home,artifact}.html       shared page shell
assets/{design-system,site}.css      tokens and layout
assets/site.js                       theme and homepage controls
SKILL.md, AGENTS.md                  agent-facing authoring contract
```

## Create or update locally

Requires Node.js and npm. Read [`SKILL.md`](SKILL.md) before authoring.

```bash
npm ci
node scripts/add-artifact.mjs \
  --slug example-guide \
  --title "Example Guide" \
  --description "A concise guide." \
  --file templates/example-content.html
npm run build
npm test
npm run validate
npm run preview
```

In another shell run `npm run test:browser`, then visit `http://127.0.0.1:4173/`. The helper accepts a **body fragment**, not a complete `<!doctype html>` page. It updates source, `artifacts.json`, and generated pages; it does not push. Existing slugs are updated in place. Add nested diagrams and images under `artifacts/<slug>/` with relative links. Source modules must use shared design tokens and be scoped to the artifact content.

For a change to one existing page, edit `src/artifacts/<slug>/content.html` (and its optional module files), then run `npm run build && npm test && npm run validate`. The generated homepage and article are checked into git alongside source. Browser checks need the loopback preview server running.

## Publication gate

This is a public site. Screen for credentials and private/company-sensitive content; check links and mobile interactions. **Obtain approval before publishing** a new artifact or deploying a redesign. After approval, commit the source, manifest, generated output and assets together; push without force. Verify the remote commit and file contents, then separately check the live Pages URL. A push is not proof that Pages has finished deploying.
