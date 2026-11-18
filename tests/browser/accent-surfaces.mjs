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
      // The system is monochrome, so the hazard is no longer "accent colour behind
      // muted text" — it is a filled ink surface whose own text fails contrast.
      const offending = await page.evaluate(() => {
        const parse = value => (value.match(/[\d.]+/g) || []).map(Number);
        const fill = parse(getComputedStyle(document.documentElement).getPropertyValue('--phosphor'));
        if (fill.length < 3) return [];
        const luminance = rgb => { const [r, g, b] = rgb.map(v => v / 255).map(v => v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4); return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
        const over = (fg, bg) => { const a = fg.length > 3 ? fg[3] : 1; return [0, 1, 2].map(i => fg[i] * a + bg[i] * (1 - a)); };
        const contrast = (fg, bg) => { const [hi, lo] = [luminance(fg), luminance(bg)].sort((x, y) => y - x); return (hi + 0.05) / (lo + 0.05); };
        return [...document.querySelectorAll('[data-artifact-content] *')].filter(el => {
          if (!el.textContent.trim() || !el.getClientRects().length) return false;
          const bg = parse(getComputedStyle(el).backgroundColor);
          if (bg.length < 3 || (bg.length === 4 && bg[3] === 0)) return false;
          if (over(bg, [255, 255, 255]).some((v, i) => Math.abs(v - fill[i]) > 2)) return false;
          return contrast(over(parse(getComputedStyle(el).color), bg), bg) < 4.5;
        }).slice(0, 6).map(el => `${el.tagName.toLowerCase()}.${String(el.className).replace(/\s+/g, '.').slice(0, 45)}: ${el.textContent.trim().slice(0, 28)}`);
      });
      if (offending.length) failures.push(`${theme} ${entry.slug}: ink-filled control with unreadable text → ${offending.join('; ')}`);
    }
  }
  await page.close();
} finally { await browser.close(); }
assert.deepEqual(failures, [], failures.join('\n'));
console.log(`Ink-filled surfaces: ${entries.length} artifacts in dark and paper themes pass`);
