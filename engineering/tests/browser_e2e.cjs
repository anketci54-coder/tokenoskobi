// Optional real Chromium acceptance: npm install playwright; npx playwright install chromium.
// TOKENOSKOBI_PLAYWRIGHT_MODULE can point to an isolated Playwright installation.
const {chromium} = require(process.env.TOKENOSKOBI_PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const net = require('node:net');
const {spawn} = require('node:child_process');
const {once} = require('node:events');

async function main() {
  const repo = path.resolve(__dirname, '../..');
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 'tokenoskobi-browser-'));
  await fs.writeFile(path.join(root, 'price'), '100');
  const reservation = net.createServer();
  reservation.listen(0, '127.0.0.1');
  await once(reservation, 'listening');
  const port = reservation.address().port;
  await new Promise(resolve => reservation.close(resolve));
  const env = Object.fromEntries(Object.entries(process.env).filter(([k]) => !k.startsWith('TOKENOSKOBI_')));
  Object.assign(env, {PYTHONPATH: repo, PYTHONDONTWRITEBYTECODE: '1',
    TOKENOSKOBI_PRODUCT_SLICE_02_PORT: String(port),
    TOKENOSKOBI_SLICE03_STATE_DIR: path.join(root, 'state'),
    TOKENOSKOBI_GT_RATE_DIR: path.join(root, 'rate')});
  const processHandle = spawn(process.env.TOKENOSKOBI_PYTHON || 'python3',
    ['-B', '-m', 'engineering.tests.product_e2e', '--serve', root], {cwd: root, env});
  let logs = '', browser;
  processHandle.stderr.on('data', data => logs += data);
  processHandle.stdout.on('data', data => logs += data);
  const base = `http://127.0.0.1:${port}`;
  try {
    let ready = false;
    for (let attempt = 0; attempt < 100; attempt++) {
      if (processHandle.exitCode !== null) throw Error(logs);
      try {if ((await fetch(base + '/healthz')).ok) {ready = true; break;}} catch {}
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    assert(ready, 'Fixture server readiness timeout: ' + logs);
    browser = await chromium.launch({headless: true});
    const page = await browser.newPage({viewport: {width: 1280, height: 900}});
    const errors = [];
    page.on('pageerror', error => errors.push(String(error)));
    await page.goto(base);
    await page.waitForFunction(() => document.getElementById('connection').textContent.includes('hazır'));
    await page.locator('#a').fill('0x' + 'a'.repeat(40));
    await page.locator('#analyze').click();
    await page.waitForFunction(() => document.getElementById('status').textContent === 'Analiz tamamlandı.');
    await page.locator('#note').fill('Browser acceptance <script>unsafe()</script>');
    await page.locator('[data-action="ACCEPT"]').click();
    await page.waitForFunction(() => document.getElementById('status').textContent.includes('kararı kaydedildi'));
    await page.waitForFunction(() => !document.getElementById('analyze').disabled);
    assert((await page.locator('#history').innerText()).includes('<script>unsafe()</script>'));
    await fs.writeFile(path.join(root, 'price'), '110');
    await page.locator('#result [data-outcome]').click();
    await page.waitForFunction(() => document.getElementById('status').textContent.includes('Değişim: 10%'));
    await page.waitForFunction(() => !document.getElementById('analyze').disabled);
    const downloadEvent = page.waitForEvent('download');
    await page.locator('#download').click();
    const download = await downloadEvent;
    const downloadPath = path.join(root, 'packet.json');
    await download.saveAs(downloadPath);
    assert.equal(JSON.parse(await fs.readFile(downloadPath)).market.token.price_usd, 100);
    await page.reload();
    await page.locator('[data-reopen]').click();
    await page.waitForFunction(() => document.getElementById('status').textContent === 'Kayıtlı paket açıldı.');
    for (const width of [1280, 390, 320]) {
      await page.setViewportSize({width, height: 900});
      const overflow = await page.evaluate(() => [...document.querySelectorAll('body *')]
        .filter(el => el.getBoundingClientRect().right > window.innerWidth + 1)
        .map(el => el.tagName + '.' + el.className));
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), `Horizontal overflow at ${width}px: ${overflow}`);
      if (process.env.TOKENOSKOBI_SCREENSHOT_DIR) {
        await fs.mkdir(process.env.TOKENOSKOBI_SCREENSHOT_DIR, {recursive: true});
        await page.screenshot({path: path.join(process.env.TOKENOSKOBI_SCREENSHOT_DIR, `panel-${width}.png`), fullPage: true});
      }
    }
    assert.deepEqual(errors, []);
    console.log('Chromium PASS: analysis, decision, outcome, export, reload, escaped text, desktop/mobile (1280/390/320px)');
  } finally {
    if (browser) await browser.close();
    if (processHandle.exitCode === null) {
      const exited = once(processHandle, 'exit');
      processHandle.kill('SIGTERM');
      const timer = setTimeout(() => processHandle.kill('SIGKILL'), 5000);
      await exited;
      clearTimeout(timer);
    }
    await fs.rm(root, {recursive: true, force: true});
  }
}
main().catch(error => {console.error(error); process.exitCode = 1;});
