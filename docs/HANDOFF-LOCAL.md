# Traspaso a local: lo que falta verificar con VirusTotal real y Android real

La sesión en la nube **no tenía claves de VirusTotal/MetaDefender ni Android SDK**. Todo lo de abajo está escrito y
probado contra servidores falsos, pero **nunca contra los servicios reales ni compilado como app Android**.

## Estado verificado (en la nube)
| Qué | Cómo | Resultado |
|---|---|---|
| Backend (`backend/`) | `cd backend && npm test` | 52/52 |
| Cliente Kotlin (`BackendSource`, `DirectSource`) | 19 tests JUnit en `app/src/test` compilados en una JVM aparte (con stubs de las anotaciones de Room) | 19/19 |
| Cliente Retrofit real ↔ backend Node real ↔ VirusTotal falso | prueba e2e temporal (lotes, sondeo, caché compartido, token malo, servidor caído) | 3/3 |

## Sin verificar: tu trabajo en local

### 1. VirusTotal real contra el backend (prioridad 1)
```bash
cd backend
cp .env.example .env        # VT_API_KEY=<tu clave gratuita>, APP_TOKENS=<token cualquiera>
set -a; . ./.env; set +a; npm start

H=275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f   # SHA-256 de eicar.com
curl -s -X POST localhost:8080/v1/reputation/batch -H "Authorization: Bearer <token>" \
     -H 'content-type: application/json' -d "{\"hashes\":[\"$H\"]}"
# repetir cada ~15 s: debe pasar de "pending" a {"status":"done","verdict":"MALICIOUS",...}
```
Qué comprobar y qué puede estar mal (escrito de memoria de la doc de VT, nunca ejecutado):
- [ ] El JSON real de `GET /api/v3/files/{hash}` trae `data.attributes.last_analysis_stats` con
      `malicious/suspicious/undetected/harmless` (`backend/src/providers/virustotal.js`).
- [ ] Un hash que VT no conoce responde 404 → el backend lo reporta `UNKNOWN`, `found:false`.
- [ ] Un 429 real activa el cooldown (mira `GET /health` → `cooldownUntil`) y NO se pierde el hash.
- [ ] Un hash inventado (`1111…`) da `UNKNOWN`, nunca `CLEAN`.
- [ ] Repetir la misma consulta no gasta cuota: segunda vez sale del caché (`source`, `checkedAt`).
- [ ] El ritmo real: 15 s entre consultas (`VT_MIN_GAP_MS`) respeta tu cuota sin generar 429s constantes.

### 2. MetaDefender (opcional, el menos fiable)
Pon `MD_API_KEY` y fuerza el respaldo (p. ej. `VT_API_KEY` inválida → 401 → VT queda deshabilitado una hora).
Confirma que `GET https://api.metadefender.com/v4/hash/{sha256}` responde con `scan_results.total_detected_avs` /
`total_avs` y cómo responde para un hash desconocido (`backend/src/providers/metadefender.js` asume 404 **o** 200 con
`error`).

### 3. Compilar y probar la app en Android Studio
Nada de esto se pudo compilar en la nube. Archivos tocados que dependen de Android/Compose/Room:
`App.kt`, `scan/AppScanner.kt`, `ui/Screens.kt`, `ui/SettingsStore.kt`, `ui/ScanViewModel.kt`,
`AndroidManifest.xml`, `res/xml/network_security_config.xml`, `data/local/HashCache.kt` (+ `Db.kt` recortado).
- [ ] Sync de Gradle + `./gradlew :app:testDebugUnitTest` (los 19 tests; si falla algo de coroutines-test, revisa
      la versión `1.8.1` en `app/build.gradle.kts`).
- [ ] Emulador: `npm start` en el PC; en Ajustes URL = `http://10.0.2.2:8080`, token = el de `APP_TOKENS`.
      Escanear → ver progreso "Consultando reputación…" y el reporte. (HTTP plano solo está permitido para `10.0.2.2`.)
- [ ] Celular físico: necesita HTTPS (o agregar tu IP LAN a `network_security_config.xml`).
- [ ] Sin URL pero con clave en Ajustes → modo VirusTotal directo (comportamiento anterior).
- [ ] Sin nada → solo heurísticas locales + aviso "Sin servicio de reputación".
- [ ] Token mal puesto → hallazgo "El servidor rechazó el token". Servidor apagado → "Sin conexión…".
- [ ] Criterio del MVP "detecta EICAR como APK": un APK que *contiene* EICAR tiene un hash distinto al de
      `eicar.com`; hay que construirlo y esperar a que VT lo conozca (puede dar `UNKNOWN`: no hay garantía).

## Decisiones tomadas que podrías querer revisar
- Si hay URL de servidor, **gana sobre** la clave de VirusTotal directa (no hay fallback automático entre modos).
- La app espera como máximo **2 min** a que el servidor termine; lo que falte sale como "consulta incompleta" y el
  servidor sigue trabajando, así que reescanear en unos minutos completa el resto. Con clave gratuita (15 s/hash) un
  primer escaneo de ~50 apps sin caché tarda ~12 min en total.
- Cambié `AppScanner`: un APK ilegible ya no tumba el escaneo (cuenta como "sin datos"), y una clave inválida corta
  en la primera app en vez de esperar 15 s por cada una.
- El token del servidor va dentro de la app (cifrado en el teléfono, pero extraíble del APK si lo embebes):
  ver "Límites honestos" en `backend/README.md`.
