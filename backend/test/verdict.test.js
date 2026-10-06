import test from 'node:test';
import assert from 'node:assert/strict';
import { verdictOf, normalizeHash } from '../src/verdict.js';

test('mismas reglas que la app Android', () => {
  assert.equal(verdictOf({ found: true, malicious: 3, suspicious: 0, total: 70 }), 'MALICIOUS');
  assert.equal(verdictOf({ found: true, malicious: 2, suspicious: 0, total: 70 }), 'SUSPICIOUS');
  assert.equal(verdictOf({ found: true, malicious: 0, suspicious: 1, total: 70 }), 'SUSPICIOUS');
  assert.equal(verdictOf({ found: true, malicious: 0, suspicious: 0, total: 70 }), 'CLEAN');
});

test('no encontrado o sin motores NO es limpio', () => {
  assert.equal(verdictOf({ found: false, malicious: 0, suspicious: 0, total: 0 }), 'UNKNOWN');
  assert.equal(verdictOf({ found: true, malicious: 0, suspicious: 0, total: 0 }), 'UNKNOWN');
});

test('normalizeHash', () => {
  assert.equal(normalizeHash('A'.repeat(64)), 'a'.repeat(64));
  assert.equal(normalizeHash(' ' + 'b'.repeat(64) + '\n'), 'b'.repeat(64));
  for (const bad of ['', 'abc', 'g'.repeat(64), 'a'.repeat(63), 'a'.repeat(65), null, 5, {}, ['a']]) {
    assert.equal(normalizeHash(bad), null, String(bad));
  }
});
