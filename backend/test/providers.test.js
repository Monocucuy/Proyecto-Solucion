import test from 'node:test';
import assert from 'node:assert/strict';
import { virusTotal } from '../src/providers/virustotal.js';
import { metaDefender } from '../src/providers/metadefender.js';
import { RateLimitError, AuthError, TransientError } from '../src/providers/errors.js';
import { H } from './helpers.js';

const resp = (status, body, headers = {}) => async () =>
  new Response(body === undefined ? null : JSON.stringify(body), { status, headers });

const vt = (fetchImpl) => virusTotal({ apiKey: 'k', fetchImpl });
const md = (fetchImpl) => metaDefender({ apiKey: 'k', fetchImpl });

test('VT: 200 parsea stats y total', async () => {
  const r = await vt(resp(200, { data: { attributes: { last_analysis_stats: { malicious: 5, suspicious: 1, undetected: 60, harmless: 4 } } } })).lookup(H('a'));
  assert.deepEqual(r, { found: true, malicious: 5, suspicious: 1, total: 70 });
});

test('VT: manda x-apikey, GET a /files/{hash}, sin body', async () => {
  let seen;
  await vt(async (url, init) => { seen = { url, init }; return new Response('{}', { status: 404 }); }).lookup(H('c'));
  assert.match(seen.url, new RegExp(`/files/${H('c')}$`));
  assert.equal(seen.init.headers['x-apikey'], 'k');
  assert.equal(seen.init.method, undefined); // GET: nunca sube el archivo
  assert.equal(seen.init.body, undefined);
});

test('VT: 404 => no encontrado (no limpio)', async () => {
  assert.equal((await vt(resp(404, {})).lookup(H('a'))).found, false);
});

test('VT: 200 sin stats => no encontrado', async () => {
  assert.equal((await vt(resp(200, { data: { attributes: {} } })).lookup(H('a'))).found, false);
});

test('VT: stats con basura no rompe', async () => {
  const r = await vt(resp(200, { data: { attributes: { last_analysis_stats: { malicious: 'x', suspicious: -4, undetected: null } } } })).lookup(H('a'));
  assert.deepEqual(r, { found: true, malicious: 0, suspicious: 0, total: 0 });
});

test('VT: 429 con Retry-After', async () => {
  await assert.rejects(vt(resp(429, {}, { 'retry-after': '42' })).lookup(H('a')), (e) => e instanceof RateLimitError && e.retryAfterMs === 42_000);
});
test('VT: 429 sin Retry-After', async () => {
  await assert.rejects(vt(resp(429, {})).lookup(H('a')), (e) => e instanceof RateLimitError && e.retryAfterMs === undefined);
});
test('VT: 401/403 => AuthError', async () => {
  for (const s of [401, 403]) await assert.rejects(vt(resp(s, {})).lookup(H('a')), AuthError);
});
test('VT: 500, JSON roto y red caida => TransientError', async () => {
  await assert.rejects(vt(resp(500, {})).lookup(H('a')), TransientError);
  await assert.rejects(vt(async () => new Response('<html>', { status: 200 })).lookup(H('a')), TransientError);
  await assert.rejects(vt(async () => { throw new TypeError('fetch failed'); }).lookup(H('a')), TransientError);
});

test('MD: 200 con scan_results', async () => {
  const r = await md(resp(200, { scan_results: { total_detected_avs: 12, total_avs: 40 } })).lookup(H('a'));
  assert.deepEqual(r, { found: true, malicious: 12, suspicious: 0, total: 40 });
});
test('MD: 404 y 200-con-error => no encontrado', async () => {
  assert.equal((await md(resp(404, {})).lookup(H('a'))).found, false);
  assert.equal((await md(resp(200, { error: { code: 404003 } })).lookup(H('a'))).found, false);
  assert.equal((await md(resp(200, { [H('a')]: 'Not Found' })).lookup(H('a'))).found, false);
});
test('MD: 429/401/500', async () => {
  await assert.rejects(md(resp(429, {})).lookup(H('a')), RateLimitError);
  await assert.rejects(md(resp(401, {})).lookup(H('a')), AuthError);
  await assert.rejects(md(resp(503, {})).lookup(H('a')), TransientError);
});

test('configured refleja la presencia de clave', () => {
  assert.equal(virusTotal({ apiKey: '' }).configured, false);
  assert.equal(metaDefender({ apiKey: 'x' }).configured, true);
});
