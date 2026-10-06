import test from 'node:test';
import assert from 'node:assert/strict';
import { loadConfig } from '../src/config.js';
import { createApp } from '../src/server.js';
import { H, EICAR, fakeProvider, hit, miss, makeService } from './helpers.js';

async function boot({ providers, env = {}, svc = {} } = {}) {
  const config = loadConfig({ REQ_PER_MIN: '1000', ...env });
  const { service, db } = makeService(providers ?? [fakeProvider('vt', () => hit(0))], svc);
  const server = createApp({ service, config });
  await new Promise((r) => server.listen(0, '127.0.0.1', r));
  const base = `http://127.0.0.1:${server.address().port}`;
  const call = (path, { method = 'GET', body, headers = {} } = {}) =>
    fetch(base + path, {
      method, headers: { 'content-type': 'application/json', ...headers },
      body: body === undefined ? undefined : typeof body === 'string' ? body : JSON.stringify(body),
    }).then(async (r) => ({ status: r.status, headers: r.headers, json: await r.json().catch(() => null) }));
  return { call, service, db, close: () => new Promise((r) => { server.close(r); server.closeAllConnections(); }) };
}

test('health no requiere auth y no expone claves', async () => {
  const s = await boot({ env: { APP_TOKENS: 'secreto', VT_API_KEY: 'SUPERKEY' } });
  const r = await s.call('/health');
  assert.equal(r.status, 200); assert.equal(r.json.ok, true);
  assert.ok(!JSON.stringify(r.json).includes('SUPERKEY'));
  await s.close();
});

test('batch: pending -> done tras el worker; resultados indexados por hash', async () => {
  const s = await boot();
  let r = await s.call('/v1/reputation/batch', { method: 'POST', body: { hashes: [H('a'), H('b')] } });
  assert.equal(r.status, 200);
  assert.equal(r.json.pending, 2);
  assert.equal(r.json.results[H('a')].status, 'pending');
  await s.service.tick(); await s.service.tick();
  r = await s.call('/v1/reputation/batch', { method: 'POST', body: { hashes: [H('a'), H('b')] } });
  assert.equal(r.json.pending, 0);
  assert.equal(r.json.results[H('a')].verdict, 'CLEAN');
  await s.close();
});

test('batch: normaliza mayusculas y deduplica', async () => {
  const s = await boot();
  const r = await s.call('/v1/reputation/batch', { method: 'POST', body: { hashes: ['A'.repeat(64), 'a'.repeat(64), ' ' + 'a'.repeat(64)] } });
  assert.equal(r.status, 200);
  assert.deepEqual(Object.keys(r.json.results), ['a'.repeat(64)]);
  await s.close();
});

test('GET /v1/reputation/:hash', async () => {
  const s = await boot({ providers: [fakeProvider('vt', () => hit(60))] });
  let r = await s.call(`/v1/reputation/${EICAR}`);
  assert.equal(r.status, 200); assert.equal(r.json.status, 'pending'); assert.equal(r.json.hash, EICAR);
  await s.service.tick();
  r = await s.call(`/v1/reputation/${EICAR.toUpperCase()}`);
  assert.equal(r.json.verdict, 'MALICIOUS'); assert.equal(r.json.malicious, 60);
  await s.close();
});

test('desconocido para todos => UNKNOWN, jamas CLEAN', async () => {
  const s = await boot({ providers: [fakeProvider('vt', () => miss())] });
  await s.call(`/v1/reputation/${H('d')}`); await s.service.tick();
  const r = await s.call(`/v1/reputation/${H('d')}`);
  assert.equal(r.json.verdict, 'UNKNOWN'); assert.equal(r.json.found, false);
  await s.close();
});

