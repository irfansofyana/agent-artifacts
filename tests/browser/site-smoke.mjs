import assert from 'node:assert/strict';
import { readFileSync,mkdirSync } from 'node:fs';
import { chromium } from 'playwright';
const entries=JSON.parse(readFileSync(new URL('../../artifacts.json',import.meta.url),'utf8')).artifacts;
const base=process.env.BASE_URL||'http://127.0.0.1:4173/';
const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH||'/usr/bin/google-chrome'});
const failures=[];
try{
 for(const width of [320,390,768,1280]){
  const page=await browser.newPage({viewport:{width,height:844}});
  const failed=[];
  page.on('response',response=>{if(response.url().startsWith(base)&&response.status()>=400)failed.push(`${response.status()} ${response.url()}`)});
  page.on('pageerror',error=>failed.push(error.message));
  for(const entry of entries){
   try{
    const response=await page.goto(new URL(entry.url,base).href,{waitUntil:'domcontentloaded'});
    assert.equal(response.status(),200);
    assert.equal(await page.locator('#site-main').count(),1);
    assert.equal(await page.locator('[data-theme-toggle]').count(),1);
    assert.equal(await page.locator('[data-artifact-content]').count(),1);
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),`${entry.slug}: overflow at ${width}px`);
    if(failed.length)throw new Error(failed.join('; '));
   }catch(e){failures.push(`${width}px ${entry.slug}: ${e.message}`)}
   failed.length=0;
  }
  await page.goto(base,{waitUntil:'domcontentloaded'});
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),`${width}px homepage overflow`);
  console.log(`PASS ${width}px: homepage + ${entries.length} artifacts`);
  await page.close();
 }
 const output=process.env.SCREENSHOT_DIR;
 if(output){
  mkdirSync(output,{recursive:true});
  for(const [name,url] of [['home',base],['artifact',new URL('artifacts/slack-bot-private-mcp-per-user/',base).href]]){
   for(const width of [390,1280]){
    const p=await browser.newPage({viewport:{width,height:844}});
    await p.goto(url,{waitUntil:'domcontentloaded'});
    await p.screenshot({path:`${output}/${name}-${width}-dark.png`});
    await p.getByRole('button',{name:/switch to paper/i}).click();
    await p.screenshot({path:`${output}/${name}-${width}-paper.png`});
    await p.close();
   }
  }
 }
}finally{await browser.close()}
assert.deepEqual(failures,[]);
