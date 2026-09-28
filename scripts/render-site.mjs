import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { dirname, resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { readSite } from './site-model.mjs';
import {parseFragment} from 'parse5';

const repo = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const homeTemplate = readFileSync(join(repo,'templates/home.html'),'utf8');
const articleTemplate = readFileSync(join(repo,'templates/artifact.html'),'utf8');
export const escapeHtml = value => String(value ?? '').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;');
function fill(template, fields) { return template.replace(/\{\{([A-Z_]+)\}\}/g, (_,key) => fields[key] ?? ''); }
function sorted(artifacts) { return [...artifacts].sort((a,b) => b.createdAt.localeCompare(a.createdAt) || a.title.localeCompare(b.title)); }
function row(entry,index) { return `<a class="artifact-card" data-artifact-row data-slug="${escapeHtml(entry.slug)}" data-date="${escapeHtml(entry.createdAt)}" data-type="${escapeHtml(entry.type)}" href="${escapeHtml(entry.url)}"><small>${String(index+1).padStart(2,'0')} · ${escapeHtml(entry.createdAt)} · ${escapeHtml(entry.type)}</small><h3>${escapeHtml(entry.title)}</h3><p>${escapeHtml(entry.description)}</p></a>`; }
export function renderHome(model) {
  const items = sorted(model.artifacts);
  const latest = items[0];
  return fill(homeTemplate, {
    TITLE: 'Irfan’s AI Agents — Published Artifacts', DESCRIPTION: 'Research, field guides, and working tools published by Irfan’s AI agents.',
    COUNT: String(items.length), ARTIFACTS: items.map(row).join('\n'),
    LATEST: latest ? `<div class="latest"><small>${escapeHtml(latest.createdAt)}</small><h3><a href="${escapeHtml(latest.url)}">${escapeHtml(latest.title)}</a></h3><p>${escapeHtml(latest.description)}</p></div>` : '<p>No artifacts published yet.</p>'
  });
}
function tocFor(fragment) {
  const headings=[];const seen=new Set();
  const attribute=(node,key)=>node.attrs?.find(a=>a.name===key)?.value;
  const text=node=>node.nodeName==='#text'?node.value:(node.childNodes||[]).map(text).join('');
  function visit(node,sectionId=''){
    const localSection=node.tagName==='section'?(attribute(node,'id')||sectionId):sectionId;
    if(node.tagName==='h2'||node.tagName==='h3'){
      const id=attribute(node,'id')||localSection;
      if(id&&!seen.has(id)){headings.push({id,label:text(node).trim()});seen.add(id)}
    }
    for(const child of node.childNodes||[])visit(child,localSection);
  }
  visit(parseFragment(fragment));
  if(headings.length<3)return {desktop:'',mobile:''};
  const links=headings.map(({id,label})=>`<a href="#${escapeHtml(id)}">${escapeHtml(label)}</a>`).join('');
  return {desktop:`<nav class="article-toc" aria-label="On this page">${links}</nav>`,mobile:`<details class="mobile-toc"><summary>On this page · sections</summary>${links}</details>`};
}
export function renderArtifact(entry,fragment,{moduleCss='',moduleJs=''}={}) {
  const toc = tocFor(fragment);
  const content = `<div class="article-layout">${toc.desktop}<div class="artifact-body">${toc.mobile}${fragment}</div></div>`;
  return fill(articleTemplate, {
    TITLE:escapeHtml(entry.title), DESCRIPTION:escapeHtml(entry.description),SLUG:escapeHtml(entry.slug),TYPE:escapeHtml(entry.type),DATE:escapeHtml(entry.updatedAt ?? entry.createdAt),
    CONTENT:content,TOC:'', MODULE_CSS: moduleCss ? `<link rel="stylesheet" href="${escapeHtml(moduleCss)}">` : '', MODULE_JS: moduleJs ? `<script src="${escapeHtml(moduleJs)}" defer></script>` : ''
  });
}
export function buildSite(root = repo,{allowLegacy=false}={}) {
  const model=readSite(root,{allowLegacy});
  writeFileSync(join(root,'index.html'),renderHome(model));
  for(const entry of model.artifacts) {
    if (!entry.sourcePath) continue;
    const dir=join(root,'artifacts',entry.slug);
    const fragment=readFileSync(entry.sourcePath,'utf8');
    const sourceDir=dirname(entry.sourcePath);
    const moduleCss=existsSync(join(sourceDir,'module.css')) ? '../../src/artifacts/'+entry.slug+'/module.css' : '';
    const moduleJs=existsSync(join(sourceDir,'module.js')) ? '../../src/artifacts/'+entry.slug+'/module.js' : '';
    writeFileSync(join(dir,'index.html'),renderArtifact(entry,fragment,{moduleCss,moduleJs}));
  }
  return model.artifacts.length;
}
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const count=buildSite(repo,{allowLegacy:process.argv.includes('--allow-legacy')});
  console.log(`Built ${count} registered artifact pages`);
}
