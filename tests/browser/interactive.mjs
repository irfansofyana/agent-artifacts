import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const base=process.env.BASE_URL || 'http://127.0.0.1:4173/';
const slugs=[
 ['ai-agent-git-worktrees','button'],['aws-ai-practitioner-journey','button'],['company-brain-technical-deep-dive','a'],['deep-agents-typescript-guide','a'],
 ['deepagents-use-case-atlas-2026','input[type="search"]'],['ecs-fargate-terraform-field-guide','button'],['firstmate-pi-herdr-gitlab-runbook','button'],
 ['forex-day-trading-starter','input[type="number"]'],['frontier-llm-prompt-field-guide-2026','button'],['graphify-daily-coding-field-guide','button'],
 ['langchain-agent-engineer-fieldbook','button'],['langgraph-learning-resources-2026','input[type="search"]'],['litellm-coding-agents','button'],
 ['mcp-evaluation-private-stack-2026','button'],['orca-ai-development-runbook','a']
];
const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH||'/usr/bin/google-chrome'});
const failures=[];
try{
 for(const [slug,selector] of slugs){
  const page=await browser.newPage({viewport:{width:390,height:844}});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  try{
   const response=await page.goto(`${base}artifacts/${slug}/`,{waitUntil:'domcontentloaded'});
   assert.equal(response.status(),200);
   assert.equal(await page.locator('[data-theme-toggle]').count(),1,'common theme button');
   assert.ok(await page.locator('.legacy-content').count(),'original article inside shared shell');
   assert.ok(await page.locator(`.legacy-content ${selector}`).count(),`original ${selector} controls preserved`);
   assert.ok(await page.locator('.legacy-content').innerText().then(s=>s.length)>300,'substantive content');
   assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'no mobile document overflow');
   if(slug==='deepagents-use-case-atlas-2026'||slug==='langgraph-learning-resources-2026'){
    await page.locator('.legacy-content #query').fill('zzzz-no-result-482');
    assert.equal(await page.locator('.legacy-content #empty').isVisible(),true,'search no-result state');
   }
   if(slug==='forex-day-trading-starter'){
    const before=await page.locator('.legacy-content #riskAmount').innerText();
    await page.locator('.legacy-content #balance').fill('10000000');
    assert.notEqual(await page.locator('.legacy-content #riskAmount').innerText(),before,'risk calculator updates');
   }
   if(slug==='litellm-coding-agents'){
    await page.locator('.legacy-content [data-tab="codex"]').click();
    assert.equal(await page.locator('.legacy-content [data-tab="codex"]').getAttribute('aria-selected'),'true','tabs activate');
   }
   await page.getByRole('button',{name:/switch to paper/i}).click();
   assert.equal(await page.locator('html').getAttribute('data-theme'),'paper');
   if(errors.length)throw new Error(errors.join('; '));
   console.log(`PASS ${slug}`);
  }catch(e){failures.push(`${slug}: ${e.message}`);console.error(`FAIL ${slug}: ${e.message}`)}
  finally{await page.close()}
 }
}finally{await browser.close()}
assert.deepEqual(failures,[]);
