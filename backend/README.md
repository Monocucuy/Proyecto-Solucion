# Backend de reputación (Proyecto Solución)

Servicio que la app Android usa en vez de llamar a VirusTotal directamente. Cumple el punto *"Backend propio para
agregar reputación y evitar límites por usuario"* de `docs/MVP.md §13`.

- **Solo recibe hashes SHA-256.** No hay endpoint para subir archivos, y los campos extra del body se ignoran.
- **Cache compartido (SQLite, 7 días):** si un usuario ya consultó un hash, los demás salen del cache y no gastan cuota.
- **Cola persistente + un worker** que respeta el ritmo de cada proveedor (VirusTotal ≈ 4/min en clave gratuita).
- **VirusTotal primero, MetaDefender de respaldo / segunda opinión.** Un 429 pone al proveedor en cooldown; un 401/403
  lo deshabilita 1 h; si ninguno responde, el hash se marca `unavailable` (no se queda colgado).
- **Cero dependencias** (Node ≥ 22.13: `node:http`, `node:sqlite`, `node:test`).

## Correr

```bash
cp .env.example .env   # rellena VT_API_KEY y/o MD_API_KEY, y APP_TOKENS
set -a; . ./.env; set +a
npm start
npm test
```

Variables: ver `.env.example` y `src/config.js` (`CACHE_TTL_DAYS`, `MAX_BATCH`, `REQ_PER_MIN`, `VT_MIN_GAP_MS`, …).

## API

Todas las rutas `/v1/*` exigen `Authorization: Bearer <token>` si `APP_TOKENS` está definido.

### `POST /v1/reputation/batch`
```json
{ "hashes": ["<sha256>", "..."] }          // 1..100, hex de 64 chars (mayúsculas se normalizan)
```
```json
{ "pending": 1,
  "results": {
    "<sha256>": { "status": "done", "verdict": "MALICIOUS", "found": true,
                  "malicious": 62, "suspicious": 0, "source": "virustotal", "checkedAt": 1759780000000 },
    "<sha256>": { "status": "pending" },
    "<sha256>": { "status": "unavailable", "verdict": "UNKNOWN", "error": "upstream_error" }
  } }
```
- `status: "pending"` → la app vuelve a preguntar en unos segundos (polling) hasta que `pending == 0`.
- `verdict` usa los mismos valores y reglas que `domain/Models.kt` (`CLEAN | SUSPICIOUS | MALICIOUS | UNKNOWN`;
  ≥3 motores maliciosos = `MALICIOUS`). **Hash no encontrado = `UNKNOWN`, nunca `CLEAN`.**
- `unavailable.error`: `no_provider`, `upstream_error`, `timeout`, `queue_full`. Tratar como `UNKNOWN`; se puede
  reintentar pasados ~10 min.

### `GET /v1/reputation/{sha256}` — igual, para un solo hash.
### `GET /health` — sin auth; estado de la cola y de los proveedores (sin claves).

Errores: `400` (`invalid_json`, `hashes_required`, `invalid_hash`, `batch_too_large`), `401`, `413`, `429` (con `Retry-After`).

## Límites honestos

- **`APP_TOKENS` embebido en el APK se puede extraer.** Frena bots casuales, no a alguien decidido. El límite por IP
  (`REQ_PER_MIN`) y `MAX_QUEUE` acotan el daño a tu cuota; para algo más serio hace falta Play Integrity (requiere
  validar el veredicto en este backend; no está implementado).
- **El cuello de botella es la cuota de VirusTotal**, no el servidor: con clave gratuita (~500/día, uso no comercial)
  el backend te ahorra consultas repetidas pero no hace magia con hashes que nadie vio antes.
- El parseo de MetaDefender está escrito según su documentación pública y probado con respuestas simuladas; **no está
  verificado contra la API real** (VirusTotal tampoco: los tests usan servidores falsos). Haz una consulta real con tu
  clave antes de confiar en él.
- Un solo proceso/worker (SQLite local). Para varias réplicas hay que cambiar la cola a Postgres/Redis.
- Los logs no incluyen hashes (la lista de apps de alguien es dato personal).
