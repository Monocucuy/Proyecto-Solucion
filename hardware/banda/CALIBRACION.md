# Calibración de la compuerta

Fecha: 17-nov-2026. Estado: los ángulos y la retención se cambiaron en el código el 17-nov-2026. El firmware con esos valores **no se ha cargado en la placa** y no se probó en la banda **[NO VERIFICADO]**.

## Resultado

| Constante (`banda_arduino.ino`) | Valor actual | Valor anterior | Para qué |
|---|---|---|---|
| `ANG_CERRADA` | 0° | 0° | Compuerta cerrada: el brazo cruza la banda y detiene el celular |
| `ANG_REVISION` | 33° | 45° | Orden `R`: abertura corta; la banda empuja el celular de lado (revisión humana) |
| `ANG_ABIERTA` | 78° | 180° | Orden `A`: abertura grande; el brazo queda casi pegado al borde y el celular sigue derecho |
| `PASO_MS` | 3000 ms (3 s) | 1000 ms (1 s) | Tiempo que la compuerta sigue abierta después de que S1 se suelta |
| `MAX_ABIERTA_MS` | 10000 ms (10 s) | sin cambio | Si S1 no se suelta, la compuerta cierra igual a los 10 s |

Los valores de 78° y 33° se **midieron de fotos** el 17-nov-2026 (foto de la compuerta abierta y foto de la compuerta en revisión). Con 180° el brazo se pasaba de largo. El firmware no se recompiló con estos valores.

## Cómo se mide

Esto es un procedimiento propuesto. Del 17-nov-2026 solo se tiene la medición sobre fotos (pasos 1 y 2).

1. Poner la compuerta en cada posición (cerrada, abierta, revisión) y tomar una foto desde arriba, con el celular paralelo a la mesa.
2. En cada foto, medir con transportador el ángulo entre el brazo y su posición cerrada (0°).
3. Anotar los ángulos en las constantes `ANG_REVISION` y `ANG_ABIERTA`.
4. Recompilar y cargar el Arduino (quitar antes el cable de D0; ver [README.md](README.md)).
5. Probar con el celular de prueba (≈ 300 g) y mandar `A` y luego `R`. Si queda corto o largo, mover **3 a 5 grados** y repetir (es la regla del comentario del firmware).
6. Cuando el ángulo se vea bien, repetir varias pasadas por orden. El informe de diseño inicial propone 20 pasadas por veredicto **[pendiente: no se ha hecho]**.

## Ajustes según lo que se ve (propuestos, sin probar)

| Síntoma | Qué ajustar |
|---|---|
| El celular choca con el brazo al pasar con `A` | Bajar `ANG_ABIERTA` unos grados |
| Con `R` el celular no se desvía | Subir `ANG_REVISION` unos grados |
| Con `R` el celular se desvía demasiado o se traba | Bajar `ANG_REVISION` unos grados |
| El brazo cerrado no cruza toda la banda | No es de firmware: mover la pieza de la viga Technic en el eje del servo |
| La compuerta cierra con el celular todavía pasando | Subir `PASO_MS`; depende de la velocidad de la banda, que **no se midió** |
| La banda va hacia el lado contrario | Intercambiar los dos cables del N20; `AVANZA` no tiene efecto sin driver |

## Qué falta medir

- Velocidad de la banda: no se midió; el equipo la describe como "lentica, pero se defiende". Se puede estimar con el video del 17-nov-2026. Con ella se puede ajustar `PASO_MS` con un dato.
- Si los 78° y los 33° funcionan con la banda en marcha y celular real: **[NO VERIFICADO]**.
- Repetibilidad del servo y fuerza que ejerce sobre el celular: no se midieron.
