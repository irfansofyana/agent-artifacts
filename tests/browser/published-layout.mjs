import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {chromium} from 'playwright';

const entries = JSON.parse(readFileSync(new URL('../../artifacts.json', import.meta.url), 'utf8')).artifacts;
const base = process.env.BASE_URL || 'http://127.0.0.1:4173/';
const browser = await chromium.launch({headless: true, executablePath: process.env.CHROME_PATH || '/usr/bin/google-chrome'});
const failures = [];
try {
  for (const width of [320, 390, 768, 1280]) {
    const page = await browser.newPage({viewport: {width, height: 844}});
    for (const entry of entries) {
      await page.goto(new URL(entry.url, base).href, {waitUntil: 'domcontentloaded'});
      const geometry = await page.evaluate(() => {
        const el = selector => document.querySelector(selector);
        const size = selector => el(selector)?.getBoundingClientRect().width ?? 0;
        const article = el('.article-layout');
        const inner = el('.legacy-content main');
        return {
          hasToc: !!el('.article-toc'), layout: size('.article-layout'), body: size('.artifact-body'),
          inner: inner && getComputedStyle(inner).display !== 'none' ? inner.getBoundingClientRect().width : 0,
          legacy: size('.legacy-content'),
          scrollWidth: el('.window-scroll').scrollWidth,
          clientWidth: el('.window-scroll').clientWidth,
          articleWidth: article?.getBoundingClientRect().width,
          narrowCells: [...document.querySelectorAll('.artifact-body table th,.artifact-body table td')]
            .filter(cell => cell.checkVisibility() && cell.textContent.trim().length > 8 && cell.getBoundingClientRect().width < 145)
            .slice(0, 3).map(cell => `${Math.round(cell.getBoundingClientRect().width)}px ${cell.textContent.trim().slice(0, 24)}`),
          textSize: parseFloat(getComputedStyle(el('.legacy-content')).fontSize),
          tableTextSize: el('.legacy-content table') ? parseFloat(getComputedStyle(el('.legacy-content table')).fontSize) : 0,
          duplicateRail: el('.legacy-content .rail')?.checkVisibility() ?? false,
          duplicateGridNav: el('.legacy-content .grid > nav')?.checkVisibility() ?? false,
          modelStepWidth: el('.legacy-content .model .step')?.getBoundingClientRect().width ?? 0,
        };
      });
      if (entry.slug === 'graphify-daily-coding-field-guide' && geometry.modelStepWidth && geometry.modelStepWidth < 150)
        failures.push(`${width}px ${entry.slug}: seven-step model columns are ${geometry.modelStepWidth}px`);
      if (entry.slug === 'orca-ai-development-runbook' && geometry.duplicateRail)
        failures.push(`${width}px ${entry.slug}: internal rail duplicates shared TOC`);
      if (entry.slug === 'headroom-how-it-works' && geometry.duplicateGridNav)
        failures.push(`${width}px ${entry.slug}: internal grid nav duplicates shared TOC`);
      if (width >= 768 && !geometry.hasToc && geometry.body < geometry.layout * .7)
        failures.push(`${width}px ${entry.slug}: no TOC but body is ${geometry.body}px in ${geometry.layout}px layout`);
      if (width >= 768 && geometry.inner && geometry.inner < geometry.legacy * .65)
        failures.push(`${width}px ${entry.slug}: legacy main is ${geometry.inner}px in ${geometry.legacy}px body`);
      if (entry.slug === 'matt-pocock-skills-ai-assisted-engineering-playbook' && (geometry.textSize < 15 || geometry.tableTextSize < 13))
        failures.push(`${width}px ${entry.slug}: typography too small (${geometry.textSize}px body, ${geometry.tableTextSize}px table)`);
      if (width <= 390 && geometry.narrowCells.length)
        failures.push(`${width}px ${entry.slug}: table cells too narrow: ${geometry.narrowCells.join('; ')}`);
      if (geometry.scrollWidth > geometry.clientWidth + 1)
        failures.push(`${width}px ${entry.slug}: page scroller overflows ${geometry.scrollWidth}/${geometry.clientWidth}`);
    }
    await page.close();
  }
} finally { await browser.close(); }
assert.deepEqual(failures, [], failures.join('\n'));
console.log(`Published layout: ${entries.length} artifacts at desktop, tablet and phone widths pass`);
