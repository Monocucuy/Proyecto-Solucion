# Imágenes y PDF de la banda

Fecha: 17-nov-2026. Estado: esta carpeta **solo tiene este archivo**. Las imágenes y el PDF se copian después; esta es la lista de lo que debe llegar. Lo que no exista no se inventa: si falta una foto, se deja la fila en "pendiente".

## Informe

| Archivo | Qué es | Estado |
|---|---|---|
| `Informe_Tecnico_Final_Banda_Clasificadora.pdf` | Informe técnico final (PDF, APA 7) | Pendiente |

El workflow de la release busca el PDF primero en `docs/banda/` (raíz del repositorio) y, si no está, en esta carpeta (`hardware/banda/docs/`). Basta con que esté en uno de los dos.

## Fotos del prototipo (17-nov-2026)

Origen: fotos subidas por el equipo el 17-nov-2026 (archivos `.webp`). El nombre final en el repositorio se define al copiarlas.

| Foto (id de origen) | Qué muestra | Estado |
|---|---|---|
| `1093b976` | Compuerta, vista general, cerrada | Copiar |
| `6b942fe3` | Compuerta, detalle, cerrada (la misma imagen aparece como `dd527064`) | Copiar una sola vez |
| `9fbac858` | Compuerta abierta a 78° (repetida como `cd1ba775`) | Copiar una sola vez |
| `93791a5c` | Compuerta en revisión, 33° (repetida como `c38ec1e8`) | Copiar una sola vez |
| Otras 9 fotos del 17-nov (`fc6d49cb`, `b1759183`, `8e99ce97`, `273c3ebe`, `4c6efabb`, `235d5836`, `79af4c8d`, `93790e3e`, `5e5920ea`) | Sin descripción verificada | Revisar una por una antes de copiar |
| `ba252221` | N20 con L293D y un rodillo de prueba sobre protoboard: **versión anterior** | Copiar solo con la etiqueta "versión anterior (L293D)" |
| `5401665a` | Banda con tela sobre la estructura Lego, junto al Arduino: **versión anterior** (beta básica) | Copiar solo con la etiqueta "versión anterior"; se ve una mano con pulsera: recortar |

Nota: el equipo dijo que todas eran del 17-nov, pero `ba252221` y `5401665a` muestran versiones anteriores. La fecha del archivo (17-nov 03:44) es la de la subida, no la de la foto **[NO VERIFICADO]**.

## Imágenes que ya existen en la carpeta de trabajo

| Archivo | Qué es | Cómo etiquetarlo |
|---|---|---|
| `esquema_l293d.png` | Esquema de conexión del L293D | **Histórico**: el chip se quemó y se descartó |
| `banda_switches_posicion.jpg` | Foto cenital con S1, S2, servo y motor marcados (archivo del 14-nov-2026) | **Versión anterior**: S1 aparece después del servo y hay cajas OK y REVISIÓN; la posición final de S1 es ≈ 4 cm antes del servo. Se ven piernas y zapatos de una persona: recortar |
| `resistencias_marcadas.jpg` | Resistencias numeradas con su valor (220 Ω, 680 Ω, 1 kΩ y dos sin identificar) | Apoyo para el cableado; no muestra 510 Ω ni 100 Ω |

## Por generar (todavía no existen)

| Qué | Cantidad | Notas |
|---|---|---|
| Renders del modelo 3D actualizado (medidas reales y MG90S) | 6 | Baja calidad, renderizados en este PC |
| Diagramas y esquemas (conexión, bloques, alimentación) | por definir | Salen del informe |
| Plano 2D con medidas | 1 | Salen del informe |
| Fotogramas del video del 13-nov-2026 (beta, 19:00) y del 17-nov-2026 (prueba con celular real, 03:21) | por definir | Evidencia; los videos originales no se suben |
| Video de 10 s a 1080p y 60 fps | 1 | Se renderiza en otro computador; **no va en esta carpeta** |

## Reglas

- Una imagen por archivo, con nombre en minúsculas, sin espacios, y con la fecha o la versión si no es del prototipo final.
- Quitar de las fotos a las personas y lo que no sea del proyecto (recortar o difuminar) antes de subirlas.
- Cada imagen se cita en el informe con su pie de figura; si una foto no está aquí, el informe no la usa.
- La carpeta `hardware/banda/` completa se comprime en `firmware-banda-early-access.zip` al publicar la release: lo que se copie aquí viaja en el zip.
