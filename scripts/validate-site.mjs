import { existsSync,readFileSync,readdirSync } from 'node:fs';
import { join,resolve,relative,dirname,extname,sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parse } from 'parse5';
import { readSite } from './site-model.mjs';
import { renderHome,renderArtifact } from './render-site.mjs';
const repo=resolve(dirname(fileURLToPath(import.meta.url)),'..');
function walk(node,visit){visit(node);for(const child of node.childNodes||[])walk(child,visit)}
function attr(node,key){return node.attrs?.find(a=>a.name===key)?.value}
function within(root,path){const r=relative(root,path);return r===''||(!r.startsWith('..'+sep)&&r!=='..'&&!r.startsWith(sep))}
function links(html){const found=[];walk(parse(html),node=>{
 for(const key of ['src','href']){const value=attr(node,key);if(value)found.push({tag:node.tagName,key,value})}
 });return found}
function assetIssues(root,slug,html){const errors=[];const base=join(root,'artifacts',slug);for(const {tag,key,value} of links(html)){
 if(/^(?:[a-z][a-z0-9+.-]*:|\/\/|#|\?)/i.test(value))continue;
 if(value.startsWith('/'))continue; // root-relative URLs require a deployment base and are not local files
 const clean=value.split(/[?#]/)[0];if(!clean)continue;
 const pathname=resolve(base,decodeURIComponent(clean));
 if(!within(root,pathname)){errors.push(`${slug}: unsafe local asset ${value}`);continue}
 // Navigation to an absent relative file/route is broken; check assets and HTML routes alike.
 if(!existsSync(pathname)&&!existsSync(join(pathname,'index.html')))errors.push(`${slug}: missing local asset ${value} (${tag} ${key})`);
 }return errors}
export function validateSite(root=repo){
 const issues=[];let model;
 try{model=readSite(root)}catch(e){return [`invalid registry/source: ${e.message}`]}
 const expected=new Set(model.artifacts.map(e=>e.slug));
 const home=join(root,'index.html');
 if(!existsSync(home))issues.push('missing generated homepage');
 else if(readFileSync(home,'utf8')!==renderHome(model))issues.push('stale generated homepage');
 const artifacts=join(root,'artifacts');
 if(existsSync(artifacts))for(const name of readdirSync(artifacts,{withFileTypes:true}).filter(x=>x.isDirectory()).map(x=>x.name)){
  if(existsSync(join(artifacts,name,'index.html'))&&!expected.has(name))issues.push(`unregistered page: ${name}`);
 }
 for(const entry of model.artifacts){
  const slug=entry.slug;const dest=join(artifacts,slug,'index.html');
  if(!existsSync(dest)){issues.push(`${slug}: missing generated page`);continue}
  const fragment=readFileSync(entry.sourcePath,'utf8');
  const sourceDir=dirname(entry.sourcePath);
  const css=existsSync(join(sourceDir,'module.css'))?`../../src/artifacts/${slug}/module.css`:'';
  const js=existsSync(join(sourceDir,'module.js'))?`../../src/artifacts/${slug}/module.js`:'';
  const expectedHtml=renderArtifact(entry,fragment,{moduleCss:css,moduleJs:js});
  const actual=readFileSync(dest,'utf8');
  if(actual!==expectedHtml)issues.push(`${slug}: stale generated page`);
  if(!actual.includes('data-theme-toggle')||!actual.includes('id="site-main"'))issues.push(`${slug}: missing shared shell/theme`);
  issues.push(...assetIssues(root,slug,fragment));
 }
 const ledger=join(root,'docs/migration-ledger.md');
 if(existsSync(ledger)){
  const rows=[...readFileSync(ledger,'utf8').matchAll(/^\| ([a-z0-9-]+) \| migrated \|/gm)].map(m=>m[1]);
  for(const slug of expected){const n=rows.filter(x=>x===slug).length;if(n!==1)issues.push(`ledger: ${slug} appears ${n} times`)}
  for(const slug of rows)if(!expected.has(slug))issues.push(`ledger: unregistered ${slug}`);
 }
 return issues;
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const issues=validateSite(repo);if(issues.length){console.error(issues.join('\n'));process.exitCode=1}else console.log('Validated homepage and all 33 registered artifact pages');
}
