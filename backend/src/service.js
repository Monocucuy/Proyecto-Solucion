import { verdictOf } from './verdict.js';
import { RateLimitError, AuthError } from './providers/errors.js';

const DEFAULT_COOLDOWN_MS = 60_000;
const AUTH_DISABLE_MS = 60 * 60_000;
const MAX_BACKOFF_MS = 5 * 60_000;

/**
 * Cache compartido + cola persistente. Los clientes preguntan por hashes; lo que no esta en cache se
 * encola y un unico worker lo resuelve respetando el ritmo de cada proveedor, asi N usuarios comparten
 * la misma cuota en vez de gastar una clave gratuita cada uno.
 */
export class ReputationService {
  constructor({ db, providers, ttlMs, failTtlMs, queueMaxAgeMs, maxQueue, maxAttempts = 3, now = Date.now, log = () => {} }) {
    Object.assign(this, { db, providers, ttlMs, failTtlMs, queueMaxAgeMs, maxQueue, maxAttempts, now, log });
    this.state = new Map(providers.map((p) => [p.name, { nextAllowedAt: 0, cooldownUntil: 0, disabledUntil: 0 }]));
    this.timer = null;
    this.running = false;
  }

  /** Configurado y con la clave no rechazada. */
  #live(t = this.now()) {
    return this.providers.filter((p) => p.configured && this.state.get(p.name).disabledUntil <= t);
  }

  /** Sin proveedores vivos nadie va a resolver la cola: responder ya en vez de retener a los clientes. */
  #drainIfDead(t) {
    if (this.#live(t).length > 0) return false;
    for (let j; (j = this.db.nextDue(Number.MAX_SAFE_INTEGER));) {
      this.db.dequeue(j.hash);
      this.db.putUnavailable(j.hash, t + this.failTtlMs, 'no_provider');
    }
    return true;
  }

  /** Resultado inmediato para un hash ya normalizado. */
  lookup(hash) {
    const t = this.now();
    const c = this.db.getCache(hash);
    if (c && t - c.checked_at < this.ttlMs) return this.#fromCache(c);

    const u = this.db.getUnavailable(hash);
    if (u && u.until > t) return { status: 'unavailable', verdict: 'UNKNOWN', error: u.reason };

    if (this.db.isQueued(hash)) return { status: 'pending' };
    if (this.#live(t).length === 0) return { status: 'unavailable', verdict: 'UNKNOWN', error: 'no_provider' };
    if (this.db.queueSize() >= this.maxQueue) return { status: 'unavailable', verdict: 'UNKNOWN', error: 'queue_full' };
    this.db.enqueue(hash, t);
    return { status: 'pending' };
  }

  #fromCache(c) {
    const r = { found: !!c.found, malicious: c.malicious, suspicious: c.suspicious, total: c.total };
    return {
      status: 'done', verdict: verdictOf(r), found: r.found,
      malicious: r.malicious, suspicious: r.suspicious, source: c.source, checkedAt: c.checked_at,
    };
  }

  #available(p, t) {
    const s = this.state.get(p.name);
    return p.configured && s.disabledUntil <= t && s.cooldownUntil <= t && s.nextAllowedAt <= t;
  }

  #readyAt(p) {
    const s = this.state.get(p.name);
    return Math.max(s.nextAllowedAt, s.cooldownUntil, s.disabledUntil);
  }

  /** Procesa a lo sumo un hash. Devuelve cuantos ms conviene esperar antes del siguiente tick. */
  async tick() {
    const t = this.now();
    this.db.purgeUnavailable(t);
    for (const h of this.db.expiredBefore(t - this.queueMaxAgeMs)) {
      this.db.dequeue(h);
      this.db.putUnavailable(h, t + this.failTtlMs, 'timeout');
    }

    const job = this.db.nextDue(t);
    if (!job) {
      const e = this.db.earliestDue();
      return { worked: false, waitMs: e ? Math.max(50, e - t) : 1000 };
    }

    if (this.#drainIfDead(t)) return { worked: true, waitMs: 0 };

    const configured = this.#live(t);
    const usable = configured.filter((p) => this.#available(p, t));
    if (usable.length === 0) {
      const next = Math.min(...configured.map((p) => this.#readyAt(p)));
      return { worked: false, waitMs: Math.max(50, next - t) };
    }

    let answered = null;
    let transientFailure = false;
    for (const p of usable) {
      const s = this.state.get(p.name);
      s.nextAllowedAt = this.now() + p.minGapMs;
      try {
        const r = await p.lookup(job.hash);
        if (r.found && r.total > 0) { answered = { r, source: p.name }; break; }
        answered = answered ?? { r: { found: false, malicious: 0, suspicious: 0, total: 0 }, source: p.name };
        // no encontrado: sigue con el siguiente proveedor disponible como segunda opinion
      } catch (e) {
        if (e instanceof RateLimitError) {
          s.cooldownUntil = this.now() + (e.retryAfterMs ?? DEFAULT_COOLDOWN_MS);
          this.log('provider_rate_limited', p.name);
        } else if (e instanceof AuthError) {
          s.disabledUntil = this.now() + AUTH_DISABLE_MS;
          this.log('provider_auth_rejected', p.name);
        } else {
          transientFailure = true;
          this.log('provider_error', p.name, e.message);
        }
      }
    }

    const done = this.now();
    this.#drainIfDead(done); // una clave rechazada en este tick puede haber matado al ultimo proveedor
    if (answered) {
      this.db.putCache(job.hash, answered.r, answered.source, done);
      this.db.dequeue(job.hash);
    } else if (transientFailure) {
      const attempts = job.attempts + 1;
      if (attempts >= this.maxAttempts) {
        this.db.dequeue(job.hash);
        this.db.putUnavailable(job.hash, done + this.failTtlMs, 'upstream_error');
      } else {
        this.db.retryLater(job.hash, attempts, done + Math.min(2 ** attempts * 10_000, MAX_BACKOFF_MS));
      }
    }
    // Solo 429/401: el hash sigue en cola sin gastar intentos; expira por queueMaxAgeMs si no hay salida.
    return { worked: true, waitMs: 0 };
  }

  start() {
    if (this.running) return;
    this.running = true;
    const loop = async () => {
      if (!this.running) return;
      let wait = 1000;
      try { ({ waitMs: wait } = await this.tick()); }
      catch (e) { this.log('tick_error', e.message); wait = 5000; }
      if (this.running) { this.timer = setTimeout(loop, wait); this.timer.unref?.(); }
    };
    loop();
  }

  stop() { this.running = false; clearTimeout(this.timer); }

  status() {
    const t = this.now();
    return {
      queueDepth: this.db.queueSize(),
      providers: Object.fromEntries(this.providers.map((p) => {
        const s = this.state.get(p.name);
        return [p.name, {
          configured: p.configured,
          disabled: s.disabledUntil > t,
          cooldownUntil: s.cooldownUntil > t ? s.cooldownUntil : null,
        }];
      })),
    };
  }
}
