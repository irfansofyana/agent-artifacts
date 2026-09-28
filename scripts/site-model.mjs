import { readFileSync, existsSync } from 'node:fs';
import { resolve, join } from 'node:path';

export function validateEntry(entry) {
  if (!entry || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(entry.slug ?? '')) throw new Error('Invalid slug');
  if (entry.url !== `artifacts/${entry.slug}/`) throw new Error(`Invalid url for ${entry.slug}`);
  for (const key of ['title', 'description', 'type']) {
    if (typeof entry[key] !== 'string' || !entry[key].trim()) throw new Error(`Invalid ${key} for ${entry.slug}`);
  }
  const date = entry.createdAt;
  if (typeof date !== 'string' || !/^\d{4}-\d\d-\d\d$/.test(date) || new Date(`${date}T00:00:00Z`).toISOString().slice(0,10) !== date) throw new Error(`Invalid date for ${entry.slug}`);
  return entry;
}

export function readSite(root, {allowLegacy = false} = {}) {
  const manifest = JSON.parse(readFileSync(join(root, 'artifacts.json'), 'utf8'));
  if (!Array.isArray(manifest.artifacts)) throw new Error('Expected artifacts array');
  const seen = new Set();
  const artifacts = manifest.artifacts.map(raw => {
    const entry = validateEntry(raw);
    if (seen.has(entry.slug)) throw new Error(`Duplicate slug: ${entry.slug}`);
    seen.add(entry.slug);
    const sourcePath = resolve(root, 'src/artifacts', entry.slug, 'content.html');
    if (!existsSync(sourcePath) && !allowLegacy) throw new Error(`Missing source: ${entry.slug}`);
    return {...entry, sourcePath: existsSync(sourcePath) ? sourcePath : null};
  });
  return {artifacts};
}
