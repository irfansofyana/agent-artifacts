import { test } from 'node:test';
import assert from 'node:assert/strict';
import { renderHome } from '../scripts/render-site.mjs';

const e=(title,slug,date,description=title)=>({title,slug,description,createdAt:date,type:'html',url:`artifacts/${slug}/`});
test('latest and list are ordered by date, not input order',()=>{
 const html=renderHome({artifacts:[e('Old','old','2026-01-01'),e('Newest','newest','2026-09-28'),e('Middle','middle','2026-05-20')]});
 assert.ok(html.indexOf('LATEST OUTPUT') < html.indexOf('Newest'));
 assert.ok(html.indexOf('href="artifacts/newest/"') < html.indexOf('href="artifacts/old/"'));
});
test('registry escapes malicious descriptions as text',()=>{
 const html=renderHome({artifacts:[e('<script>alert(1)</script>','x','2026-09-28','<img src=x onerror=alert(1)>')]});
 assert.doesNotMatch(html,/<script>alert/);
 assert.doesNotMatch(html,/<img src=x/);
 assert.match(html,/&lt;script&gt;/);
});
test('no JavaScript still exposes each complete registry link',()=>{
 const html=renderHome({artifacts:[e('One','one','2026-01-01'),e('Two','two','2026-01-02')]});
 assert.match(html,/href="artifacts\/one\/"/);
 assert.match(html,/href="artifacts\/two\/"/);
});
