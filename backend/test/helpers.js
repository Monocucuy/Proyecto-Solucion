import { openDb } from '../src/db.js';
import { ReputationService } from '../src/service.js';
import { RateLimitError, AuthError, TransientError } from '../src/providers/errors.js';

export const H = (c) => c.repeat(64);
export const EICAR = '275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f';

export function clock(start = 1_000_000) {
  let t = start;
  const now = () => t;
  now.advance = (ms) => { t += ms; };
  return now;
}

/** Proveedor falso: `script` es una funcion (hash, n) => resultado | Error. */
export function fakeProvider(name, script, { minGapMs = 0, configured = true } = {}) {
  const calls = [];
  return {
    name, configured, minGapMs, calls,
    async lookup(hash) {
      calls.push(hash);
      const r = script(hash, calls.length);
      if (r instanceof Error) throw r;
      return r;
    },
  };
}
export const hit = (malicious, suspicious = 0, total = 70) => ({ found: true, malicious, suspicious, total });
export const miss = () => ({ found: false, malicious: 0, suspicious: 0, total: 0 });
export { RateLimitError, AuthError, TransientError };

export function makeService(providers, over = {}) {
  const now = over.now ?? clock();
  const db = over.db ?? openDb(':memory:');
  const service = new ReputationService({
    db, providers, now,
    ttlMs: 7 * 86_400_000, failTtlMs: 600_000, queueMaxAgeMs: 3_600_000, maxQueue: 100,
    ...over,
  });
  return { service, db, now };
}
