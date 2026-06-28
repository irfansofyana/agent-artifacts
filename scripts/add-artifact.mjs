#!/usr/bin/env node

import { copyFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const args = parseArgs(process.argv.slice(2));

if (args.help) {
  printUsage();
  process.exit(0);
}

const required = ["slug", "title", "description", "file"];
const missing = required.filter((key) => !args[key]);

if (missing.length) {
  console.error(`Missing required argument(s): ${missing.join(", ")}`);
  printUsage();
  process.exit(1);
}

const slug = validateSlug(args.slug);
const sourceFile = resolve(args.file);

if (!existsSync(sourceFile)) {
  console.error(`Artifact file does not exist: ${sourceFile}`);
  process.exit(1);
}

const artifactDir = resolve(repoRoot, "artifacts", slug);
const artifactFile = resolve(artifactDir, "index.html");
const manifestFile = resolve(repoRoot, "artifacts.json");
const createdAt = args.date ?? new Date().toISOString().slice(0, 10);

mkdirSync(artifactDir, { recursive: true });
copyFileSync(sourceFile, artifactFile);

const manifest = JSON.parse(readFileSync(manifestFile, "utf8"));
const artifacts = Array.isArray(manifest.artifacts) ? manifest.artifacts : [];
const nextEntry = {
  title: args.title,
  slug,
  description: args.description,
  createdAt,
  type: args.type ?? "html",
  url: `artifacts/${slug}/`,
};

const existingIndex = artifacts.findIndex((artifact) => artifact.slug === slug);

if (existingIndex >= 0) {
  artifacts[existingIndex] = nextEntry;
} else {
  artifacts.unshift(nextEntry);
}

manifest.artifacts = artifacts;
writeFileSync(manifestFile, `${JSON.stringify(manifest, null, 2)}\n`);

console.log(`Published artifact draft: artifacts/${slug}/index.html`);
console.log(`Public URL after push: https://irfansp.dev/agent-artifacts/artifacts/${slug}/`);

function parseArgs(values) {
  const parsed = {};

  for (let index = 0; index < values.length; index += 1) {
    const value = values[index];

    if (value === "--help" || value === "-h") {
      parsed.help = true;
      continue;
    }

    if (!value.startsWith("--")) {
      console.error(`Unexpected argument: ${value}`);
      printUsage();
      process.exit(1);
    }

    const key = value.slice(2);
    const next = values[index + 1];

    if (!next || next.startsWith("--")) {
      console.error(`Missing value for --${key}`);
      printUsage();
      process.exit(1);
    }

    parsed[key] = next;
    index += 1;
  }

  return parsed;
}

function validateSlug(value) {
  if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(value)) {
    console.error("Slug must use lowercase letters, numbers, and hyphens only.");
    process.exit(1);
  }

  return value;
}

function printUsage() {
  console.log(`
Usage:
  node scripts/add-artifact.mjs \\
    --slug artifact-slug \\
    --title "Artifact Title" \\
    --description "Short description." \\
    --file /path/to/index.html

Optional:
  --date YYYY-MM-DD
  --type html
`);
}
