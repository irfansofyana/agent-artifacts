#!/usr/bin/env node
// One-time source extraction. Run with explicit slugs; never overwrite migrated sources.
import { execFileSync } from 'node:child_process';
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { join, dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parse, serializeOuter } from 'parse5';
import postcss from 'postcss';
import selectorParser from 'postcss-selector-parser';

const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const refresh=process.argv.includes('--refresh-css');
const slugs=process.argv.slice(2).filter(arg=>arg!=='--refresh-css');
if(!slugs.length) throw new Error('Pass explicit slugs to migrate');
function walk(node,predicate,out=[]) {if(predicate(node))out.push(node);for(const child of node.childNodes||[])walk(child,predicate,out);return out}
function attrs(node) {return Object.fromEntries((node.attrs||[]).map(a=>[a.name,a.value]))}
function text(node) {return (node.childNodes||[]).map(child=>child.value||text(child)).join('')}
function scopedCss(css) {
  let tree;
  try { tree=postcss.parse(css); } catch(err) {throw new Error(`Invalid legacy CSS: ${err.message}`)}
  tree.walkRules(rule=>{
    if(rule.parent?.name?.includes('keyframes')) return;
    rule.selector=selectorParser(selectors=>{
      selectors.each(sel=>{
        sel.walkPseudos(p=>{if(p.value===':root')p.replaceWith(selectorParser.className({value:'legacy-content'}))});
        const first=sel.nodes.find(n=>n.type!=='comment');
        if(first?.type==='tag' && /^(html|body)$/.test(first.value)){
          first.replaceWith(selectorParser.className({value:'legacy-content'}));
          if(sel.nodes[1]?.type==='combinator' && sel.nodes[2]?.type==='tag' && /^(html|body)$/.test(sel.nodes[2].value)) sel.nodes[2].remove();
        } else if(!(first?.type==='class' && first.value==='legacy-content')){
          sel.prepend(selectorParser.combinator({value:' '}));sel.prepend(selectorParser.className({value:'legacy-content'}));
        }
      });
    }).processSync(rule.selector);
    rule.walkDecls(decl=>{
      if(decl.prop.startsWith('--') && /^#|^rgb|^hsl/i.test(decl.value)) {
        const name=decl.prop.toLowerCase();
        if(/bg|background|panel|surface|card|gray-100|gray-200|purple-light/.test(name)) decl.value='var(--bg-terminal)';
        else if(/muted|gray|secondary/.test(name)) decl.value='var(--text-secondary)';
        else if(/text|ink|foreground|^--fg$/.test(name)) decl.value='var(--text-primary)';
        else if(/border|line/.test(name)) decl.value='var(--border-chrome)';
        else if(/cyan|link/.test(name)) decl.value='var(--accent-cyan)';
        else if(/amber|gold|warn/.test(name)) decl.value='var(--accent-amber)';
        else if(/red|danger|error/.test(name)) decl.value='var(--accent-error)';
        else decl.value='var(--phosphor)';
      }
      if(decl.value===`var(${decl.prop})`) decl.remove();
      if (decl.prop==='font-family') decl.value='var(--font-mono)';
      if (decl.prop==='color' && !/^(inherit|transparent|currentColor|var\()/i.test(decl.value)) decl.value='var(--text-secondary)';
      if (/^background(?:-color)?$/.test(decl.prop) && !/url\(|transparent|none|var\(/i.test(decl.value)) decl.value='var(--surface-output)';
      if (decl.prop==='box-shadow'||decl.prop==='text-shadow') decl.value='none';
    });
  });
  return tree.toString();
}
for(const slug of slugs){
 if(!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug)) throw new Error(`Invalid slug: ${slug}`);
 const input=join(root,'artifacts',slug,'index.html');
 const sourceDir=join(root,'src/artifacts',slug),output=join(sourceDir,'content.html');
 if(existsSync(output) && !refresh) throw new Error(`Source already exists: ${output}`);
 const doc=parse(execFileSync('git',['show',`2cddb02:artifacts/${slug}/index.html`],{cwd:root,encoding:'utf8'}));
 const body=walk(doc,n=>n.tagName==='body')[0],head=walk(doc,n=>n.tagName==='head')[0];
 if(!body||!head) throw new Error(`Incomplete HTML in ${slug}`);
 const styles=walk(head,n=>n.tagName==='style').map(text);
 const stylesheetLinks=walk(head,n=>n.tagName==='link' && attrs(n).rel==='stylesheet').map(n=>serializeOuter(n));
 const headScripts=walk(head,n=>n.tagName==='script').map(n=>serializeOuter(n));
 mkdirSync(sourceDir,{recursive:true});
 const content=`<div class="legacy-content" data-artifact-content>\n${body.childNodes.map(serializeOuter).join('')}\n</div>\n${headScripts.join('\n')}`.trimEnd()+'\n';
 if(!refresh) writeFileSync(output,(stylesheetLinks.join('\n')+'\n'+content).trimEnd()+'\n');
 if(styles.length)writeFileSync(join(sourceDir,'module.css'),styles.map(scopedCss).join('\n').split('\n').map(line=>line.trimEnd()).join('\n').trimEnd()+'\n');
 console.log(`Migrated ${slug}: ${content.length} HTML chars; ${styles.length} style blocks`);
}
