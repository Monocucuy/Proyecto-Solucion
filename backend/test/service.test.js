import test from 'node:test';
import assert from 'node:assert/strict';
import { openDb } from '../src/db.js';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { H, EICAR, fakeProvider, hit, miss, makeService, clock, RateLimitError, AuthError, TransientError } from './helpers.js';

test('hash nuevo => pending; tras tick => done y queda en cache', async () => {
  const p = fakeProvider('vt', () => hit(0));
  const { service } = makeService([p]);
  assert.deepEqual(service.lookup(H('a')), { status: 'pending' });
  assert.deepEqual(service.lookup(H('a')), { status: 'pending' }); // idempotente, no duplica
  await service.tick();
  const r = service.lookup(H('a'));
  assert.equal(r.status, 'done');
  assert.equal(r.verdict, 'CLEAN');
  assert.equal(r.source, 'vt');
  assert.equal(p.calls.length, 1);
});

test('EICAR: >=3 motores => MALICIOUS', async () => {
  const { service } = makeService([fakeProvider('vt', () => hit(62))]);
  service.lookup(EICAR); await service.tick();
  assert.equal(service.lookup(EICAR).verdict, 'MALICIOUS');
});

test('cache caliente: segundo cliente no gasta cuota', async () => {
  const p = fakeProvider('vt', () => hit(0));
  const { service } = makeService([p]);
  service.lookup(H('a')); await service.tick();
  for (let i = 0; i < 20; i++) assert.equal(service.lookup(H('a')).status, 'done');
  assert.equal(p.calls.length, 1);
});

test('TTL de 7 dias: expira y se reconsulta', async () => {
  const p = fakeProvider('vt', () => hit(0));
  const { service, now } = makeService([p]);
  service.lookup(H('a')); await service.tick();
  now.advance(7 * 86_400_000 - 1);
  assert.equal(service.lookup(H('a')).status, 'done');
  now.advance(2);
  assert.equal(service.lookup(H('a')).status, 'pending');
  await service.tick();
  assert.equal(p.calls.length, 2);
});

test('hash desconocido para todos => UNKNOWN con found=false (no CLEAN) y se cachea', async () => {
  const vt = fakeProvider('vt', () => miss()), md = fakeProvider('md', () => miss());
  const { service } = makeService([vt, md]);
  service.lookup(H('a')); await service.tick();
  const r = service.lookup(H('a'));
  assert.equal(r.verdict, 'UNKNOWN'); assert.equal(r.found, false);
  assert.equal(vt.calls.length, 1); assert.equal(md.calls.length, 1); // segunda opinion
});

test('VT no lo conoce, MD si => usa MD', async () => {
  const { service } = makeService([fakeProvider('vt', () => miss()), fakeProvider('md', () => hit(9))]);
  service.lookup(H('a')); await service.tick();
  const r = service.lookup(H('a'));
  assert.equal(r.verdict, 'MALICIOUS'); assert.equal(r.source, 'md');
});

test('found pero total=0 (sin analisis) se trata como desconocido', async () => {
  const { service } = makeService([fakeProvider('vt', () => hit(0, 0, 0))]);
  service.lookup(H('a')); await service.tick();
  assert.equal(service.lookup(H('a')).verdict, 'UNKNOWN');
});

test('429 en VT => cooldown y cae a MD sin perder el hash', async () => {
  const vt = fakeProvider('vt', () => new RateLimitError(120_000));
  const md = fakeProvider('md', () => hit(0));
  const { service, now } = makeService([vt, md]);
  service.lookup(H('a')); service.lookup(H('b'));
  await service.tick();
  assert.equal(service.lookup(H('a')).source, 'md');
  await service.tick(); // b: VT sigue en cooldown, no se le vuelve a pegar
  assert.equal(vt.calls.length, 1);
  assert.equal(md.calls.length, 2);
  now.advance(120_001);
  service.lookup(H('c')); await service.tick();
  assert.equal(vt.calls.length, 2); // vuelve a usarse tras el cooldown
});

test('429 en todos los proveedores: hash sigue en cola, espera, y no gasta intentos', async () => {
  let limited = true;
  const vt = fakeProvider('vt', () => (limited ? new RateLimitError(60_000) : hit(0)));
  const { service, now } = makeService([vt]);
  service.lookup(H('a'));
  await service.tick();
  assert.equal(service.lookup(H('a')).status, 'pending');
  const t = await service.tick();
  assert.equal(t.worked, false); assert.ok(t.waitMs >= 50); // espera, no martilla
  assert.equal(vt.calls.length, 1);
  limited = false; now.advance(60_001);
  await service.tick();
  assert.equal(service.lookup(H('a')).status, 'done');
});

test('clave rechazada (401) deshabilita ese proveedor y usa el otro', async () => {
  const vt = fakeProvider('vt', () => new AuthError());
  const md = fakeProvider('md', () => hit(0));
  const { service } = makeService([vt, md]);
  service.lookup(H('a')); await service.tick();
  service.lookup(H('b')); await service.tick();
  assert.equal(vt.calls.length, 1); // no reintenta con clave mala
  assert.equal(service.lookup(H('b')).status, 'done');
  assert.equal(service.status().providers.vt.disabled, true);
});

