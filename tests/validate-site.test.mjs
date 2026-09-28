import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync,mkdirSync,writeFileSync,rmSync,readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { validateSite } from '../scripts/validate-site.mjs';
import { renderHome,renderArtifact } from '../scripts/render-site.mjs';
const entry={slug:'example',title:'Example',description:'Example page',url:'artifacts/example/',type:'guide',createdAt:'2026-01-01'};
function fixture(){
 const root=mkdtempSync(join(tmpdir(),'artifact-validation-'));
 mkdirSync(join(root,'artifacts/example'),{recursive:true});mkdirSync(join(root,'src/artifacts/example'),{recursive:true});
 writeFileSync(join(root,'artifacts.json'),JSON.stringify({artifacts:[entry]}));
 const content='<div class="legacy-content" data-artifact-content><h2 id="intro">Intro</h2><p>Hello.</p></div>';
 writeFileSync(join(root,'src/artifacts/example/content.html'),content);
 writeFileSync(join(root,'index.html'),renderHome({artifacts:[entry]}));
 writeFileSync(join(root,'artifacts/example/index.html'),renderArtifact(entry,content));
 return root;
}
function withFixture(fn){const root=fixture();try{fn(root)}finally{rmSync(root,{recursive:true,force:true})}}
test('rejects missing registered generated page',()=>withFixture(root=>{
 rmSync(join(root,'artifacts/example/index.html'));
 assert.match(validateSite(root).join('\n'),/missing generated page/i);
}));
test('rejects unregistered page',()=>withFixture(root=>{
 mkdirSync(join(root,'artifacts/stray'));writeFileSync(join(root,'artifacts/stray/index.html'),'stray');
 assert.match(validateSite(root).join('\n'),/unregistered/i);
}));
test('rejects broken local image or diagram asset',()=>withFixture(root=>{
 const content=readFileSync(join(root,'src/artifacts/example/content.html'),'utf8').replace('Hello.','<img src="missing.png" alt="missing"><iframe src="diagrams/none.html"></iframe>');
 writeFileSync(join(root,'src/artifacts/example/content.html'),content);
 writeFileSync(join(root,'artifacts/example/index.html'),renderArtifact(entry,content));
 assert.match(validateSite(root).join('\n'),/missing.*(?:missing\.png|diagrams\/none\.html)/i);
}));
test('rejects stale generated output without rewriting it',()=>withFixture(root=>{
 const path=join(root,'artifacts/example/index.html');writeFileSync(path,'stale');
 assert.match(validateSite(root).join('\n'),/stale generated page/i);
 assert.equal(readFileSync(path,'utf8'),'stale');
}));
test('rejects unsafe relative asset traversal',()=>withFixture(root=>{
 const content='<div class="legacy-content"><img src="../../../../private.txt"></div>';
 writeFileSync(join(root,'src/artifacts/example/content.html'),content);
 writeFileSync(join(root,'artifacts/example/index.html'),renderArtifact(entry,content));
 assert.match(validateSite(root).join('\n'),/unsafe local asset/i);
}));
test('all original slugs appear exactly once in migration ledger',()=>{
 const root=new URL('..',import.meta.url).pathname;
 assert.deepEqual(validateSite(root).filter(e=>e.includes('ledger')),[]);
});
