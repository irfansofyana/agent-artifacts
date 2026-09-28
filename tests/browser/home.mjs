import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH || '/usr/bin/google-chrome'});
const page=await browser.newPage({viewport:{width:390,height:844}});
const errors=[];page.on('pageerror',e=>errors.push(e.message));
try{
 await page.goto(process.env.BASE_URL || 'http://127.0.0.1:4173/',{waitUntil:'networkidle'});
 assert.equal(await page.locator('[data-artifact-row]').count(),33);
 await page.getByRole('searchbox').fill('company brain');
 assert.equal(await page.locator('[data-artifact-row]').count(),1);
 assert.match(await page.locator('[data-artifact-row]').first().textContent(),/Company Brain/i);
 await page.getByRole('searchbox').fill('zzzzz-no-results');
 assert.equal(await page.locator('[data-artifact-row]:visible').count(),0);
 assert.equal(await page.locator('#empty-state').isVisible(),true);
 await page.getByRole('button',{name:/clear search/i}).click();
 assert.equal(await page.locator('[data-artifact-row]:visible').count(),33);
 await page.getByRole('combobox',{name:/sort/i}).selectOption('title');
 assert.match(await page.locator('[data-artifact-row]').first().textContent(),/Agent Engineer Fieldbook/i);
 await page.getByRole('button',{name:/switch to paper/i}).click();
 assert.equal(await page.locator('html').getAttribute('data-theme'),'paper');
 await page.reload({waitUntil:'networkidle'});
 assert.equal(await page.locator('html').getAttribute('data-theme'),'paper');
 assert.deepEqual(errors,[]);
 console.log('Home search/sort/theme: pass');
}finally{await browser.close()}
