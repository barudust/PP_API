# Plan — Fase 16: Módulo Listas gráfico (plantillas Agromas/Api-Aba con precios del portal)

> ✅ **IMPLEMENTADA Y VERIFICADA (2026-07-17).** Las 8 decisiones de §6 se
> confirmaron con el dueño en el chat, y después pidió explícitamente
> empezar a programar ("empieza a programar la fase 16 has todo tu como te
> dije"). Detalle real de lo construido (que en algunos puntos se desvía de
> lo que este documento proponía, con la razón documentada) en
> `EMPEZAR_AQUI.md` §5h, `CHANGELOG.md` ("Fase 16") y `MEMORIA.md`
> (ADR-026, ADR-027). Este documento queda como registro del análisis y las
> decisiones — no lo tomes como la fuente de verdad de qué se construyó,
> para eso están los tres documentos anteriores.

Fecha de redacción: **2026-07-17**. Estado: **COMPLETADA.**
Prerequisito ya cumplido: la Fase 15 (especies/categorías + clasificación)
está verificada — esta fase se apoya en esa clasificación.

---

## 0. Qué pidió el dueño (en sus palabras)

> "quiero que actualices los documentos de md y hagas el plan para poder
> cambiar el modulo de listas de forma grafica, osea que se tomen los exceles
> que hay en `PP_API/ejemplos_importacion` y se dupliquen lista api-aba y
> lista agromas con esos estilos y colores y se llenen automaticamente con los
> precios del portal, si en el portal no sale alguno con precio pues que se
> deje vacio, haz el analisis y llena los md"

Traducción a requisitos:
1. El módulo **Listas** (`/listas`) debe volverse **gráfico** — reproducir el
   look de las listas de precios que el dueño ya usa (los Excel de
   `ejemplos_importacion/`), no la tabla plana actual.
2. Como mínimo **Agromas** y **Api-Aba**, cada una con **sus estilos y colores**.
3. Los **precios se llenan automáticamente** con los del catálogo del sistema
   ("el portal").
4. Si un producto de la lista **no tiene precio en el portal, la celda queda
   vacía** (no se inventa ni se oculta la fila).

---

## 1. Análisis de las plantillas Excel (anatomía exacta)

Archivos fuente (⚠️ en `.gitignore` — traen datos reales del negocio, no se
versionan): `ejemplos_importacion/Lista Agromas.xlsx` y
`ejemplos_importacion/Lista Api-Aba.xlsx`.

**No son tablas** — son un **catálogo tipo menú a dos columnas (paneles)**.
Estructura idéntica en ambos archivos, cambiando solo el color de marca:

### 1.1 Rejilla y estilos (verificado celda por celda con openpyxl)
- **Título**: `A1:H2` combinado, texto de marca centrado, **Calibri 26** (Agromas
  sin negrita, Api-Aba negrita), relleno con el color de acento de la marca a
  tono pleno.
- **Dos paneles lado a lado**:
  - Panel izquierdo: columnas **A–D**. Nombre de producto en **`A{fila}:B{fila}`
    combinado** (centrado, Calibri 11); **precio en `C{fila}`** (celda con
    borde de caja, **vacía en la plantilla**); `D{fila}` es separador con borde.
  - Panel derecho: columnas **E–H**. Nombre en **`E{fila}:F{fila}` combinado**;
    **precio en `G{fila}`**; `H{fila}` separador.
- **Encabezado de sección/especie** (ej. "Cerdos", "Ovinos", "Gallos",
  "Pavos", "Aves de postura", "Ganado de engorda", "Ganado lechero"…):
  combinado a lo ancho del panel (`A:D` o `E:H`), **Calibri 16 negrita**,
  relleno color de marca **tint 0.4** (más claro), alto de fila 20.1.
