import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const base = process.env.BASE_URL || 'http://127.0.0.1:4173/';
const browser = await chromium.launch({headless: true, executablePath: process.env.CHROME_PATH || '/usr/bin/google-chrome'});

function luminance(rgb) {
  const channels = rgb.match(/[\d.]+/g).slice(0, 3).map(Number).map(value => {
    const s = value / 255;
    return s <= 0.04045 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
  });
  return channels[0] * 0.2126 + channels[1] * 0.7152 + channels[2] * 0.0722;
}
function contrast(a, b) {
  const [lighter, darker] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (lighter + 0.05) / (darker + 0.05);
}

try {
  for (const theme of ['dark', 'paper']) {
    const page = await browser.newPage({viewport: {width: 390, height: 844}});
    await page.goto(new URL('artifacts/company-brain-technical-deep-dive/', base).href);
    if (theme === 'paper') await page.getByRole('button', {name: /switch to paper/i}).click();
    const colors = await page.locator('.legacy-content pre.flow').evaluate(el => {
      const style = getComputedStyle(el);
      return {foreground: style.color, background: style.backgroundColor};
    });
    assert.ok(contrast(colors.foreground, colors.background) >= 4.5, `${theme} flow text contrast: ${JSON.stringify(colors)}`);
    await page.close();
  }

  for (const theme of ['dark', 'paper']) {
    const page = await browser.newPage({viewport: {width: 390, height: 844}});
    await page.goto(new URL('artifacts/deep-agents-typescript-guide/', base).href);
    if (theme === 'paper') await page.getByRole('button', {name: /switch to paper/i}).click();
    const colors = await page.locator('.legacy-content td code').first().evaluate(el => {
      const style = getComputedStyle(el);
      return {foreground: style.color, background: style.backgroundColor};
    });
    assert.ok(contrast(colors.foreground, colors.background) >= 4.5, `${theme} inline code contrast: ${JSON.stringify(colors)}`);
    await page.close();
  }

  for (const width of [320, 390]) {
    const page = await browser.newPage({viewport: {width, height: 700}});
    await page.goto(new URL('artifacts/deep-agents-typescript-guide/', base).href);
    const table = page.locator('.legacy-content .tw table').filter({hasText: 'LangGraph'}).first();
    const wrapper = table.locator('xpath=..');
    assert.equal(await wrapper.getAttribute('tabindex'), '0', 'wide table must be keyboard-scrollable');
    assert.match(await wrapper.getAttribute('aria-label') || '', /scroll horizontally/i);
    assert.match(await page.locator('.legacy-content .table-scroll-hint').first().textContent(), /swipe/i);
    const geometry = await table.evaluate(el => {
      const wrapper = el.closest('.tw');
      const first = el.querySelector('tbody td');
      return {
        documentWidth: document.documentElement.scrollWidth,
        viewportWidth: document.documentElement.clientWidth,
        wrapperWidth: wrapper.clientWidth,
        wrapperScrollWidth: wrapper.scrollWidth,
        firstCellWidth: first.getBoundingClientRect().width,
      };
    });
    assert.ok(geometry.documentWidth <= geometry.viewportWidth + 1, `${width}px document overflows: ${JSON.stringify(geometry)}`);
    assert.ok(geometry.wrapperScrollWidth > geometry.wrapperWidth + 100, `${width}px table should scroll within its wrapper: ${JSON.stringify(geometry)}`);
    assert.ok(geometry.firstCellWidth >= 95, `${width}px Layer column wraps into vertical letters: ${JSON.stringify(geometry)}`);
    await page.close();
  }
  console.log('Mobile content contrast and table layout pass');
} finally {
  await browser.close();
}
