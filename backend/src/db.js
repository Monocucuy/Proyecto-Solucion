import { DatabaseSync } from 'node:sqlite';
import { mkdirSync } from 'node:fs';
import { dirname } from 'node:path';

export function openDb(path) {
  if (path !== ':memory:') mkdirSync(dirname(path), { recursive: true });
  const db = new DatabaseSync(path);
  db.exec(`
    PRAGMA journal_mode = WAL;
    CREATE TABLE IF NOT EXISTS cache (
      hash TEXT PRIMARY KEY, found INTEGER NOT NULL, malicious INTEGER NOT NULL,
      suspicious INTEGER NOT NULL, total INTEGER NOT NULL, source TEXT NOT NULL,
      checked_at INTEGER NOT NULL
    );
    CREATE TABLE IF NOT EXISTS queue (
      hash TEXT PRIMARY KEY, enqueued_at INTEGER NOT NULL,
      attempts INTEGER NOT NULL DEFAULT 0, next_attempt_at INTEGER NOT NULL
    );
    CREATE TABLE IF NOT EXISTS unavailable (
      hash TEXT PRIMARY KEY, until INTEGER NOT NULL, reason TEXT NOT NULL
    );
  `);
  const q = (sql) => db.prepare(sql);
  const st = {
    getCache: q('SELECT * FROM cache WHERE hash = ?'),
    putCache: q(`INSERT INTO cache (hash, found, malicious, suspicious, total, source, checked_at)
                 VALUES (?, ?, ?, ?, ?, ?, ?)
                 ON CONFLICT(hash) DO UPDATE SET found=excluded.found, malicious=excluded.malicious,
                   suspicious=excluded.suspicious, total=excluded.total, source=excluded.source,
                   checked_at=excluded.checked_at`),
    getQueued: q('SELECT * FROM queue WHERE hash = ?'),
    enqueue: q('INSERT OR IGNORE INTO queue (hash, enqueued_at, attempts, next_attempt_at) VALUES (?, ?, 0, ?)'),
    dequeue: q('DELETE FROM queue WHERE hash = ?'),
    queueSize: q('SELECT COUNT(*) AS n FROM queue'),
    nextDue: q('SELECT * FROM queue WHERE next_attempt_at <= ? ORDER BY enqueued_at LIMIT 1'),
    earliest: q('SELECT MIN(next_attempt_at) AS t FROM queue'),
    expired: q('SELECT hash FROM queue WHERE enqueued_at < ?'),
    retryLater: q('UPDATE queue SET attempts = ?, next_attempt_at = ? WHERE hash = ?'),
    deferTo: q('UPDATE queue SET next_attempt_at = ? WHERE hash = ?'),
    getUnavail: q('SELECT * FROM unavailable WHERE hash = ?'),
    putUnavail: q(`INSERT INTO unavailable (hash, until, reason) VALUES (?, ?, ?)
                   ON CONFLICT(hash) DO UPDATE SET until=excluded.until, reason=excluded.reason`),
    purge: q('DELETE FROM unavailable WHERE until < ?'),
  };
  return {
    raw: db,
    close: () => db.close(),
    getCache: (h) => st.getCache.get(h),
    putCache: (h, r, source, now) =>
      st.putCache.run(h, r.found ? 1 : 0, r.malicious, r.suspicious, r.total, source, now),
    isQueued: (h) => !!st.getQueued.get(h),
    enqueue: (h, now) => st.enqueue.run(h, now, now),
    dequeue: (h) => st.dequeue.run(h),
    queueSize: () => st.queueSize.get().n,
    nextDue: (now) => st.nextDue.get(now),
    earliestDue: () => st.earliest.get().t,
    expiredBefore: (t) => st.expired.all(t).map((r) => r.hash),
    retryLater: (h, attempts, at) => st.retryLater.run(attempts, at, h),
    deferTo: (h, at) => st.deferTo.run(at, h),
    getUnavailable: (h) => st.getUnavail.get(h),
    putUnavailable: (h, until, reason) => st.putUnavail.run(h, until, reason),
    purgeUnavailable: (now) => st.purge.run(now),
  };
}