test('validacion de entrada', async () => {
  const s = await boot({ env: { MAX_BATCH: '3' } });
  const post = (body) => s.call('/v1/reputation/batch', { method: 'POST', body });
  assert.equal((await post({})).json.error, 'hashes_required');
  assert.equal((await post({ hashes: [] })).json.error, 'hashes_required');
  assert.equal((await post({ hashes: 'x' })).json.error, 'hashes_required');
  assert.equal((await post(null)).json.error, 'hashes_required');
  assert.equal((await post([H('a')])).json.error, 'hashes_required');
  assert.equal((await post({ hashes: [H('a'), 'nope'] })).json.error, 'invalid_hash');
  assert.equal((await post({ hashes: [H('a'), 5] })).json.error, 'invalid_hash');
  assert.equal((await post({ hashes: [H('a'), H('b'), H('c'), H('d')] })).json.error, 'batch_too_large');
  assert.equal((await post('{no json')).json.error, 'invalid_json');
  assert.equal((await s.call('/v1/reputation/zzz')).json.error, 'invalid_hash');
  assert.equal((await s.call('/v1/reputation/%E0%A4%A')).json.error, 'invalid_hash'); // URI malformado => 400, no 500
  assert.equal((await s.call('/v1/otra')).status, 404);
  assert.equal((await s.call('/nada')).status, 404);
  await s.close();
});

test('una entrada invalida no encola nada (todo-o-nada)', async () => {
  const s = await boot();
  await s.call('/v1/reputation/batch', { method: 'POST', body: { hashes: [H('a'), 'malo'] } });
  assert.equal(s.db.queueSize(), 0);
  await s.close();
});

test('cuerpo > 64KB => 413', async () => {
  const s = await boot();
  const r = await s.call('/v1/reputation/batch', { method: 'POST', body: JSON.stringify({ hashes: [H('a')], pad: 'x'.repeat(70_000) }) });
  assert.equal(r.status, 413);
  await s.close();
});

test('el servidor solo acepta hashes: campos extra (rutas, nombres de apps) se ignoran y no se guardan', async () => {
  const s = await boot();
  await s.call('/v1/reputation/batch', { method: 'POST', body: { hashes: [H('a')], packageName: 'com.secreto.app', path: '/data/app/x.apk' } });
  const dump = JSON.stringify([...s.db.raw.prepare('SELECT * FROM queue').all(), ...s.db.raw.prepare('SELECT * FROM cache').all()]);
  assert.ok(!dump.includes('secreto')); assert.ok(!dump.includes('/data/app'));
  await s.close();
});

test('auth: sin token, token malo => 401; token bueno => 200; hay mas de un token', async () => {
  const s = await boot({ env: { APP_TOKENS: 'uno, dos' } });
  const body = { hashes: [H('a')] };
  assert.equal((await s.call('/v1/reputation/batch', { method: 'POST', body })).status, 401);
  assert.equal((await s.call('/v1/reputation/batch', { method: 'POST', body, headers: { authorization: 'Bearer malo' } })).status, 401);
  assert.equal((await s.call('/v1/reputation/batch', { method: 'POST', body, headers: { authorization: 'uno' } })).status, 401);
  assert.equal((await s.call('/v1/reputation/batch', { method: 'POST', body, headers: { authorization: 'Bearer uno' } })).status, 200);
  assert.equal((await s.call('/v1/reputation/batch', { method: 'POST', body, headers: { authorization: 'Bearer dos' } })).status, 200);
  assert.equal((await s.call(`/v1/reputation/${H('a')}`)).status, 401);
  await s.close();
});

test('rate limit por cliente => 429 con Retry-After', async () => {
  const s = await boot({ env: { REQ_PER_MIN: '3' } });
  for (let i = 0; i < 3; i++) assert.equal((await s.call(`/v1/reputation/${H('a')}`)).status, 200);
  const r = await s.call(`/v1/reputation/${H('a')}`);
  assert.equal(r.status, 429); assert.ok(Number(r.headers.get('retry-after')) >= 1);
  assert.equal((await s.call('/health')).status, 200); // health no cuenta
  await s.close();
});

test('upstream caido => 200 con unavailable, el servidor no revienta', async () => {
  const s = await boot({ providers: [fakeProvider('vt', () => { throw new TypeError('x'); })], svc: { maxAttempts: 1 } });
  await s.call(`/v1/reputation/${H('e')}`); await s.service.tick();
  const r = await s.call(`/v1/reputation/${H('e')}`);
  assert.equal(r.status, 200); assert.equal(r.json.status, 'unavailable'); assert.equal(r.json.verdict, 'UNKNOWN');
  await s.close();
});

test('errores internos no filtran detalles', async () => {
  const s = await boot();
  s.service.lookup = () => { throw new Error('SQLITE_CORRUPT /var/db/secret.db'); };
  const r = await s.call(`/v1/reputation/${H('a')}`);
  assert.equal(r.status, 500); assert.deepEqual(r.json, { error: 'internal' });
  await s.close();
});
