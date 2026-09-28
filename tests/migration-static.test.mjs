import { test } from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { join } from 'node:path';
import { parse } from 'parse5';
import { renderArtifact } from '../scripts/render-site.mjs';
import { readSite } from '../scripts/site-model.mjs';

const root=new URL('..',import.meta.url).pathname;
const selected=(process.env.MIGRATION_SLUGS || 'amp-coding-agent-deep-research,bedrock-mantle-vs-runtime-2026-07-09,build-first-agentic-ai-roadmap,deepseek-harness-brief,goal-loop-engineering,headroom-how-it-works').split(',');
const manifest=new Map(readSite(root,{allowLegacy:true}).artifacts.map(e=>[e.slug,e]));
function descendants(node,fn,out=[]){if(fn(node))out.push(node);for(const child of node.childNodes||[])descendants(child,fn,out);return out}
function attrs(node){return Object.fromEntries((node.attrs||[]).map(x=>[x.name,x.value]))}
function facts(html){
 const doc=parse(html);const body=descendants(doc,n=>n.tagName==='body')[0];
 const content=descendants(body,n=>(n.attrs||[]).some(a=>a.name==='class' && a.value.split(/\s+/).includes('legacy-content')))[0] ?? body;
 const all=descendants(content,n=>Boolean(n.tagName));
 return {ids:all.map(n=>attrs(n).id).filter(Boolean).sort(),links:all.flatMap(n=>['href','src'].map(k=>attrs(n)[k]).filter(Boolean)).sort(),codes:all.filter(n=>n.tagName==='pre').length,tables:all.filter(n=>n.tagName==='table').length};
}
for(const slug of selected)test(`${slug}: migrated content preserves original ids, links, code and tables`,()=>{
 const source=join(root,'src/artifacts',slug,'content.html');
 assert.ok(existsSync(source),`Missing migrated source: ${slug}`);
 const before=execFileSync('git',['show',`2cddb02:artifacts/${slug}/index.html`],{cwd:root,encoding:'utf8'});
 const fragment=readFileSync(source,'utf8');
 const expected=facts(before),actual=facts(fragment);
 assert.deepEqual(actual,expected);
 const emitted=renderArtifact(manifest.get(slug),fragment);
 const cssPath=join(root,'src/artifacts',slug,'module.css');
 if(existsSync(cssPath)) {
   const css=readFileSync(cssPath,'utf8');
   assert.doesNotMatch(css,/--(?:purple|bg|text)\s*:\s*#[0-9a-f]{3,8}/i,`unmapped legacy palette: ${slug}`);
 }
 for(const id of expected.ids)assert.ok(emitted.includes(`id="${id}"`),`lost #${id}`);
 assert.ok(emitted.includes('data-theme-toggle'));
});
