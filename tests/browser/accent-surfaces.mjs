import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {chromium} from 'playwright';

const entries = JSON.parse(readFileSync(new URL('../../artifacts.json', import.meta.url), 'utf8')).artifacts;
const base = process.env.BASE_URL || 'http://127.0.0.1:4173/';
const browser = await chromium.launch({headless: true, executablePath: process.env.CHROME_PATH || '/usr/bin/google-chrome'});
const failures = [];
try {
  const page = await browser.newPage({viewport: {width: 1280, height: 844}});
  for (const theme of ['dark', 'paper']) {
    for (const entry of entries) {
      await page.goto(new URL(entry.url, base).href, {waitUntil: 'domcontentloaded'});
      await page.evaluate(theme => { document.documentElement.dataset.theme = theme; }, theme);
      const offending = await page.evaluate(() => {
        const accent = getComputedStyle(document.documentElement).getPropertyValue('--phosphor').trim().toLowerCase();
        const rgb = accent.match(/[a-f\d]{2}/gi).map(v => parseInt(v, 16));
        const forbidden = `rgb(${rgb.join(', ')})`;
        return [...document.querySelectorAll('[data-artifact-content] *')].filter(el => {
          if (!el.textContent.trim() || !el.getClientRects().length) return false;
          return getComputedStyle(el).backgroundColor === forbidden;
        }).slice(0, 6).map(el => `${el.tagName.toLowerCase()}.${String(el.className).replace(/\s+/g, '.').slice(0, 45)}: ${el.textContent.trim().slice(0, 28)}`);
      });
      if (offending.length) failures.push(`${theme} ${entry.slug}: ${offending.join('; ')}`);
    }
  }
  await page.close();
} finally { await browser.close(); }
assert.deepEqual(failures, [], failures.join('\n'));
console.log(`Accent surfaces: ${entries.length} artifacts in dark and paper themes pass`);
