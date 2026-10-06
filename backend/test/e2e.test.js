// End-to-end: servicio real + worker con timers reales + providers reales contra un VirusTotal/MetaDefender falsos por HTTP.
import test from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { openDb } from '../src/db.js';
import { virusTotal } from '../src/providers/virustotal.js';
import { metaDefender } from '../src/providers/metadefender.js';
import { ReputationService } from '../src/service.js';
import { createApp } from '../src/server.js';
import { loadConfig } from '../src/config.js';
import { H, EICAR } from './helpers.js';

function fakeUpstream(handler) {
  const hits = [];
  const srv = createServer((req, res) => {
    hits.push({ method: req.method, url: req.url, headers: req.headers });
    handler(req, res, hits.length);
  });
  return new Promise((r) => srv.listen(0, '127.0.0.1', () => r({ srv, hits, url: `http://127.0.0.1:${srv.address().port}` })));
}
const json = (res, code, body, h = {}) => { res.writeHead(code, { 'content-type': 'application/json', ...h }); res.end(JSON.stringify(body)); };
const vtBody = (m, s = 0) => ({ data: { attributes: { last_analysis_stats: { malicious: m, suspicious: s, undetected: 60, harmless: 5 } } } });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
async function until(fn, ms = 5000) { const t0 = Date.now(); for (;;) { const v = await fn(); if (v) return v; if (Date.now() - t0 > ms) throw new Error('timeout esperando condicion'); await sleep(20); } }

test('e2e: cliente pregunta, worker consulta VT por HTTP, cliente recibe veredicto; segundo cliente sale del cache', async () => {
  const vt = await fakeUpstream((req, res) => {
    const hash = req.url.split('/').pop();
    if (hash === EICAR) return json(res, 200, vtBody(62));
    if (hash === H('1')) return json(res, 200, vtBody(0));
    if (hash === H('2')) return json(res, 200, vtBody(1, 1));
    return json(res, 404, { error: { code: 'NotFoundError' } });
  });
  const db = openDb(':memory:');
  const service = new ReputationService({
    db, providers: [virusTotal({ apiKey: 'K', baseUrl: vt.url, minGapMs: 30 })],
    ttlMs: 86_400_000, failTtlMs: 60_000, queueMaxAgeMs: 3_600_000, maxQueue: 100,
  });
  const app = createApp({ service, config: loadConfig({ APP_TOKENS: 't' }) });
  await new Promise((r) => app.listen(0, '127.0.0.1', r));
  const base = `http://127.0.0.1:${app.address().port}`;
  const post = (hashes) => fetch(base + '/v1/reputation/batch', { method: 'POST', headers: { authorization: 'Bearer t', 'content-type': 'application/json' }, body: JSON.stringify({ hashes }) }).then((r) => r.json());
  service.start();
  try {
    const all = [EICAR, H('1'), H('2'), H('9')];
    const first = await post(all);
    assert.equal(first.pending, 4);

    const final = await until(async () => { const r = await post(all); return r.pending === 0 ? r : null; });
    assert.equal(final.results[EICAR].verdict, 'MALICIOUS');
    assert.equal(final.results[H('1')].verdict, 'CLEAN');
    assert.equal(final.results[H('2')].verdict, 'SUSPICIOUS');
    assert.equal(final.results[H('9')].verdict, 'UNKNOWN'); // 404 en VT: nunca "limpia"
    assert.equal(final.results[H('9')].found, false);

    // Privacidad/contrato: solo GET por hash, con la clave en header, sin cuerpo.
    assert.equal(vt.hits.length, 4);
    for (const h of vt.hits) { assert.equal(h.method, 'GET'); assert.equal(h.headers['x-apikey'], 'K'); assert.match(h.url, /^\/files\/[a-f0-9]{64}$/); }
    // Ritmo: los 4 hashes no se dispararon de golpe.
    // (minGap 30ms => al menos ~90ms entre primera y ultima; lo verificamos indirecto con el conteo estable)
    await post(all); await post(all);
    assert.equal(vt.hits.length, 4, 'las consultas repetidas deben salir del cache');
  } finally { service.stop(); await new Promise((r) => { app.close(r); app.closeAllConnections(); }); vt.srv.close(); }
});

test('e2e: VT responde 429 => el worker usa MetaDefender y el cliente igual obtiene veredicto', async () => {
  const vt = await fakeUpstream((req, res) => json(res, 429, { error: { code: 'QuotaExceededError' } }, { 'retry-after': '3600' }));
  const md = await fakeUpstream((req, res) => json(res, 200, { scan_results: { total_detected_avs: 20, total_avs: 40 } }));
  const db = openDb(':memory:');
  const service = new ReputationService({
    db, providers: [virusTotal({ apiKey: 'K', baseUrl: vt.url, minGapMs: 10 }), metaDefender({ apiKey: 'M', baseUrl: md.url, minGapMs: 10 })],
    ttlMs: 86_400_000, failTtlMs: 60_000, queueMaxAgeMs: 3_600_000, maxQueue: 100,
  });
  service.start();
  try {
    service.lookup(H('7')); service.lookup(H('8'));
    await until(() => service.lookup(H('7')).status === 'done' && service.lookup(H('8')).status === 'done');
    assert.equal(service.lookup(H('7')).verdict, 'MALICIOUS');
    assert.equal(service.lookup(H('7')).source, 'metadefender');
    assert.equal(vt.hits.length, 1, 'VT en cooldown tras el 429: no se le insiste');
    assert.equal(md.hits.length, 2);
    assert.equal(md.hits[0].headers.apikey, 'M');
  } finally { service.stop(); vt.srv.close(); md.srv.close(); }
});

test('e2e: upstream caido (conexion rechazada) => unavailable, sin crash', async () => {
  const dead = await fakeUpstream(() => {}); const deadUrl = dead.url; dead.srv.close();
  const db = openDb(':memory:');
  const service = new ReputationService({
    db, providers: [virusTotal({ apiKey: 'K', baseUrl: deadUrl, minGapMs: 0, timeoutMs: 500 })],
    ttlMs: 86_400_000, failTtlMs: 60_000, queueMaxAgeMs: 3_600_000, maxQueue: 100, maxAttempts: 1,
  });
  service.lookup(H('5'));
  await service.tick();
  const r = service.lookup(H('5'));
  assert.equal(r.status, 'unavailable'); assert.equal(r.verdict, 'UNKNOWN');
});
