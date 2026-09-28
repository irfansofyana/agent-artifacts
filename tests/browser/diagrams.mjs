import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const base=process.env.BASE_URL||'http://127.0.0.1:4173/';
const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH||'/usr/bin/google-chrome'});
try{
 const page=await browser.newPage({viewport:{width:390,height:844},hasTouch:true,isMobile:true});
 await page.goto(`${base}artifacts/slack-bot-private-mcp-per-user/`,{waitUntil:'networkidle'});
 const frame=page.frame({url:/diagrams\/architecture\.html/});
 assert.ok(frame,'real Archify iframe loaded');
 const canvas=frame.locator('.diagram-container');
 await canvas.scrollIntoViewIfNeeded();
 const max=await canvas.evaluate(e=>e.scrollWidth-e.clientWidth);
 assert.ok(max>200,`expected swipeable diagram width, got ${max}`);
 const rect=await canvas.boundingBox();const x=Math.min(rect.x+rect.width-25,360),y=Math.min(rect.y+80,800);
 const cdp=await page.context().newCDPSession(page);
 await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x,y}]});
 for(let i=1;i<=8;i++)await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:x-i*22,y}]});
 await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
 await page.waitForTimeout(200);
 assert.ok(await canvas.evaluate(e=>e.scrollLeft)>30,'real touch gesture pans the Archify canvas');
 for(const name of ['architecture','connect','call']){
  const link=page.locator(`a[href="diagrams/${name}.html"]`).first();
  assert.ok(await link.count(),`${name} full-size link`);
  const response=await page.request.get(new URL(await link.getAttribute('href'),page.url()).href);
  assert.equal(response.status(),200);
 }
 await page.close();
 for(const slug of ['company-brain-technical-deep-dive','deep-agents-typescript-guide']){
  const p=await browser.newPage({viewport:{width:390,height:844}});
  await p.goto(`${base}artifacts/${slug}/`,{waitUntil:'domcontentloaded'});
  assert.equal(await p.locator('[data-theme-toggle]').count(),1);
  const hasMermaid=await p.locator('.legacy-content .mermaid').count();
  assert.ok(hasMermaid || await p.locator('.legacy-content a[href*="diagram"]').count(),`${slug}: readable diagram source or link`);
  await p.close();
 }
 console.log('Archify touch pan/full-size and Mermaid source checks: pass');
}finally{await browser.close()}
