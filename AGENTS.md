# Agent instructions

Before changing this site, follow [`SKILL.md`](SKILL.md) and the local workflow in [`README.md`](README.md).

- Edit `src/artifacts/<slug>/content.html`, optional scoped `module.css`/`module.js`, and `artifacts.json`; `artifacts/<slug>/index.html` and root `index.html` are generated.
- Do not replace the shared template or bypass the dark/paper theme. Preserve article URLs, anchors, live interactive controls and relative assets.
- Run `npm run build && npm test && npm run validate && npm run test:browser` using a loopback preview server.
- Treat this public repo as publication: screen for secrets and sensitive data. Local preview is not authorization to publish.
