/** Ventana fija por cliente. Suficiente para frenar abuso; no es un WAF. */
export function createRateLimiter({ limit, windowMs = 60_000, now = Date.now }) {
  const hits = new Map();
  const timer = setInterval(() => {
    const t = now();
    for (const [k, v] of hits) if (v.resetAt <= t) hits.delete(k);
  }, windowMs);
  timer.unref();
  return {
    /** @returns {{ok:boolean, retryAfterSec:number}} */
    check(key) {
      const t = now();
      let e = hits.get(key);
      if (!e || e.resetAt <= t) { e = { n: 0, resetAt: t + windowMs }; hits.set(key, e); }
      e.n++;
      return { ok: e.n <= limit, retryAfterSec: Math.max(1, Math.ceil((e.resetAt - t) / 1000)) };
    },
    stop: () => clearInterval(timer),
  };
}
