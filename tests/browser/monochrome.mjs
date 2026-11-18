import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { chromium } from 'playwright';

// Enforces the Scandinavian system on every published page, in both themes:
// no hue survives in interface chrome (colour is only allowed inside media and
// diagrams), no styled uppercase, and nothing overflows the viewport at 390px.
const entries = JSON.parse(readFileSync(new URL('../../artifacts.json', import.meta.url), 'utf8')).artifacts;
const base = process.env.BASE_URL || 'http://127.0.0.1:4173/';
const browser = await chromium.launch({ headless: true, executablePath: process.env.CHROME_PATH || '/usr/bin/google-chrome' });
const failures = [];

const audit = () => {
  // defined in-page: this function is serialised into the browser
  const MEDIA = 'iframe, svg, img, picture, video, canvas, .diagram, .diagram-frame';
  const parse = value => (value.match(/[\d.]+/g) || []).map(Number);
  const hueish = value => {
    if (!value || value === 'none') return false;
    const n = parse(value);
    if (n.length < 3) return false;
    if (n.length === 4 && n[3] === 0) return false;
    const [r, g, b] = n;
    const spread = Math.max(r, g, b) - Math.min(r, g, b);
    return spread > 12 && !(r > 244 && g > 244 && b > 244) && !(r < 14 && g < 14 && b < 14);
  };
  const props = ['color', 'backgroundColor', 'borderTopColor', 'borderRightColor', 'borderBottomColor', 'borderLeftColor', 'outlineColor', 'textDecorationColor'];
  const hues = new Set();
  let uppercase = 0;
  const uppercaseExamples = [];
  for (const el of document.querySelectorAll('body *')) {
    if (el.closest(MEDIA)) continue;
    const cs = getComputedStyle(el);
    if (cs.textTransform === 'uppercase' && el.textContent.trim()) {
      uppercase += 1;
      if (uppercaseExamples.length < 3) uppercaseExamples.push(`${el.tagName.toLowerCase()}.${String(el.className).slice(0, 30)}: ${el.textContent.trim().slice(0, 24)}`);
    }
    for (const prop of props) if (hueish(cs[prop])) hues.add(`${prop}: ${cs[prop]}`);
    if (cs.backgroundImage && cs.backgroundImage !== 'none') {
      for (const stop of cs.backgroundImage.match(/rgba?\([^)]+\)/g) || []) {
        if (hueish(stop)) { hues.add(`background-image: ${cs.backgroundImage.slice(0, 60)}`); break; }
      }
    }
  }
  return {
    hues: [...hues].slice(0, 5),
    uppercase,
    uppercaseExamples,
    overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
  };
};

try {
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  for (const theme of ['dark', 'paper']) {
    for (const entry of entries) {
      await page.goto(new URL(entry.url, base).href, { waitUntil: 'domcontentloaded' });
      await page.evaluate(t => { document.documentElement.dataset.theme = t; }, theme);
      const report = await page.evaluate(audit);
      if (report.hues.length) failures.push(`${theme} ${entry.slug}: hue in chrome → ${report.hues.join(' | ')}`);
      if (report.uppercase) failures.push(`${theme} ${entry.slug}: ${report.uppercase} uppercase element(s) → ${report.uppercaseExamples.join(' ; ')}`);
      if (report.overflow > 1) failures.push(`${theme} ${entry.slug}: ${report.overflow}px horizontal overflow`);
    }
  }
  await page.setViewportSize({ width: 390, height: 844 });
  for (const entry of entries) {
    await page.goto(new URL(entry.url, base).href, { waitUntil: 'domcontentloaded' });
    const report = await page.evaluate(audit);
    if (report.overflow > 1) failures.push(`390px ${entry.slug}: ${report.overflow}px horizontal overflow`);
  }
  await page.close();
} finally {
  await browser.close();
}
assert.deepEqual(failures, [], failures.join('\n'));
console.log(`Monochrome system: ${entries.length} artifacts in dark and paper themes, plus 390px, pass`);
