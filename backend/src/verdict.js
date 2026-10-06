// Misma regla que la app Android (domain/Models.kt: verdictOf).
export const Verdict = Object.freeze({
  CLEAN: 'CLEAN',
  SUSPICIOUS: 'SUSPICIOUS',
  MALICIOUS: 'MALICIOUS',
  UNKNOWN: 'UNKNOWN',
});

/**
 * @param {{found:boolean, malicious:number, suspicious:number, total?:number}} r
 * "No encontrado" o sin ningun motor que haya analizado el archivo NO es limpio: es UNKNOWN.
 */
export function verdictOf({ found, malicious, suspicious, total }) {
  if (!found) return Verdict.UNKNOWN;
  if (total !== undefined && total <= 0) return Verdict.UNKNOWN;
  if (malicious >= 3) return Verdict.MALICIOUS;
  if (malicious + suspicious >= 1) return Verdict.SUSPICIOUS;
  return Verdict.CLEAN;
}

const SHA256 = /^[a-f0-9]{64}$/;
export function normalizeHash(h) {
  if (typeof h !== 'string') return null;
  const x = h.trim().toLowerCase();
  return SHA256.test(x) ? x : null;
}
