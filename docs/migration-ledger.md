# Artifact migration ledger

Baseline: commit `2cddb02` (33 registered HTML artifacts). The migration utility extracts the full original body into a scoped content fragment, preserves links, IDs, code and tables, and remaps legacy palette declarations to the shared design tokens. Original `h1` and legacy `.toc` remain in source for audit but are visually replaced by the common article hero and generated navigation. Site-level CSS cannot guarantee every bespoke module is visually correct: browser checks and per-page exceptions are required.

| Slug | Source | Structural comparison | Browser status | Exception / follow-up |
| --- | --- | --- | --- | --- |
| amp-coding-agent-deep-research | migrated | ids/links/code/tables match | mobile dark/paper: no overflow or page errors | Original title/TOC visually suppressed; subtitle retained |
| bedrock-mantle-vs-runtime-2026-07-09 | migrated | ids/links/code/tables match | mobile dark/paper: no overflow or page errors | Dense tables need gesture inspection |
| build-first-agentic-ai-roadmap | migrated | ids/links/code/tables match | mobile dark/paper: no overflow or page errors | External font import may be redundant |
| deepseek-harness-brief | migrated | ids/links/code/tables match | mobile dark/paper: no overflow or page errors | Cards need visual inspection |
| goal-loop-engineering | migrated | ids/links/code/tables match | mobile dark/paper: no overflow or page errors | Grid needs visual inspection |
| headroom-how-it-works | migrated | ids/links/code/tables match | mobile dark/paper: no overflow or page errors | Flow needs gesture inspection |
| headroom-litellm-eks-runbook | migrated | ids/links/code/tables match | mobile dark/paper: no overflow or page errors | Scoped legacy layout |
| hello-world | migrated | ids/links/code/tables match | mobile dark/paper: no overflow or page errors | Smoke page retains registry back-link |
| hermes-dashboard-inspiration | migrated | ids/links/code/tables match | mobile dark/paper: no overflow or page errors | Scoped legacy layout |
| litellm-bedrock-model-evaluation-playbook-2026-08-04 | migrated | ids/links/code/tables match | mobile dark/paper: no overflow or page errors | Four tables need swipe inspection |
| matt-pocock-skills-ai-assisted-engineering-playbook | migrated | ids/links/code/tables match | mobile dark/paper: no overflow or page errors | Five tables need swipe inspection |
| matt-pocock-skills-learning-guide | migrated | ids/links/code/tables match | mobile dark/paper: no overflow or page errors | Two tables need swipe inspection |
