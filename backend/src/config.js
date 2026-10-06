const int = (v, d) => (v !== undefined && v !== '' && Number.isFinite(+v) ? +v : d);

export function loadConfig(env = process.env) {
  return {
    port: int(env.PORT, 8080),
    dbPath: env.DB_PATH || './data/reputation.db',
    appTokens: (env.APP_TOKENS || '').split(',').map((s) => s.trim()).filter(Boolean),
    trustProxy: env.TRUST_PROXY === '1',
    vtKey: env.VT_API_KEY || '',
    mdKey: env.MD_API_KEY || '',
    ttlMs: int(env.CACHE_TTL_DAYS, 7) * 24 * 60 * 60 * 1000,
    failTtlMs: int(env.FAIL_TTL_MINUTES, 10) * 60 * 1000,
    queueMaxAgeMs: int(env.QUEUE_MAX_AGE_MINUTES, 60) * 60 * 1000,
    maxQueue: int(env.MAX_QUEUE, 5000),
    maxBatch: int(env.MAX_BATCH, 100),
    reqPerMin: int(env.REQ_PER_MIN, 60),
    vtMinGapMs: int(env.VT_MIN_GAP_MS, 15_000), // clave gratuita ~4/min
    mdMinGapMs: int(env.MD_MIN_GAP_MS, 2_000),
  };
}
