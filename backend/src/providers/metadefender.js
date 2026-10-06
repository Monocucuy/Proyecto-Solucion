import { RateLimitError, AuthError, TransientError } from './errors.js';

/** Respaldo / segunda opinion: MetaDefender Cloud v4, busqueda por hash. */
export function metaDefender({ apiKey, baseUrl = 'https://api.metadefender.com/v4', minGapMs = 2_000, fetchImpl = fetch, timeoutMs = 10_000 }) {
  const notFound = { found: false, malicious: 0, suspicious: 0, total: 0 };
  return {
    name: 'metadefender',
    configured: !!apiKey,
    minGapMs,
    async lookup(hash) {
      let res;
      try {
        res = await fetchImpl(`${baseUrl}/hash/${hash}`, {
          headers: { apikey: apiKey, accept: 'application/json' },
          signal: AbortSignal.timeout(timeoutMs),
        });
      } catch (e) {
        throw new TransientError(`net:${e.name}`);
      }
      if (res.status === 404) return notFound;
      if (res.status === 429) {
        const ra = Number(res.headers.get('retry-after'));
        throw new RateLimitError(ra > 0 ? ra * 1000 : undefined);
      }
      if (res.status === 401 || res.status === 403) throw new AuthError();
      if (res.status !== 200) throw new TransientError(`http:${res.status}`);
      let body;
      try { body = await res.json(); } catch { throw new TransientError('bad_json'); }
      // Hash desconocido: MetaDefender puede responder 200 con {error:{...}} o {<hash>:"Not Found"}.
      if (!body || body.error || !body.scan_results) return notFound;
      const total = Number(body.scan_results.total_avs) || 0;
      const detected = Number(body.scan_results.total_detected_avs) || 0;
      return { found: true, malicious: Math.max(0, Math.floor(detected)), suspicious: 0, total: Math.max(0, Math.floor(total)) };
    },
  };
}
