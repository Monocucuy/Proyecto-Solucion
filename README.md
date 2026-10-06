# Proyecto Solución — Android Device Scanner

App Android (Kotlin + Jetpack Compose) que revisa el celular y entrega un puntaje de salud:

- **Seguridad:** apps instaladas por hash SHA-256 contra VirusTotal + heurísticas locales (permisos de riesgo, origen de instalación).
- **Hardware:** batería, almacenamiento, RAM, estado térmico, sensores (solo APIs públicas, sin root).
- **Sistema:** versión de Android, parche de seguridad, bloqueo de pantalla, depuración USB.

Documento de producto: [`docs/MVP.md`](docs/MVP.md)

Backend opcional de reputación (cache compartido + cola con límite de tasa): [`backend/`](backend/README.md).
En **Ajustes** puedes poner su URL y token; sin URL la app consulta VirusTotal directo con tu clave.
Pendiente de verificar con claves reales y en Android Studio: [`docs/HANDOFF-LOCAL.md`](docs/HANDOFF-LOCAL.md)

## Cómo correrlo

1. Abre la carpeta en **Android Studio** (Ladybug o más nuevo, JDK 17). Deja que sincronice Gradle.
2. Ejecuta en un celular físico o emulador con API 26+.
3. En la app: **Ajustes** → pega tu clave gratuita de https://www.virustotal.com (perfil → API key).
4. Toca **Escanear**.

Sin clave, la app corre hardware, sistema y heurísticas locales; solo se omite la reputación por hash.

## Notas

- Solo se envía el **hash** de cada APK. Ningún archivo sale del dispositivo.
- La clave gratuita de VirusTotal permite ~4 consultas/min: el primer escaneo con muchas apps es lento; lo consultado queda en cache 7 días.
- Un "sin datos" de VirusTotal **no** significa app limpia.
- La clave se guarda con `EncryptedSharedPreferences`. No la subas al repo.
- `QUERY_ALL_PACKAGES` está restringido en Google Play; por ahora distribuye por APK.
- Fuera del MVP: root, protección en tiempo real, eliminación automática de malware.

## Estructura

```
app/src/main/java/com/monocucuy/solucion/
 ├─ App.kt, MainActivity.kt
 ├─ domain/   Models.kt
 ├─ data/     local (Room) · remote (Retrofit/VirusTotal) · repo
 ├─ scan/     AppScanner · HardwareChecker · SystemChecker
 └─ ui/       ScanViewModel · Screens · SettingsStore
```
