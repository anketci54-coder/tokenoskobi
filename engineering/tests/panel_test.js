// Execute the served JavaScript, including its renderer, without provider calls.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const html = fs.readFileSync(0, 'utf8');
const nodes = new Map();
const document = {
  getElementById(id) {
    if (!nodes.has(id)) nodes.set(id, {innerHTML: '', textContent: '', value: '',
      hidden: false, disabled: false, addEventListener() {}, querySelectorAll() {return [];}});
    return nodes.get(id);
  },
  querySelectorAll() {return [];},
};
const context = vm.createContext({document, console, Intl, setTimeout, clearTimeout,
  window: {scrollTo() {}}, URL, Blob,
  fetch: async () => ({ok: true, headers: {get: () => 'application/json'},
    json: async () => ({ok: true, product_slice: '03', records: []})}),
});
for (const match of html.matchAll(/<script>([\s\S]*?)<\/script>/g)) {
  vm.runInContext(match[1], context);
}
assert.equal(vm.runInContext('price(null)', context), 'VERİ YETERSİZ');
assert.equal(vm.runInContext('price(0)', context), '0');
vm.runInContext(`renderAnalysis({
  token_address: '0x' + 'a'.repeat(40),
  contract: {metadata: {symbol: '<img src=x onerror=alert(1)>'}},
  market: {token: {price_usd: null}, selected_pool: {}},
  decision: {decision: 'BLOCK', risk_score: 100, data_quality: 'VERI_YETERSIZ',
    blockers: ['TARGET_ASSET_ORIENTATION_UNVERIFIED'], warnings: [], evidence: []},
  technical_timeframes: {}, news: {}, history: {packet_id: 'b'.repeat(64)}
})`, context);
const rendered = nodes.get('result').innerHTML;
assert.match(rendered, /TARGET_ASSET_ORIENTATION_UNVERIFIED/);
assert.match(rendered, /VERİ YETERSİZ/);
assert.doesNotMatch(rendered, /<img/);
assert.match(rendered, /&lt;img/);
console.log('Panel: missing prices, blockers, provider-text escaping PASS');
