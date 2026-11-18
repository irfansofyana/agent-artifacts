// Render + accessibility verification for the Codex Security x GitLab page.
// Uses the repo's playwright against a local Chrome, over a loopback http.server.
//
//   node verify_render.mjs http://127.0.0.1:8765/index.html
//
// Reports, per width (1280x1000, 390x844) and per colour scheme (light, dark):
//   * document horizontal overflow (must be 0)
//   * elements whose computed colour/bg/border-colour channel spread > 12 and is
//     not near-white/near-black and not inside svg/iframe/img/.diagram (must be 0)
//   * elements with text-transform: uppercase (must be 0)
//   * composited contrast for body text, eyebrow/meta text and text on a filled surface
//   * console errors (must be empty) and document.fonts.check('16px "Inter Variable"')
import { chromium } from 'playwright';

const url = process.argv[2] || 'http://127.0.0.1:8765/index.html';
const CHROME = process.env.CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const VIEWPORTS = [
  { name: '1280x1000', width: 1280, height: 1000 },
  { name: '390x844', width: 390, height: 844 },
];
const SCHEMES = ['light', 'dark'];

const PROBE = () => {
  const parse = (s) => {
    const m = String(s).match(/rgba?\(([^)]+)\)/);
    if (!m) return null;
    const p = m[1].split(/[ ,/]+/).map(Number);
    return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 };
  };
  const over = (fg, bg) => ({ r: fg.r * fg.a + bg.r * (1 - fg.a), g: fg.g * fg.a + bg.g * (1 - fg.a), b: fg.b * fg.a + bg.b * (1 - fg.a), a: 1 });
  const lin = (c) => { c /= 255; return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); };
  const lum = (c) => 0.2126 * lin(c.r) + 0.7152 * lin(c.g) + 0.0722 * lin(c.b);
  const ratio = (a, b) => { const L = [lum(a), lum(b)].sort((x, y) => y - x); return (L[0] + 0.05) / (L[1] + 0.05); };

  const canvasBase = document.documentElement.matches(':root') ? (getComputedStyle(document.body).backgroundColor) : 'rgb(255,255,255)';
  const base = parse(canvasBase) || { r: 255, g: 255, b: 255, a: 1 };

  const effBg = (el) => {
    const chain = [];
    for (let n = el; n; n = n.parentElement) chain.push(n);
    chain.reverse();
    let acc = null;
    for (const n of chain) {
      const bg = parse(getComputedStyle(n).backgroundColor);
      if (!bg || bg.a === 0) continue;
      acc = acc ? over(bg, acc) : bg;
    }
    if (!acc || acc.a < 1) acc = over(acc || { r: 0, g: 0, b: 0, a: 0 }, base);
    return acc;
  };
  const textContrast = (el) => {
    const bg = effBg(el);
    const fg = over(parse(getComputedStyle(el).color), bg);
    return { ratio: ratio(fg, bg), bg, fg };
  };

  // ---- horizontal overflow
  const html = document.documentElement;
  const overflow = Math.max(html.scrollWidth, document.body.scrollWidth) - html.clientWidth;

  // ---- tinted-neutral sweep
  const nearNeutral = (c) => Math.max(c.r, c.g, c.b) - Math.min(c.r, c.g, c.b) <= 12;
  const nearWhiteOrBlack = (c) => Math.min(c.r, c.g, c.b) >= 240 || Math.max(c.r, c.g, c.b) <= 15;
  const spread = (c) => Math.max(c.r, c.g, c.b) - Math.min(c.r, c.g, c.b);
  const tinted = [];
  const upper = [];
  const all = document.querySelectorAll('*');
  for (const el of all) {
    const cs = getComputedStyle(el);
    if (cs.textTransform === 'uppercase') {
      upper.push(el.tagName + '.' + (el.className || '') + ' :: ' + (el.textContent || '').slice(0, 40));
    }
    if (el.closest('svg, iframe, img, .diagram')) continue;
    const props = ['color', 'backgroundColor', 'borderTopColor', 'borderRightColor', 'borderBottomColor', 'borderLeftColor'];
    for (const p of props) {
      const c = parse(cs[p]);
      if (!c || c.a === 0) continue;
      if (spread(c) > 12 && !nearWhiteOrBlack(c)) {
        tinted.push(p + '=' + cs[p] + ' on ' + el.tagName + '.' + (el.className || ''));
      }
    }
  }

  // ---- contrast probes
  const probe = (sel, label) => {
    const el = document.querySelector(sel);
    if (!el) return null;
    const r = textContrast(el);
    return { label, selector: sel, ratio: Math.round(r.ratio * 100) / 100, color: getComputedStyle(el).color, background: `rgb(${Math.round(r.bg.r)},${Math.round(r.bg.g)},${Math.round(r.bg.b)})` };
  };
  const probes = [
    probe('.chapters p', 'body text'),
    probe('.eyebrow', 'eyebrow'),
    probe('.lede', 'lede'),
    probe('.muted', 'meta (muted)'),
    probe('figcaption', 'metadata (caption)'),
    probe('footer.foot p', 'footer text'),
    probe('thead th', 'text on filled surface (table head)'),
    probe('pre code', 'code on filled surface (pre)'),
    probe(':not(pre) > code', 'inline code on filled surface'),
  ].filter(Boolean);

  return {
    overflow,
    tinted,
    upper,
    probes,
    fontsInter: document.fonts.check('16px "Inter Variable"'),
  };
};

const out = { url, results: [] };
const browser = await chromium.launch({ executablePath: CHROME, headless: true });
for (const vp of VIEWPORTS) {
  for (const scheme of SCHEMES) {
    const ctx = await browser.newContext({ viewport: { width: vp.width, height: vp.height }, colorScheme: scheme });
    const page = await ctx.newPage();
    const errors = [];
    page.on('console', (m) => { if (m.type() === 'error') errors.push('console: ' + m.text()); });
    page.on('pageerror', (e) => errors.push('pageerror: ' + e.message));
    await page.goto(url, { waitUntil: 'load' });
    await page.evaluate(() => document.fonts.ready);
    const data = await page.evaluate(PROBE);
    out.results.push({
      viewport: vp.name,
      scheme,
      overflow: data.overflow,
      tintedCount: data.tinted.length,
      tintedSamples: data.tinted.slice(0, 8),
      upperCount: data.upper.length,
      upperSamples: data.upper.slice(0, 8),
      fontsInter: data.fontsInter,
      consoleErrors: errors,
      probes: data.probes,
    });
    await ctx.close();
  }
}
await browser.close();
console.log(JSON.stringify(out, null, 2));
