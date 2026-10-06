import { loadConfig } from './config.js';
import { openDb } from './db.js';
import { virusTotal } from './providers/virustotal.js';
import { metaDefender } from './providers/metadefender.js';
import { ReputationService } from './service.js';
import { createApp } from './server.js';

const config = loadConfig();
const providers = [
  virusTotal({ apiKey: config.vtKey, minGapMs: config.vtMinGapMs }),
  metaDefender({ apiKey: config.mdKey, minGapMs: config.mdMinGapMs }),
];
if (!providers.some((p) => p.configured)) {
  console.warn('[aviso] Sin VT_API_KEY ni MD_API_KEY: todo hash nuevo se respondera "unavailable".');
}
if (config.appTokens.length === 0) console.warn('[aviso] APP_TOKENS vacio: API abierta (solo desarrollo).');

const db = openDb(config.dbPath);
// Los logs no incluyen hashes: la lista de apps de un usuario es dato personal.
const log = (...a) => console.log(new Date().toISOString(), ...a);
const service = new ReputationService({ db, providers, ...config, log });
const server = createApp({ service, config });

service.start();
server.listen(config.port, () => log(`escuchando en :${config.port}`));

const shutdown = () => { service.stop(); server.close(() => { db.close(); process.exit(0); }); };
process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);
