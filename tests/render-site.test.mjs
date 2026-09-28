import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { runInNewContext } from 'node:vm';
import { renderArtifact, renderHome } from '../scripts/render-site.mjs';

const entry = {title:'A < B & C',slug:'sample',description:'Guide & map',createdAt:'2026-09-28',type:'html',url:'artifacts/sample/'};
test('artifact shell escapes metadata and retains a relative diagram link', () => {
  const html = renderArtifact(entry,'<article data-artifact-content><a href="diagrams/architecture.html#detail">Map</a></article>');
  assert.match(html,/A &lt; B &amp; C/);
  assert.match(html,/Guide &amp; map/);
  assert.doesNotMatch(html,/<title>A < B/);
  assert.match(html,/href="diagrams\/architecture.html#detail"/);
  assert.match(html,/data-theme-toggle/);
  assert.match(html,/href="\.\.\/\.\.\/"/);
  assert.match(html,/<main\b/);
  assert.match(html,/href="#site-main"/);
});
test('short articles without a TOC render in a full-width article column',()=>{
 const html=renderArtifact(entry,'<div data-artifact-content><h2>Only section</h2><p>Text</p></div>');
 assert.match(html,/<div class="article-layout article-layout--plain"><div class="artifact-body">/);
 assert.doesNotMatch(html,/class="article-toc"/);
});

test('section IDs become shared navigation even when heading has no ID',()=>{
 const entry={slug:'section-test',title:'Guide',description:'Guide',type:'html',createdAt:'2026-01-01',url:'artifacts/section-test/'};
 const fragment='<div class="legacy-content"><section id="first"><h2>First</h2></section><section id="second"><h2>Second</h2></section><section id="third"><h2>Third</h2></section></div>';
 const html=renderArtifact(entry,fragment);
 assert.match(html,/<nav class="article-toc"[^>]*>/);
 assert.match(html,/<a href="#first">First<\/a>/);
 assert.match(html,/<a href="#third">Third<\/a>/);
});

test('theme button remains usable when storage is unavailable', () => {
   const script = readFileSync(new URL('../assets/site.js',import.meta.url),'utf8');
  const handlers = {};
  const button = {textContent:'',setAttribute(k,v){this[k]=v},addEventListener(k,fn){handlers[k]=fn}};
  const root = {dataset:{}};
  runInNewContext(script, {document:{documentElement:root,querySelector:selector=>selector==='[data-theme-toggle]'?button:null},get localStorage(){throw new Error('blocked')}});
  handlers.click();
  assert.equal(root.dataset.theme,'paper');
  assert.equal(button.textContent,'Theme: Paper');
});
test('same input renders byte-for-byte equal', () => {
  assert.equal(renderArtifact(entry,'<p>hello</p>'),renderArtifact(entry,'<p>hello</p>'));
});
test('home has the same shell and explicit paper theme support', () => {
  const html = renderHome({artifacts:[entry]});
  assert.match(html,/data-theme-toggle/);
  assert.match(html,/assets\/design-system.css/);
  assert.match(html,/sample/);
  assert.match(readFileSync(new URL('../assets/design-system.css',import.meta.url),'utf8'),/\[data-theme="paper"\]/);
  assert.match(readFileSync(new URL('../assets/site.css',import.meta.url),'utf8'),/prefers-reduced-motion/);
});
