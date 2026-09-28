import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { readSite, validateEntry } from '../scripts/site-model.mjs';

const valid = {slug:'hello-world',title:'Hello',description:'A page',createdAt:'2026-09-28',type:'html',url:'artifacts/hello-world/'};
function fixture(entries, withSource = true) {
  const root = mkdtempSync(join(tmpdir(),'artifact-model-'));
  writeFileSync(join(root,'artifacts.json'), JSON.stringify({artifacts:entries}));
  if (withSource) {
    mkdirSync(join(root,'src/artifacts/hello-world'),{recursive:true});
    writeFileSync(join(root,'src/artifacts/hello-world/content.html'),'<article>Hello</article>');
  }
  return root;
}
test('accepts a registered page with source', () => {
  const root = fixture([valid]);
  try { assert.equal(readSite(root).artifacts[0].sourcePath,join(root,'src/artifacts/hello-world/content.html')); }
  finally { rmSync(root,{recursive:true,force:true}); }
});
test('rejects duplicate slugs', () => {
  const root = fixture([valid,valid]);
  try { assert.throws(()=>readSite(root),/duplicate/i); }
  finally { rmSync(root,{recursive:true,force:true}); }
});
test('rejects a path-escaping slug', () => {
  assert.throws(()=>validateEntry({...valid,slug:'../escape'}),/slug/i);
});
test('rejects an external or escaping manifest URL', () => {
  for (const url of ['../outside/','https://evil.example/']) assert.throws(()=>validateEntry({...valid,url}),/url/i);
});
test('requires the source in strict mode but permits a legacy migration', () => {
  const root = fixture([valid],false);
  try {
    assert.throws(()=>readSite(root),/source/i);
    assert.equal(readSite(root,{allowLegacy:true}).artifacts[0].sourcePath,null);
  } finally { rmSync(root,{recursive:true,force:true}); }
});
test('rejects nonexistent dates', () => {
  assert.throws(()=>validateEntry({...valid,createdAt:'2026-02-30'}),/date/i);
});
