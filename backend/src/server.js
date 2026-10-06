import { createServer } from 'node:http';
import { timingSafeEqual, createHash } from 'node:crypto';
import { normalizeHash } from './verdict.js';
import { createRateLimiter } from './ratelimit.js';

const MAX_BODY = 64 * 1024;
const digest = (s) => createHash('sha256').update(s).digest();

export function createApp({ service, config, now = Date.now }) {
  const limiter = createRateLimiter({ limit: config.reqPerMin, now });
  const tokens = config.appTokens.map(digest);

  const send = (res, code, obj, headers = {}) => {
    const body = JSON.stringify(obj);
    res.writeHead(code, { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store', ...headers });
    res.end(body);
  };

  const authorized = (req) => {
    if (tokens.length === 0) return true;
    const m = /^Bearer (.+)$/.exec(req.headers.authorization || '');
    if (!m) return false;
    const d = digest(m[1]);
    return tokens.some((t) => timingSafeEqual(t, d));
  };

  const clientKey = (req) => {
    if (config.trustProxy) {
      const xff = String(req.headers['x-forwarded-for'] || '').split(',')[0].trim();
      if (xff) return xff;
    }
    return req.socket.remoteAddress || 'unknown';
  };

  const readJson = (req) => new Promise((resolve, reject) => {
    if (Number(req.headers['content-length']) > MAX_BODY) return reject({ code: 413, error: 'body_too_large' });
    let size = 0, over = false; const chunks = [];
    req.on('data', (c) => {
      if (over) return; // descarta el resto; la respuesta 413 cierra la conexion
      size += c.length;
      if (size > MAX_BODY) { over = true; chunks.length = 0; reject({ code: 413, error: 'body_too_large' }); return; }
      chunks.push(c);
    });
    req.on('end', () => {
      if (over) return;
      try { resolve(JSON.parse(Buffer.concat(chunks).toString('utf8'))); }
      catch { reject({ code: 400, error: 'invalid_json' }); }
    });
    req.on('error', () => reject({ code: 400, error: 'read_error' }));
  });

  const handler = async (req, res) => {
    try {
      const url = new URL(req.url, 'http://x');
      const path = url.pathname;

      if (req.method === 'GET' && path === '/health') {
        return send(res, 200, { ok: true, ...service.status() });
      }
      if (!path.startsWith('/v1/')) return send(res, 404, { error: 'not_found' });

      if (!authorized(req)) return send(res, 401, { error: 'unauthorized' }, { 'www-authenticate': 'Bearer' });
      const rl = limiter.check(clientKey(req));
      if (!rl.ok) return send(res, 429, { error: 'rate_limited' }, { 'retry-after': String(rl.retryAfterSec) });

      if (req.method === 'POST' && path === '/v1/reputation/batch') {
        const body = await readJson(req);
        const list = body && typeof body === 'object' ? body.hashes : undefined;
        if (!Array.isArray(list) || list.length === 0) return send(res, 400, { error: 'hashes_required' });
        if (list.length > config.maxBatch) return send(res, 400, { error: 'batch_too_large', max: config.maxBatch });
        const uniq = new Set();
        for (const h of list) {
          const n = normalizeHash(h);
          if (!n) return send(res, 400, { error: 'invalid_hash' });
          uniq.add(n);
        }
        const results = {}; let pending = 0;
        for (const h of uniq) {
          const r = service.lookup(h);
          if (r.status === 'pending') pending++;
          results[h] = r;
        }
        return send(res, 200, { results, pending });
      }

      const m = /^\/v1\/reputation\/([^/]+)$/.exec(path);
      if (req.method === 'GET' && m) {
        let raw; try { raw = decodeURIComponent(m[1]); } catch { return send(res, 400, { error: 'invalid_hash' }); }
        const h = normalizeHash(raw);
        if (!h) return send(res, 400, { error: 'invalid_hash' });
        return send(res, 200, { hash: h, ...service.lookup(h) });
      }

      return send(res, 404, { error: 'not_found' });
    } catch (e) {
      if (e && e.code && e.error) {
        // 413: responder primero y luego cortar, para no leer un cuerpo enorme.
        if (e.code === 413) res.once('finish', () => req.socket.destroy());
        return send(res, e.code, { error: e.error }, e.code === 413 ? { connection: 'close' } : {});
      }
      return send(res, 500, { error: 'internal' }); // sin detalles al cliente
    }
  };

  const server = createServer(handler);
  server.on('close', () => limiter.stop());
  return server;
}
