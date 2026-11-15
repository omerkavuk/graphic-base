#!/usr/bin/env node
// Renders design.html with headless Chrome: one image per view, PDFs for print views, thumbnails for the one-second
// read, and the audit make.py checks (text sizes, edges, overlaps, fonts, image resolution, contrast). Zero npm
// dependencies (Node 22+). make.py calls it; call it by hand only for a step make.py does not cover.
//
//   node tools/render.mjs --url design.html --out renders/draft-v1 [--views post,story] [--scale 1] [--format png|jpeg]
//                         [--pdf] [--thumb 160] [--report renders/draft-v1/report.json] [--no-contrast]
//   node tools/render.mjs --page review/sheet.html --shot review/sheet-v1.jpg --width 1600   # any page, full height
//
// --scale: device pixels per CSS pixel. Screen views are authored at their real pixel size, so 1 gives the true file;
//          print views are authored in mm, so make.py passes dpi / 96 (300 dpi = 3.125).
// --pdf:   print views (unit mm) also go out as a vector PDF at trim + bleed, fonts embedded.
// Env: CHROME_PATH overrides browser discovery.

import { spawn } from 'node:child_process';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve, dirname } from 'node:path';
import { pathToFileURL } from 'node:url';

const args = parseArgs(process.argv.slice(2));
if (args.help || args.h || (!args.url && !args.page)) {
  console.log('usage: node render.mjs --url design.html --out <dir> [--views a,b] [--scale 1] [--format png|jpeg] [--pdf] [--thumb 160] [--report file.json] [--no-contrast]\n'
    + '       node render.mjs --page sheet.html --shot out.jpg [--width 1600]');
  process.exit(args.help || args.h ? 0 : 2);
}

const chrome = findChrome();
const browser = await launch(chrome);
let exitCode = 0;
try {
  if (args.page) await shotPage(browser, args.page, args.shot, +(args.width || 1600), !!args.full);
  else if (args.info) {                                   // the DESIGN block's views as JSON, read by the page itself
    const p = await browser.open(buildUrl(args.url, {}));
    const info = await p.ready();
    const views = await p.eval('DESIGN.views');
    console.log(JSON.stringify(views.map((v) => ({ ...v, pages: (info.pageCount || {})[v.id] || 1 }))));
    await p.close();
  } else await renderDesign(browser);
} catch (e) {
  console.error(`render: ${e.message}`);
  exitCode = 1;
} finally {
  await browser.close();
}
process.exit(exitCode);

async function renderDesign(b) {
  const out = args.out || 'renders/out';
  mkdirSync(out, { recursive: true });
  const scale = +(args.scale || 1);
  const fmt = args.format === 'jpeg' ? 'jpeg' : 'png';
  const first = await b.open(buildUrl(args.url, {}));
  const info = await first.ready();
  const ids = args.views && args.views !== 'all' ? String(args.views).split(',') : info.views;
  const report = { url: args.url, scale, views: [] };
  for (const id of ids) {
    const n = (info.pageCount || {})[id] || 1;
    const pages = args.pages ? String(args.pages).split(',').map(Number).filter((x) => x >= 1 && x <= n) : [...Array(n).keys()].map((x) => x + 1);
    let firstOfView = null, unit = 'px';
    for (const pg of pages) {
      const t0 = Date.now();
      const tag = n > 1 ? `${id}-p${String(pg).padStart(2, '0')}` : id;
      const extra = args.params ? Object.fromEntries(new URLSearchParams(String(args.params))) : {};
      const page = await b.open(buildUrl(args.url, { ...extra, view: id, page: pg, ...(args.wire ? { wire: 1 } : {}) }));
      const v = await page.ready();
      unit = v.unit;
      await page.send('Emulation.setDeviceMetricsOverride', { width: v.width, height: v.height, deviceScaleFactor: scale, mobile: false });
      await page.eval('document.fonts.ready.then(() => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r))))');
      const shot = await page.send('Page.captureScreenshot', { format: fmt, quality: fmt === 'jpeg' ? 92 : undefined, captureBeyondViewport: false,
        clip: { x: 0, y: 0, width: v.width, height: v.height, scale: 1 } });
      const file = join(out, `${tag}.${fmt === 'jpeg' ? 'jpg' : 'png'}`);
      writeFileSync(file, Buffer.from(shot.data, 'base64'));
      const a = await page.eval('GB.audit()');
      a.file = file;
      a.tag = tag;
      a.pixels = [Math.round(v.width * scale), Math.round(v.height * scale)];
      if (args.thumb) {
        const k = +args.thumb / Math.max(v.width, v.height);
        const th = await page.send('Page.captureScreenshot', { format: 'jpeg', quality: 85, clip: { x: 0, y: 0, width: v.width, height: v.height, scale: k / scale } });
        a.thumb = join(out, `${tag}-thumb.jpg`);
        writeFileSync(a.thumb, Buffer.from(th.data, 'base64'));
      }
      if (!args['no-contrast'] && !args.wire) {
        for (const t of a.texts) {
          if (t.box.w < 2 || t.box.h < 2 || t.offEdge) continue;
          const pad = 2;
          const clip = { x: Math.max(0, t.box.x - pad), y: Math.max(0, t.box.y - pad), width: Math.min(v.width, t.box.w + 2 * pad), height: Math.min(v.height, t.box.h + 2 * pad), scale: Math.max(1, 2 / scale) };   // never downsampled: resampling invents edge colours
          try {
            const c = await page.send('Page.captureScreenshot', { format: 'png', clip });
            t.contrast = await page.eval(`GB.contrastOf(${JSON.stringify('data:image/png;base64,' + c.data)}, ${JSON.stringify(t.color)})`);
          } catch { t.contrast = null; }
        }
      }
      a.ms = Date.now() - t0;
      a.errors = page.errors();
      report.views.push(a);
      firstOfView = firstOfView || a;
      console.log(`[render] ${tag} ${a.pixels.join('x')} -> ${file} (${a.ms} ms)`);
      await page.close();
    }
    // one PDF per view, every page in it: print views always, screen views with more than one page (a carousel)
    if (args.pdf && firstOfView && (unit === 'mm' || n > 1) && !args.wire) {
      for (const marks of args.marks && unit === 'mm' ? [false, true] : [false]) {
        const pp = await b.open(buildUrl(args.url, { view: id, print: 1, ...(marks ? { marks: 1 } : {}) }));
        await pp.ready();
        const g = await pp.eval(`GB.pageMM(${JSON.stringify(id)}, ${marks})`);
        const pdf = await pp.send('Page.printToPDF', { paperWidth: g.w / 25.4, paperHeight: g.h / 25.4, marginTop: 0, marginBottom: 0,
          marginLeft: 0, marginRight: 0, printBackground: true, preferCSSPageSize: true, scale: 1 });
        const f = join(out, `${id}${marks ? '-marks' : ''}.pdf`);
        writeFileSync(f, Buffer.from(pdf.data, 'base64'));
        if (marks) { firstOfView.pdfMarks = f; firstOfView.sheet = g; } else firstOfView.pdf = f;
        console.log(`[render] ${id} -> ${f} (${n} page${n > 1 ? 's' : ''})`);
        await pp.close();
      }
    }
  }
  await first.close();
  const rp = args.report || join(out, 'report.json');
  writeFileSync(rp, JSON.stringify(report, null, 1));
  console.log(`[render] report -> ${rp}`);
}

