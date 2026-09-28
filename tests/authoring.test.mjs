import {test} from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,mkdirSync,writeFileSync,readFileSync,existsSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {execFileSync,spawnSync} from 'node:child_process';
import {validateSite} from '../scripts/validate-site.mjs';
const project=new URL('..',import.meta.url).pathname;
const helper=join(project,'scripts/add-artifact.mjs');
const initial={artifacts:[]};
function withRepo(fn){const root=mkdtempSync(join(tmpdir(),'artifact-author-'));try{mkdirSync(join(root,'artifacts'));mkdirSync(join(root,'src/artifacts'),{recursive:true});mkdirSync(join(root,'docs'),{recursive:true});writeFileSync(join(root,'docs/migration-ledger.md'),'# Migration ledger\n');writeFileSync(join(root,'artifacts.json'),JSON.stringify(initial));fn(root)}finally{rmSync(root,{recursive:true,force:true})}}
function add(root,source,slug='new-guide',title='New Guide'){
 return spawnSync(process.execPath,[helper,'--slug',slug,'--title',title,'--description','Useful guide.','--date','2026-09-28','--file',source],{cwd:root,env:{...process.env,ARTIFACT_REPO_ROOT:root},encoding:'utf8'});
}
test('fragment creates source, manifest entry and shared-shell output; updating keeps one row',()=>withRepo(root=>{
 const source=join(root,'fragment.html');writeFileSync(source,'<section><h2 id="start">Start</h2><p>Content.</p></section>');
 const created=add(root,source);assert.equal(created.status,0,created.stderr);
 const dest=join(root,'src/artifacts/new-guide/content.html');assert.equal(readFileSync(dest,'utf8'),readFileSync(source,'utf8'));
 const generated=readFileSync(join(root,'artifacts/new-guide/index.html'),'utf8');assert.match(generated,/data-theme-toggle/);assert.match(generated,/<h2 id="start">/);
 assert.equal(JSON.parse(readFileSync(join(root,'artifacts.json'),'utf8')).artifacts.length,1);
 assert.equal(add(root,source,'new-guide','Updated Guide').status,0);
 const entries=JSON.parse(readFileSync(join(root,'artifacts.json'),'utf8')).artifacts;
 assert.equal(entries.length,1);assert.equal(entries[0].title,'Updated Guide');
 assert.deepEqual(validateSite(root),[],`new page must validate using documented workflow`);
}));
test('rejects full document and unsafe slug before writing anything',()=>withRepo(root=>{
 const source=join(root,'full.html');writeFileSync(source,'<!doctype html><html><body><h1>Old shell</h1></body></html>');
 const before=readFileSync(join(root,'artifacts.json'),'utf8');
 const rejected=add(root,source);assert.notEqual(rejected.status,0);assert.match(rejected.stderr,/fragment|full document/i);
 assert.equal(readFileSync(join(root,'artifacts.json'),'utf8'),before);
 assert.equal(existsSync(join(root,'src/artifacts/new-guide')),false);
 writeFileSync(source,'<h2>Safe</h2>');assert.notEqual(add(root,source,'../escape').status,0);
 assert.equal(readFileSync(join(root,'artifacts.json'),'utf8'),before);
}));
test('repo authoring skill blocks sensitive content across page, metadata and assets',()=>{
 const skill=readFileSync(join(project,'SKILL.md'),'utf8');
 for(const term of ['company-confidential','private person','private file','metadata','screenshots','do not publish','anonymize'])assert.match(skill,new RegExp(term,'i'),term);
});

test('repo instructions codify shared template, themes, mobile, Archify, validation and publish gate',()=>{
 const skill=readFileSync(join(project,'SKILL.md'),'utf8');
 for(const term of ['templates/artifact.html','theme','mobile','Archify','npm run validate','approval'])assert.match(skill,new RegExp(term,'i'));
});
