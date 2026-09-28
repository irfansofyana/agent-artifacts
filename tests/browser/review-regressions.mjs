import assert from 'node:assert/strict';
import {chromium} from 'playwright';
const base=process.env.BASE_URL||'http://127.0.0.1:4173/';
const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH||'/usr/bin/google-chrome'});
try{
 for(const slug of ['deep-agents-typescript-guide','ecs-fargate-terraform-field-guide']){
  const page=await browser.newPage({viewport:{width:390,height:844}});
  await page.goto(new URL(`artifacts/${slug}/`,base).href);
  const detail=await page.evaluate(()=>{const body=document.querySelector('.artifact-body').getBoundingClientRect();const inner=document.querySelector('.legacy-content main').getBoundingClientRect();return {bodyRight:body.right,innerRight:inner.right}});
  assert.ok(detail.innerRight<=detail.bodyRight+1,`${slug}: main content clipped: ${JSON.stringify(detail)}`);
  if(slug==='ecs-fargate-terraform-field-guide'){
   await page.getByRole('button',{name:/switch to paper/i}).click();
   const gradient=await page.locator('.legacy-content .card').first().evaluate(el=>getComputedStyle(el).backgroundImage);
   assert.doesNotMatch(gradient,/rgb\(16, 24, 33\)/,`paper mode contains dark gradient: ${gradient}`);
  }
  await page.close();
 }
 for(const slug of ['ecs-fargate-terraform-field-guide','mcp-evaluation-private-stack-2026']){
  const p=await browser.newPage();await p.goto(new URL(`artifacts/${slug}/`,base).href);
  assert.ok(await p.locator('.article-toc a, .mobile-toc a').count()>0,`${slug}: section navigation missing`);
  await p.close();
 }
 console.log('Review regressions pass');
}finally{await browser.close()}