async function shotPage(b, url, outFile, width, full = false) {
  const params = args.params ? Object.fromEntries(new URLSearchParams(String(args.params))) : {};
  const page = await b.open(buildUrl(url, params), false);
  await page.send('Emulation.setDeviceMetricsOverride', { width, height: 800, deviceScaleFactor: 1, mobile: false });
  // a page that builds itself (body data-wait) says when it is done with data-ready="1"
  await page.eval(`new Promise((r) => { const t = Date.now(); (function c() { const b = document.body;
    if (!b || !b.hasAttribute('data-wait') || b.dataset.ready === '1' || Date.now() - t > 20000) r(); else setTimeout(c, 100); })(); })`, 30000);
  await page.eval('Promise.all([...document.images].map((i) => i.decode().catch(() => null))).then(() => document.fonts.ready)');
  const h = await page.eval('Math.ceil(document.body.getBoundingClientRect().bottom + parseFloat(getComputedStyle(document.body).marginBottom || 0))');   // the content, not the 800 px window
  await page.send('Emulation.setDeviceMetricsOverride', { width, height: h, deviceScaleFactor: 1, mobile: false });
  // sheets stay under 1.1 megapixels, so they can be read in the chat (the guard refuses larger images)
  const k = full ? 1 : Math.min(1, Math.sqrt(1.1e6 / (width * h)));   // --full: the style board, sent to the user at its real size
  const s = await page.send('Page.captureScreenshot', { format: 'jpeg', quality: 85, clip: { x: 0, y: 0, width, height: h, scale: k } });
  mkdirSync(dirname(resolve(outFile)), { recursive: true });
  writeFileSync(outFile, Buffer.from(s.data, 'base64'));
  console.log(`[render] sheet ${width}x${h} -> ${outFile}`);
  await page.close();
}