- **Sub-encabezado de línea** (solo Agromas — ej. "Linea suprema", "Linea
  Optima", "Linea Esencial"): **Calibri 11 negrita**, relleno color de marca
  **tint 0.8** (mucho más claro).
- **Filas de producto**: Calibri 11 normal, alto 15, con bordes de caja.
- Anchos de columna aprox.: A≈15, B≈15, C≈11 (y el espejo E/F/G).

### 1.2 Colores (tema estándar de Office en ambos libros)
- **Agromas** → acento 2 = **naranja `#ED7D31`**.
- **Api-Aba** → acento 6 = **verde `#70AD47`**.
- Tonos derivados: secciones = color a **tint 0.4**, líneas (Agromas) = **tint
  0.8**, título = color pleno.

### 1.3 Hojas y volumen
- **Agromas**: 1 hoja (`Hoja1`), ~90 nombres de producto en ~11 secciones de
  especie, varias con sub-líneas.
- **Api-Aba**: **3 hojas** (`Hoja1`, `Hoja2`, `Vimifos`) — más productos,
  probablemente separadas por proveedor/línea (Vimifos es una marca de
  vacunas/aditivos que Api-Aba distribuye).

### 1.4 Dato clave
En las plantillas **la columna de precio está vacía** — son formatos en blanco
que el dueño llena a mano cada vez que cambian precios. **Automatizar ese
llenado es exactamente lo que pide esta fase.**

---

## 2. Estado actual del módulo Listas y del modelo de datos

### 2.1 Frontend — `punto-peludo-web/src/pages/ListasPage.tsx`
- Hoy: **tabla plana agrupada por marca** (Producto · Presentación · Precio),
  usa `precio_base`. Botones "Exportar Excel" e "Imprimir / PDF" (este último
  reusa el patrón `.printable`).
- No tiene noción de especie/categoría ni de layout de dos paneles ni colores
  de marca.

### 2.2 Backend — export actual
- `GET /productos/exportar/excel` (`app/routers/productos.py`) arma
  `[Marca, Producto, Presentación, Precio]` y lo pasa a
  `generar_excel()` (`app/services/export_service.py`).
- `generar_excel()` es **genérico**: encabezado en negrita + auto-ancho.
  **No reproduce estilos, colores, combinadas ni secciones.** Sirve para
  reportes, no para replicar una plantilla de marca.

### 2.3 Modelo de datos disponible (`app/models/producto.py`)
Campos útiles por producto: `nombre`, `sku` (código de proveedor capturado en
importación), `codigo_barras`, `precio_base`, `precio_granel`, `contenido_neto`,
`unidad_medida`, `marca_id`, **`especie_id`**, **`categoria_id`**,
**`subcategoria_id`** (estos 3 ya poblados para 22/26 Agromas tras Fase 15).

### 2.4 El hueco central (el problema real a resolver)
Los **nombres del catálogo** vienen de la importación del distribuidor y son
largos/técnicos: `POLLO ENGORDA CP 25 kg`, `BOVIMAS ENGORDA OPTIMA 15 MP 25 kg`,
`MAS LECHON PRE-INICIADOR 1`. Los **nombres de la plantilla** son la taquigrafía
del dueño: `Pollo Engorda`, `Bovimas Engorda Optima 15%`, `Mas Lechon 1`.
**No coinciden literalmente**, así que llenar el precio de cada renglón de la
plantilla exige **vincular renglón-de-plantilla ↔ producto-del-catálogo**, y eso
no es trivial ni 100% automático. Es la decisión central de §3/§6.

Además, hoy el catálogo tiene **26 productos Agromas y 0 Api-Aba** confirmados,
contra ~90 y ~cientos de renglones en las plantillas → **la mayoría de las
celdas de precio nacerán vacías**. Eso es consistente con lo que pidió el dueño
("si no sale con precio, se deja vacío"), pero conviene que lo tenga presente:
al principio la lista se verá mayormente en blanco y se irá llenando conforme
el catálogo real crezca.

---

## 3. Decisión de diseño central (y recomendación)

Hay dos formas de construir esto. **Cambian todo el resto del plan**, por eso
es la primera pregunta de §6.

### Enfoque A — Plantilla fiel (RECOMENDADO, es lo que el dueño describió)
La estructura y los nombres salen de **los Excel** (se "duplican"). El sistema
solo **rellena la columna de precio** buscando el producto correspondiente en
el catálogo. Si no lo encuentra o no tiene precio → celda vacía.
- ✅ Reproduce exactamente la lista que el dueño ya conoce y reparte.
- ✅ "Se deja vacío si no hay precio" encaja naturalmente.
- ⚠️ Requiere resolver el vínculo renglón↔producto (ver §4.2).
- ⚠️ Si el dueño agrega un producto nuevo a su catálogo real que no está en la
  plantilla, no aparece en la lista hasta actualizar la plantilla.

### Enfoque B — Catálogo dinámico con estilo de marca
La estructura se **genera desde el catálogo**: agrupar los productos reales por
**especie → categoría** (que ya existen tras Fase 15) y pintarlos con los
colores de la marca, imitando el estilo de la plantilla.
- ✅ No hay problema de matching: cada fila ES un producto real con su precio.
- ✅ Se mantiene solo (crece con el catálogo).
- ⚠️ **No reproduce la plantilla** del dueño (orden, nombres, secciones como
  "Mi patio", "Bultitos", "Vimifos" que son agrupaciones comerciales, no
  especies). No muestra productos que el dueño vende pero aún no captura.

**Recomendación:** empezar con **A** para las 2 marcas que el dueño pidió
(reproduce su formato), y dejar **B como fallback** para marcas sin plantilla
(hoy la tabla plana actual).

> ✅ **Confirmado por el dueño (2026-07-17): Enfoque A**, con una precisión
> importante que no estaba en el análisis original: **`Lista Agromas.xlsx` /
> `Lista Api-Aba.xlsx` no son solo un formato de impresión — son la fuente de
> verdad de qué productos se venden realmente.** El dueño explícitamente dijo
> que el lote "Formato de pedidos" (94 líneas, todavía en `revisión`) **trae
> más productos de los que en realidad se venden**, y que todos los productos
> Agromas del catálogo — vengan del XML, del Excel "Formato de pedidos", o de
> la propia Lista Agromas — **se deben acoplar a los nombres de Lista
> Agromas**, porque esa es la lista real de venta. Ver §6.2 y §6.8 para el
> detalle operativo.

---

## 4. Enfoque propuesto en detalle (asumiendo A; ajustar según §6)

### 4.1 Representar la plantilla como dato
Parsear una sola vez cada Excel de `ejemplos_importacion/` a una estructura
versionable (JSON o tabla nueva `lista_plantilla`/`lista_plantilla_fila`), del
estilo:
```
Marca: Agromas  (color #ED7D31)
  Hoja/columna izquierda:
    Sección "Cerdos"
      Línea "Linea suprema"
        Fila "Mas Lechon 0"
        Fila "Mas Lechon 1"
        ...
    Sección "Pollos de engorda"
      Fila "Pollo Inicio"
      ...
```
Guardar el orden, a qué panel/columna va cada cosa, y el tipo de fila
(sección / línea / producto). Así el render y el export no dependen de re-leer
el .xlsx en runtime.

### 4.2 Vincular fila de plantilla ↔ producto del catálogo (el corazón)

> ✅ **Confirmado por el dueño (2026-07-17): opción (d), alineación en el
> origen — no un algoritmo de matching en runtime.** En vez de resolver el
> vínculo con heurísticas, el dueño va a **ajustar los nombres de producto en
> el origen** para que coincidan exactamente con `Lista Agromas.xlsx` /
> `Lista Api-Aba.xlsx`:
> - El lote "Formato de pedidos" (94 líneas, Agromas, en `revisión`) se ajusta
>   **antes de confirmarlo** para que cada línea use el nombre corto de la
>   plantilla (ej. "Pollo Engorda"), no el nombre técnico largo.
> - Los **26 productos Agromas ya confirmados** (nombres largos tipo "POLLO
>   ENGORDA CP 25 kg", venidos de XML/Formato de pedidos/Lista Agromas en
>   distintos momentos) **se renombran** para acoplarse a `Lista Agromas.xlsx`,
>   porque esa lista es la que refleja lo que realmente se vende.
> - Lo mismo aplica a futuro para Api-Aba: lo que se importe debe terminar con
>   nombres que coincidan con `Lista Api-Aba.xlsx`.
>
> Con los nombres alineados en el origen, el vínculo en runtime se resuelve
> por **coincidencia exacta de `producto.nombre`** (normalizando solo
> mayúsculas/espacios, sin necesidad de heurísticas de similitud) — se guarda
> igual en `lista_plantilla_fila.producto_id` para no tener que re-resolver en
> cada carga, pero la fuente de la verdad es el nombre ya curado.
>
> **Pendiente operativo (no bloquea §6, se resuelve al ejecutar la tarea 3 de
> §5):** el dueño dijo que "Formato de pedidos" trae productos que en
> realidad no se venden. Falta decidir, línea por línea de ese Excel, cuáles
> SÍ corresponden a un renglón real de `Lista Agromas.xlsx` (esas se
> confirman/renombran) y cuáles se ignoran en la importación. Es trabajo de
> revisión de datos, no una decisión de diseño — se hace cuando se trabaje esa
> tarea, con el dueño revisando la vista previa de importación como ya hace
> siempre.
>
> Las opciones (a)/(b)/(c) de abajo quedan como referencia histórica del
> análisis, pero **no se van a implementar** — se documentan por si en el
> futuro hace falta reabrir esta decisión para una marca nueva sin la
> disciplina de nombres ya aplicada.

Opciones consideradas originalmente (descartadas a favor de la alineación en
el origen, ver arriba):
- **(a) Mapa manual una sola vez**: una pantalla/paso donde el dueño (o
  nosotros) asocia cada renglón de plantilla a un producto del catálogo. Más
  trabajo inicial, resultado exacto y estable. El mapa se guarda
  (`lista_plantilla_fila.producto_id`).
- **(b) Match por SKU/código**: si el renglón de la plantilla llega a tener el
  código de proveedor y el producto también (`producto.sku`), enlazar por ahí.
  Hoy las plantillas **no** traen código, así que esto no aplica solo.
- **(c) Match difuso por nombre normalizado**: normalizar (mayúsculas, sin
  acentos, sin tamaños "25 kg", tokens) y sugerir el mejor candidato. Rápido
  pero **aproximado** — sirve como *sugerencia* para acelerar (a), no como
  verdad automática (riesgo de pegar el precio equivocado a un producto).

### 4.3 Resolver precios y regla de vacío
Para cada renglón de producto de la plantilla:
- Si tiene producto vinculado y `precio_base` no nulo → mostrar ese precio.
- Si no tiene vínculo, o el producto no tiene precio → **celda vacía, fila
  visible** (no se oculta la fila — confirmado, ver §6.5).

> ✅ **Confirmado por el dueño (2026-07-17): siempre `precio_base` (precio por
> pieza)**, sin importar si el producto también se vende a granel. No se pidió
> mostrar la presentación (ej. "25 kg") aparte — se mantiene igual que la
> plantilla original, que solo trae nombre + una celda de precio. Si el dueño
> la quiere después, es un ajuste menor de layout, no de datos.

### 4.4 UI gráfica (Listas rediseñado)
- Selector de marca (Agromas / Api-Aba / … ; las que tengan plantilla). Para
  Api-Aba, las 3 hojas (`Hoja1`, `Hoja2`, `Vimifos`) se muestran las 3 —
  confirmado (§6.4) — probablemente como pestañas dentro de la vista de
  Api-Aba.
- **Vista previa fiel**: layout de dos paneles, secciones con el color de la
  marca (naranja Agromas / verde Api-Aba), sub-líneas, y la columna de precio
  llena o vacía. En web se puede lograr con una grilla estilizada (CSS) usando
  el color de marca como variable.
- Botones: **Exportar Excel** (fiel a la plantilla) e **Imprimir / PDF** (reusa
  `.printable`).

> ✅ **Confirmado por el dueño (2026-07-17): la plantilla debe ser editable
> desde la web** (§6.6), no fija. Esto amplía el alcance de esta tarea:
> además del render de solo-lectura descrito arriba, hace falta un CRUD de
> estructura — agregar/quitar/reordenar secciones, líneas y renglones de
> producto dentro de una marca, sin depender de volver a tocar el `.xlsx`
> original. Implica: endpoints `POST/PUT/DELETE` sobre
> `lista_plantilla`/`lista_plantilla_fila` (no solo el `GET` de consulta), y
> una UI de edición (agregar sección, mover fila, vincular/desvincular
> producto) además de la vista de solo lectura. Es trabajo adicional real
> frente al plan original — dimensionar aparte al planear la tarea 6 de §5.

### 4.5 Export Excel fiel
Dos caminos:
- **(i) Copiar el .xlsx plantilla y solo escribir la columna de precio** (con
  `openpyxl load_workbook` sobre una copia de `ejemplos_importacion/*.xlsx`).
  Es lo **más fiel** (conserva estilos/colores/combinadas exactas sin
  reconstruir nada). Contra: depende de tener el archivo plantilla en el
  servidor (hoy están gitignored; habría que decidir dónde viven en
  producción).
- **(ii) Reconstruir el libro con openpyxl** desde la estructura de §4.1
  (aplicando fills de tema, combinadas, bordes). Más código, no depende del
  archivo original, pero hay que replicar los estilos a mano.
- Recomendado: **(i)** por fidelidad; evaluar (ii) si no se quiere depender del
  archivo fuente. `generar_excel()` actual **no** sirve para esto (es tabla
  plana) — habría una función nueva, sin tocar la existente.

> ✅ **Confirmado por el dueño (2026-07-17): opción (i)**, con el archivo
> fuente viviendo en una **carpeta de assets no versionada** en el servidor
> (§6.7) — ej. `PP_API/app/assets/plantillas/`, fuera de git igual que hoy
> vive `ejemplos_importacion/`. Nota: si la plantilla pasa a ser editable
> desde la web (§4.4), esta copia base sigue sirviendo como plantilla de
> estilos (colores, combinadas, bordes) para generar el Excel exportado,
> aunque la estructura de secciones/filas ya no dependa 100% del archivo
> original sino de `lista_plantilla`/`lista_plantilla_fila`.

### 4.6 Marcas sin plantilla
Fallback al comportamiento actual (tabla plana por marca) o al Enfoque B. No se
rompe nada de lo que ya existe.

---

## 5. Tareas en orden (PLAN — nada de esto está hecho)
1. ~~Confirmar §6 con el dueño~~ ✅ **hecho, 2026-07-17** (ver §6). Falta que
   el dueño pida explícitamente empezar a programar — confirmar el plan no
   es lo mismo que autorizar el código, ver advertencia al inicio del
   documento.
2. **Curación de nombres (nuevo, previo a todo lo demás)**: alinear los
   nombres de producto en el catálogo con `Lista Agromas.xlsx` /
   `Lista Api-Aba.xlsx` (§4.2 y §6.8) — renombrar los 26 productos Agromas ya
   confirmados, y revisar línea por línea el lote "Formato de pedidos" (94
   líneas, en `revisión`) para decidir cuáles corresponden a un renglón real
   de la plantilla antes de confirmarlo. Es trabajo de datos con el dueño
   revisando cada cambio (mismo patrón que usa importación hoy), no
   automatizable sin supervisión — bloquea la tarea 4 (sin nombres alineados,
   el matching por nombre exacto no funciona).
3. Parsear las 2 plantillas a la estructura de datos de §4.1 (script de
   extracción, una sola vez) — incluye las 3 hojas de Api-Aba (§6.4).
4. Backend: modelo `lista_plantilla`/`lista_plantilla_fila` +
   resolución del vínculo por nombre exacto contra `producto.nombre` (§4.2).
5. Backend: CRUD de estructura de plantilla (agregar/quitar/reordenar
   secciones y filas) — alcance nuevo por la decisión de plantilla editable
   (§4.4, §6.6), no estaba en el análisis original.
6. Backend: endpoint `GET /listas/plantilla?marca=...` que devuelve la
   estructura + precios resueltos (`precio_base`, §6.3) + huecos vacíos
   visibles (§6.5).
7. Backend: export Excel fiel (§4.5) copiando la plantilla base desde la
   carpeta de assets no versionada (§6.7); función nueva, no tocar
   `generar_excel`.
8. Frontend: rediseño gráfico de `ListasPage.tsx` (dos paneles + colores de
   marca + pestañas para las 3 hojas de Api-Aba + selector + imprimir/PDF),
   con fallback (Enfoque B / tabla plana actual) para marcas sin plantilla.
9. Frontend: UI de edición de estructura (agregar/quitar/reordenar
   sección/línea/fila, vincular/desvincular producto) — consume el CRUD de
   la tarea 5.
10. Pruebas automatizadas + verificación en navegador contra la BD real
    (mismo estándar del proyecto: nada se marca "hecho" sin probarse).
11. Actualizar `CHANGELOG.md` / `MEMORIA.md` (ADR nuevo) / `ROADMAP.md` /
    `EMPEZAR_AQUI.md` con el resultado real.

---

## 6. Decisiones del dueño — ✅ TODAS CONFIRMADAS (2026-07-17)

Registro literal de lo que confirmó el dueño, para que ninguna sesión futura
tenga que volver a preguntar. Detalle de cómo cada una afecta el diseño está
inline en §3/§4 (buscar los bloques `✅ Confirmado`).

1. **Enfoque**: **A** — reproducir fielmente las plantillas Excel. Además, el
   dueño aclaró algo que no estaba en el análisis original: `Lista
   Agromas.xlsx` / `Lista Api-Aba.xlsx` no son solo un formato de impresión,
   son **la lista real de lo que se vende** — tiene más peso que un simple
   layout a reproducir. Ver §3.
2. **Vínculo fila↔producto**: **no** se implementa matching difuso ni mapa
   manual en la app. En vez de eso, el dueño va a **alinear los nombres en el
   origen** — tanto el catálogo ya confirmado como las importaciones
   pendientes/futuras de Agromas y Api-Aba deben usar el nombre corto de la
   plantilla correspondiente. El runtime resuelve por **coincidencia exacta
   de nombre**. Ver §4.2 para el detalle completo, incluye el pendiente
   operativo de qué hacer con las líneas de "Formato de pedidos" que no
   corresponden a ningún renglón de `Lista Agromas.xlsx`.
3. **Precio a mostrar**: **`precio_base` (precio por pieza) siempre**, nunca
   granel, sin columna de presentación aparte. Ver §4.3.
4. **Hojas de Api-Aba**: **las 3** (`Hoja1`, `Hoja2`, `Vimifos`) aparecen en
   la lista. Ver §4.4.
5. **Renglones sin precio**: **se muestran vacíos, la fila queda visible**
   (no se oculta). Ver §4.3.
6. **¿Plantilla fija o editable desde la web?**: **editable** — el dueño
   quiere poder agregar/quitar/reordenar productos y secciones desde la web
   sin depender de volver a tocar el `.xlsx` original. Esto amplía el alcance
   original del plan (agrega un CRUD de estructura, no solo una vista de solo
   lectura) — ver §4.4 y las tareas 5/9 de §5.
7. **Archivo plantilla en producción**: **carpeta de assets no versionada**
   en el servidor (ej. `PP_API/app/assets/plantillas/`), fuera de git. Ver
   §4.5.
8. **(Aclaración adicional, no estaba en la lista original de 7)** Qué hacer
   con los 26 productos Agromas ya confirmados que tienen nombres técnicos
   largos: **se renombran** para acoplarse a `Lista Agromas.xlsx`,
   independientemente de si originalmente vinieron del XML, de "Formato de
   pedidos" o de la propia Lista Agromas — porque esa lista es la fuente de
   verdad de lo que realmente se vende, aunque otras fuentes tengan más
   productos listados. Ver §4.2.

---

## 7. Fuera de alcance (salvo que el dueño lo pida)
- Pulido de branding general (logo, tipografía corporativa) — el dueño dijo
  "eso después".
- Otras marcas fuera de Agromas/Api-Aba (usan el fallback actual).
- Cambiar cómo se capturan/importan los productos (esta fase solo consume
  precios ya existentes; la mejora del importador fue Fase 15).
- Los otros archivos de `ejemplos_importacion/` (`Winners.xlsx`, el Excel de
  pedidos, el CFDI, el PDF) — no forman parte de este pedido.

---

## 8. Recordatorio (anti-repetición del error de Fase 15)
Este documento es **diseño, no implementación**. No hay una sola línea de
código de Fase 16 escrita, ni cambios en la BD. La próxima acción correcta es
**resolver §6 con el dueño**, no empezar a programar.
