import { RateLimitError, AuthError, TransientError } from './errors.js';

/** Solo consulta por hash (GET /files/{sha256}). Nunca sube archivos. */
export function virusTotal({ apiKey, baseUrl = 'https://www.virustotal.com/api/v3', minGapMs = 15_000, fetchImpl = fetch, timeoutMs = 10_000 }) {
  return {
    name: 'virustotal',
    configured: !!apiKey,
    minGapMs,
    async lookup(hash) {
      let res;
      try {
        res = await fetchImpl(`${baseUrl}/files/${hash}`, {
          headers: { 'x-apikey': apiKey, accept: 'application/json' },
          signal: AbortSignal.timeout(timeoutMs),
        });
      } catch (e) {
        throw new TransientError(`net:${e.name}`);
      }
      if (res.status === 404) return { found: false, malicious: 0, suspicious: 0, total: 0 };
      if (res.status === 429) {
        const ra = Number(res.headers.get('retry-after'));
        throw new RateLimitError(ra > 0 ? ra * 1000 : undefined);
      }
      if (res.status === 401 || res.status === 403) throw new AuthError();
      if (res.status !== 200) throw new TransientError(`http:${res.status}`);
      let body;
      try { body = await res.json(); } catch { throw new TransientError('bad_json'); }
      const s = body?.data?.attributes?.last_analysis_stats;
      if (!s || typeof s !== 'object') return { found: false, malicious: 0, suspicious: 0, total: 0 };
      const n = (x) => (Number.isFinite(x) && x > 0 ? Math.floor(x) : 0);
      const malicious = n(s.malicious), suspicious = n(s.suspicious);
      const total = malicious + suspicious + n(s.undetected) + n(s.harmless);
      return { found: true, malicious, suspicious, total };
    },
  };
}