// ---- Chrome over the DevTools protocol ----
async function launch(chromePath) {
  const profile = mkdtempSync(join(tmpdir(), `graphic-base-chrome-${process.pid}-`));
  const flags = ['--headless=new', '--remote-debugging-port=0', `--user-data-dir=${profile}`, '--no-first-run',
    '--no-default-browser-check', '--disable-extensions', '--mute-audio', '--hide-scrollbars', '--use-mock-keychain',
    '--password-store=basic', '--allow-file-access-from-files', '--force-color-profile=srgb', '--font-render-hinting=none',
    'about:blank'];
  const proc = spawn(chromePath, flags, { stdio: ['ignore', 'ignore', 'pipe'] });
  let stderr = '';
  proc.stderr.on('data', (d) => { stderr = (stderr + d).slice(-4000); });
  const portFile = join(profile, 'DevToolsActivePort');
  const deadline = Date.now() + 20000;
  let port;
  while (!port) {
    if (Date.now() > deadline || proc.exitCode !== null) throw new Error(`Chrome did not start.\n${stderr}`);
    try { port = readFileSync(portFile, 'utf8').split('\n')[0].trim(); } catch { /* not yet */ }
    if (!port) await sleep(50);
  }
  const base = `http://127.0.0.1:${port}`;
  return {
    async open(url, needReady = true) {
      let target;
      for (let i = 0; i < 40 && !target; i++) {
        try { target = await (await fetch(`${base}/json/new?${encodeURI('about:blank')}`, { method: 'PUT' })).json(); } catch { await sleep(100); }
      }
      if (!target) throw new Error('could not open a tab');
      const ws = new WebSocket(target.webSocketDebuggerUrl);
      await new Promise((ok, fail) => { ws.onopen = ok; ws.onerror = () => fail(new Error('DevTools socket failed')); });
      let id = 0;
      const pending = new Map(), errors = [];
      ws.onmessage = (m) => {
        const msg = JSON.parse(typeof m.data === 'string' ? m.data : m.data.toString());
        if (msg.id && pending.has(msg.id)) {
          const { ok, fail } = pending.get(msg.id); pending.delete(msg.id);
          msg.error ? fail(new Error(msg.error.message)) : ok(msg.result);
        } else if (msg.method === 'Runtime.exceptionThrown') {
          errors.push(msg.params.exceptionDetails.exception?.description ?? msg.params.exceptionDetails.text);
        } else if (msg.method === 'Runtime.consoleAPICalled' && msg.params.type === 'error') {
          errors.push(msg.params.args.map((a) => a.value ?? a.description).join(' '));
        }
      };
      const send = (method, params = {}) => new Promise((ok, fail) => {
        const i = ++id; pending.set(i, { ok, fail }); ws.send(JSON.stringify({ id: i, method, params }));
      });
      await send('Runtime.enable');
      await send('Page.enable');
      await send('Page.navigate', { url });
      for (let i = 0; i < 300; i++) {
        const r = await send('Runtime.evaluate', { expression: 'document.readyState', returnByValue: true });
        if (r.result?.value === 'complete') break;
        await sleep(50);
      }
      const evalJs = async (expression, ms = 120000) => {
        const r = await Promise.race([send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true }),
          sleep(ms).then(() => { throw new Error(`the page gave no answer in ${ms / 1000} s`); })]);
        if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description ?? r.exceptionDetails.text);
        return r.result.value;
      };
      return {
        send, eval: evalJs, errors: () => [...new Set(errors)],
        async ready() {
          if (!needReady) return null;
          const has = await evalJs('typeof window.READY !== "undefined"');
          if (!has) throw new Error(`the page has no window.READY: is it a design.html from the kit?\n${errors.join('\n')}`);
          try { return await evalJs('window.READY'); } catch (e) { throw new Error(`${e.message}${errors.length ? '\n' + [...new Set(errors)].join('\n') : ''}`); }
        },
        async close() { try { ws.close(); } catch { /* ignore */ } try { await fetch(`${base}/json/close/${target.id}`); } catch { /* ignore */ } },
      };
    },
    async close() {
      proc.kill();
      await sleep(300);
      try { rmSync(profile, { recursive: true, force: true }); } catch { /* temp profile */ }
    },
  };
}

function findChrome() {
  if (process.env.CHROME_PATH) return process.env.CHROME_PATH;
  const c = {
    darwin: ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '/Applications/Chromium.app/Contents/MacOS/Chromium',
      '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge'],
    linux: ['/usr/bin/google-chrome', '/usr/bin/google-chrome-stable', '/usr/bin/chromium', '/usr/bin/chromium-browser', '/snap/bin/chromium'],
    win32: ['C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', 'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
      ...(process.env.LOCALAPPDATA ? [join(process.env.LOCALAPPDATA, 'Google', 'Chrome', 'Application', 'chrome.exe')] : []),
      'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe', 'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe'],
  }[process.platform] ?? [];
  const found = c.find((p) => existsSync(p));
  if (!found) { console.error('render: no Chrome, Chromium or Edge found; set CHROME_PATH'); process.exit(2); }
  return found;
}

function buildUrl(u, params) {
  const url = /^[a-z]+:\/\//i.test(u) ? new URL(u) : pathToFileURL(resolve(u));
  if (u === args.url) url.searchParams.set('capture', '1');
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, String(v));
  return url.href;
}

function parseArgs(argv) {
  const o = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (!a.startsWith('--')) continue;
    const key = a.slice(2), next = argv[i + 1];
    if (next === undefined || next.startsWith('--')) o[key] = true; else { o[key] = next; i++; }
  }
  return o;
}
function sleep(ms) { return new Promise((r) => setTimeout(r, ms)); }