test('todas las claves rechazadas => unavailable/no_provider, no queda colgado', async () => {
  const { service } = makeService([fakeProvider('vt', () => new AuthError())]);
  service.lookup(H('a')); await service.tick();
  service.lookup(H('b')); await service.tick();
  const r = service.lookup(H('b'));
  assert.equal(r.status, 'unavailable'); assert.equal(r.error, 'no_provider'); assert.equal(r.verdict, 'UNKNOWN');
});

test('sin proveedores configurados => unavailable inmediato, no encola', () => {
  const { service, db } = makeService([fakeProvider('vt', () => hit(0), { configured: false })]);
  const r = service.lookup(H('a'));
  assert.equal(r.status, 'unavailable'); assert.equal(r.error, 'no_provider');
  assert.equal(db.queueSize(), 0);
});

test('error transitorio: backoff, reintenta y al agotar intentos => unavailable (con TTL corto)', async () => {
  const vt = fakeProvider('vt', () => new TransientError('http:500'));
  const { service, now } = makeService([vt], { maxAttempts: 3 });
  service.lookup(H('a'));
  await service.tick(); assert.equal(service.lookup(H('a')).status, 'pending');
  let t = await service.tick(); assert.equal(t.worked, false); // todavia en backoff
  now.advance(20_001); await service.tick();
  now.advance(40_001); await service.tick();
  assert.equal(vt.calls.length, 3);
  const r = service.lookup(H('a'));
  assert.equal(r.status, 'unavailable'); assert.equal(r.error, 'upstream_error');
  assert.equal(vt.calls.length, 3); // los clientes no re-encolan en bucle
  now.advance(600_001);
  assert.equal(service.lookup(H('a')).status, 'pending'); // tras el TTL corto se puede reintentar
});

test('transitorio en VT pero MD responde => resuelto', async () => {
  const { service } = makeService([fakeProvider('vt', () => new TransientError()), fakeProvider('md', () => hit(1))]);
  service.lookup(H('a')); await service.tick();
  assert.equal(service.lookup(H('a')).verdict, 'SUSPICIOUS');
});

test('ritmo: respeta minGapMs de cada proveedor', async () => {
  const vt = fakeProvider('vt', () => hit(0), { minGapMs: 15_000 });
  const { service, now } = makeService([vt]);
  service.lookup(H('a')); service.lookup(H('b'));
  await service.tick();
  const t = await service.tick();
  assert.equal(t.worked, false); assert.equal(vt.calls.length, 1);
  assert.ok(t.waitMs > 14_000 && t.waitMs <= 15_000);
  now.advance(15_000); await service.tick();
  assert.equal(vt.calls.length, 2);
});

test('cola llena => unavailable/queue_full', () => {
  const { service } = makeService([fakeProvider('vt', () => hit(0))], { maxQueue: 2 });
  assert.equal(service.lookup(H('a')).status, 'pending');
  assert.equal(service.lookup(H('b')).status, 'pending');
  const r = service.lookup(H('c'));
  assert.equal(r.status, 'unavailable'); assert.equal(r.error, 'queue_full');
});

test('items viejos en cola expiran (no hay espera infinita si la cuota diaria se agoto)', async () => {
  const vt = fakeProvider('vt', () => new RateLimitError(600_000));
  const { service, now } = makeService([vt], { queueMaxAgeMs: 3_600_000 });
  service.lookup(H('a')); await service.tick();
  now.advance(3_600_001); await service.tick();
  const r = service.lookup(H('a'));
  assert.equal(r.status, 'unavailable'); assert.equal(r.error, 'timeout');
});

test('orden FIFO', async () => {
  const vt = fakeProvider('vt', () => hit(0));
  const { service, now } = makeService([vt]);
  service.lookup(H('a')); now.advance(1); service.lookup(H('b')); now.advance(1); service.lookup(H('c'));
  await service.tick(); await service.tick(); await service.tick();
  assert.deepEqual(vt.calls, [H('a'), H('b'), H('c')]);
});

test('persistencia: la cola y el cache sobreviven a un reinicio', async () => {
  const dir = mkdtempSync(join(tmpdir(), 'rep-'));
  try {
    const path = join(dir, 'r.db'); const now = clock();
    let db = openDb(path);
    let { service } = makeService([fakeProvider('vt', () => hit(0))], { db, now });
    service.lookup(H('a')); service.lookup(H('b'));
    await service.tick(); // resuelve 'a'
    db.close();

    db = openDb(path);
    const vt2 = fakeProvider('vt', () => hit(0));
    ({ service } = makeService([vt2], { db, now }));
    assert.equal(service.lookup(H('a')).status, 'done'); // cache persistido
    assert.equal(service.lookup(H('b')).status, 'pending'); // cola persistida
    await service.tick();
    assert.deepEqual(vt2.calls, [H('b')]);
    db.close();
  } finally { rmSync(dir, { recursive: true, force: true }); }
});

test('un tick con excepcion inesperada del proveedor no tumba el worker', async () => {
  const { service } = makeService([fakeProvider('vt', () => { throw new RangeError('boom'); })]);
  service.lookup(H('a'));
  await assert.doesNotReject(service.tick()); // se trata como transitorio
});
