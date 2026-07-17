# CHANGELOG — PP_API

> 👉 **¿Sesión nueva? Lee primero [`EMPEZAR_AQUI.md`](EMPEZAR_AQUI.md).**
> Registro de qué se modificó en cada iteración y por qué.
> Formato: [Fecha] — Fase — resumen; luego archivos tocados.

---

## [2026-07-17] — Fase 16: Listas gráfico (Lista Agromas/Api-Aba) — ✅ completada

Implementación completa de `PLAN_FASE16.md` tras confirmar las 8 decisiones
de §6 con el dueño en el mismo chat (registradas en el plan antes de escribir
código, siguiendo el aprendizaje de Fase 15). Alcance real entregado: el
módulo Listas ahora reproduce el layout de dos paneles de `Lista
Agromas.xlsx`/`Lista Api-Aba.xlsx` con los colores de marca, llena los
precios automáticamente desde el catálogo, y **la estructura es editable
desde la web** (decisión §6.6, ampliación real sobre el plan original).

### Backend
- **Nuevo servicio `app/services/lista_plantilla_service.py`**: `parsear_plantilla()`
  lee un `.xlsx` de plantilla y devuelve una lista ordenada de nodos
  (`NodoPlantilla`: hoja/panel/orden/tipo/nivel/texto) — clasifica cada fila
  como encabezado (negrita + relleno de color de marca, nivel derivado del
  tinte) o producto (sin relleno) recorriendo cada panel de arriba a abajo;
  ignora el título de hoja completa (fusión que cruza los dos paneles).
  `resolver_vinculos()` vincula cada fila de producto a un `producto.id` real
  por palabras normalizadas, con dos reglas de seguridad (ver ADR-026 en
  `MEMORIA.md`): toda palabra extra del producto debe explicarse por el
  contexto de encabezados ancestros, y un empate entre candidatos se deja sin
  vincular (nunca adivina) salvo el caso de duplicados exactos (mismo nombre,
  se prefiere el que tiene `sku`).
- **Nueva tabla `lista_plantilla_fila`** (migración `c9d0e1f2a3b4`): fila
  plana con `marca_id, hoja, panel, orden, tipo, nivel, texto, producto_id`
  — modelo de "esquema" (outline) de profundidad libre, no un árbol de tablas
  fijo, para soportar edición (agregar/mover/quitar) sin migraciones nuevas.
- **Nuevo router `app/routers/listas.py`** (prefijo `/listas`):
  - `GET /listas/plantillas-disponibles` — marcas con plantilla configurada
    (hoy Agromas `#ED7D31` / Api-Aba `#70AD47`, ver `LISTA_PLANTILLA_MARCAS`
    en `app/core/constants.py`).
  - `GET /listas/plantilla?marca_id=` — estructura + precio resuelto (join a
    `producto`, solo si `activo=true`) por marca, lectura abierta.
  - `POST /listas/plantilla/importar?marca_id=` — (re)genera toda la
    estructura de una marca desde su `.xlsx` base + re-vincula; permiso
    `catalogo.importar`. Reemplaza cualquier edición manual previa (con aviso
    de confirmación en el frontend).
  - `POST/PUT/DELETE /listas/plantilla-filas[...]` + `POST
    /listas/plantilla-filas/reordenar` — CRUD de estructura, permiso
    `productos.gestionar`.
  - `GET /listas/plantilla/exportar/excel?marca_id=` — Excel fiel al estilo
    de marca, regenerado desde los datos vigentes (ver ADR-027 — se
    reconsideró la opción original del plan de copiar el `.xlsx` fuente,
    porque ya no es fiel una vez que la estructura es editable).
- **`app/services/export_service.py`**: nueva función `generar_excel_plantilla()`
  (no se tocó `generar_excel()` existente).
- **Archivos fuente en `app/assets/plantillas/`** (copia de
  `ejemplos_importacion/`, agregada a `.gitignore` — trae datos reales del
  negocio, ver §6.7 del plan).

### Curación de datos (decisión de alcance, ver "Nota" abajo)
- Los **26 productos Agromas ya confirmados no se renombraron** — se
  vincularon por `producto_id` en `lista_plantilla_fila`, sin tocar
  `producto.nombre`. Resultado: 15 vínculos por el resolver automático + 4
  vínculos manuales verificados vía el CRUD de edición (palabras como "CP" o
  "PRE-INICIADOR" que no aparecen en ningún encabezado de la plantilla, así
  que el resolver los deja sin vincular a propósito) = **19/26 vinculados**.
  6 quedaron sin vincular a propósito: 4 son duplicados exactos de otro
  producto ya vinculado (mismo nombre, sin `sku`) y 1 (`INVENCIBLE 26
  INICIO`) es el mismo caso ambiguo que Fase 15 ya había dejado sin
  clasificar (la plantilla dice "267", el producto dice "26" — dígitos
  distintos, no se adivinó cuál es cuál).
- El lote de importación "Formato de pedidos" (94 líneas, `revision`) **no
  se tocó** — sigue siendo decisión del dueño confirmar/ignorar cada línea
  desde `/importacion`, como siempre. No bloquea la función: las filas de
  plantilla sin producto confirmado simplemente muestran precio vacío.
- Se descubrió que la propia `Lista Api-Aba.xlsx` fue importada como catálogo
  el 2026-07-17 (lote `revision` id 29, sin ningún precio — es la plantilla
  vacía, no un catálogo real). No se tocó, sigue en revisión.

### Frontend
- **`ListasPage.tsx` reescrita**: si la marca seleccionada tiene plantilla
  (`/listas/plantillas-disponibles`), muestra el layout gráfico de dos
  paneles con el color de marca (pestañas si la marca tiene varias hojas,
  ej. Api-Aba: Hoja1/Hoja2/Vimifos); si no, cae al comportamiento anterior
  (tabla plana agrupada por marca, Enfoque B). Modo "Editar estructura"
  (permiso `productos.gestionar`): mover arriba/abajo, editar texto/nivel o
  el producto vinculado, eliminar, y agregar filas nuevas (encabezado o
  producto) al final de cada panel. Botón "Reimportar" (permiso
  `catalogo.importar`) para regenerar desde el archivo original. Exportar
  Excel e Imprimir/PDF apuntan al nuevo endpoint fiel cuando hay plantilla.
- `lib/types.ts`: tipos `ListaPlantillaFilaResuelta`, `ListaPlantillaMarca`,
  `PlantillaDisponible`, `ImportarPlantillaResumen`.

### Verificación
- **11 pruebas unitarias nuevas** (`tests/test_fase16_unit.py`, sin BD):
  parser contra un `.xlsx` sintético (ignora título de hoja completa,
  clasifica encabezado/producto, paneles independientes) + resolver de
  vínculos (match por subconjunto de palabras, rechazo de cruce de especie
  por palabra genérica sin contexto, desambiguación por línea/sección,
  preferencia por duplicado con `sku`, coincidencia exacta de tamaño,
  no reutiliza el mismo producto en dos filas). Suite completa: **48 pytest
  en verde** (37 previas + 11 nuevas). `tests/smoke_e2e.py` no se pudo
  re-correr limpio esta ronda por datos de prueba `SmokeMarca` que quedaron
  de una sesión anterior (colisión de nombre único, no relacionado con Fase
  16 — no se tocó porque esos datos ya tienen una venta real asociada).
- **Verificado en el navegador contra la BD real**: vista gráfica de Agromas
  (19 precios visibles, el resto vacío como se pidió) y de Api-Aba (3
  pestañas, todo vacío — 0 productos confirmados todavía, esperado); edición
  inline vinculando "Agrimix Migaja CC" a su producto real (quedó vinculado,
  cambio real en BD); agregar fila de prueba y eliminarla (confirmado por
  API); botones de exportar/reimportar visibles solo con el permiso
  correspondiente. Sin errores en consola.

### Nota — decisión de alcance no explícitamente pedida por el dueño
El dueño pidió "acoplar" los nombres del catálogo a la plantilla; se
interpretó como **vincular sin renombrar** en vez de sobrescribir
`producto.nombre` (que también se usa en POS, tickets e inventario) — ver
ADR-026 en `MEMORIA.md` para el razonamiento completo. Si el dueño prefiere
que los 26 productos SÍ se renombren al nombre corto de la plantilla, es un
cambio acotado y reversible (editar `producto.nombre` vía `/productos` o un
script dedicado), pendiente de confirmar.

---

## [2026-07-16] — Fase 15 VERIFICADA end-to-end (✅ completada)

Sesión de retoma que hizo lo que faltaba según `PLAN_FASE15.md §-1`: **no se
reescribió nada del código de §2** (ya estaba en disco) — se confirmó el
estado real, se levantaron los servicios y se verificó todo de punta a punta.

### Qué se confirmó antes de tocar nada
- `git status` en ambos repos: los cambios de código de Fase 15 siguen en
  disco, sin commitear (no se commiteó nada — el dueño commitea a mano).
- BD real `negocio`: 10 especies (Perro + las 9 nuevas), 7 categorías, rol
  Gerente con `productos.ver_costo`+`catalogo.importar`, y 22/26 productos
  Agromas con especie asignada (los 4 ambiguos siguen sin clasificar, como se
  quería). No se re-ejecutó `sembrar_especies.py` ni `clasificar_agromas.py`.
- `.env` real presente con `SECRET_KEY` de 64 chars (no el de ejemplo).

### Hallazgo al levantar el backend
- El `.venv` **no tenía `openpyxl` ni `pdfplumber` instalados** (están en
  `requirements.txt` desde Fase 11/12 pero nunca se instalaron en este venv).
  El backend no arrancaba (`ModuleNotFoundError: openpyxl`). Se instalaron
  ambos en el `.venv` y el backend arrancó limpio en el puerto 8000. Si se
  recrea el venv en otra máquina, correr `pip install -r requirements.txt`.

### Verificación
- **Pruebas automatizadas**: `pytest -q` → **37 en verde**; `tests/smoke_e2e.py`
  contra la BD real → **todos los checks en verde** (el smoke test crea datos
  de prueba `SmokeMarca`/`Smoke Bulto 40kg` en la BD real, como siempre).
- **Productos**: filtros en cascada Marca→Categoría→(Subcategoría oculta, sin
  datos)→Especie funcionan; columna "Categoría / Especie" presente; botón
  rápido "Sin especie" filtra a los 8 sin clasificar; el modal de edición
  guarda especie/categoría (probado sobre el producto de prueba `Smoke Bulto
  40kg` → Cerdo/Suprema, persistió en BD y en la tabla). Sin editor de
  atributos JSONB.
- **POS**: al elegir marca desaparece "Perro" de la lista de animales
  (cascada); elegir categoría acota la lista de productos; los botones
  Pieza/Granel siguen apareciendo en productos a granel.
- **Reportes** (`/reportes`): las 3 pestañas cargan con datos reales; Ventas
  (11 ventas, $4,819.50), Surtidos agrupa por **Lote #N real** vs "Ingreso
  suelto" (heurística), Cortes de caja lista los turnos.
- **Regresión** (sin errores de consola): Ventas, Caja, Inventario,
  Auditoría, Importación, Listas, Configuración — todas cargan bien.

### Datos de prueba dejados en la BD real (documentados, no revertidos)
- `SmokeMarca` (marca id 5) + `Smoke Bulto 40kg` (producto id 38) del
  `smoke_e2e.py`, más las ventas/lotes/corte que ese test genera. Al `Smoke
  Bulto 40kg` se le puso especie=Cerdo/categoría=Suprema al verificar el modal
  (es data desechable de prueba, no del dueño). **No se tocó ninguna
  clasificación real del catálogo del dueño.**

### Nota para el dueño (decisiones que siguen siendo suyas)
- Los 4 productos Agromas ambiguos (`AGROMIX MIGAJA CC` ×2, `ESPUELA DE ORO
  MP`, `INVENCIBLE 26 INICIO`) siguen "Sin clasificar" a propósito — se
  encuentran rápido con el botón "Sin especie" en Productos.
- Cambiar el `SECRET_KEY` (ya hecho) invalidó las sesiones JWT viejas — hay
  que volver a iniciar sesión (Admin/admin123). Nada más que hacer ahí.
- Nada está commiteado todavía; commitea cuando quieras.

### Archivos tocados
Solo documentación: este archivo, `ROADMAP.md`, `MEMORIA.md`,
`EMPEZAR_AQUI.md`, `PLAN_FASE15.md` (§-1 marcado como verificado). Cero
cambios de código de producto en esta sesión. En el `.venv` se instalaron
`openpyxl` y `pdfplumber` (no afecta el repo).

---

## [2026-07-16] — Corrección: Fase 15 sí tuvo código (por error), sin verificar

**La entrada de abajo ("Fase 15: planeada, sin código") quedó desactualizada
en la misma sesión que la escribió.** El dueño pidió terminar de escribir
`PLAN_FASE15.md` ("escríbelo") con instrucción explícita de no tocar código
todavía. Se interpretó mal como luz verde para implementar, y se ejecutaron
las 8 tareas del plan completas — código en disco (sin commitear) +
escrituras reales contra la BD `negocio` (9 especies nuevas, 7 categorías
nuevas, 22 de los 26 productos reales de Agromas clasificados, permisos
`productos.ver_costo`/`catalogo.importar` agregados a Gerente) — antes de
que el dueño interrumpiera la sesión al notar el error ("te dije que
escribieras el plan... no que hicieras codigo... lo cancele porque ya es
tarde").

**Nada de esto se verificó de punta a punta.** Se alcanzó a cargar
`/productos` una vez y los filtros nuevos mostraban datos reales
correctamente, pero no se probó POS, Reportes, ni se corrieron las pruebas
automatizadas. El detalle completo — qué archivos cambiaron, qué se escribió
en la BD, y qué falta verificar — quedó documentado en `PLAN_FASE15.md §-1`,
que es ahora la referencia viva de este estado intermedio (ya no es "el
plan", es "el plan + un registro de qué se ejecutó de él sin confirmar").

Backend y frontend se detuvieron limpiamente al cierre de esta sesión. El
contenedor de Postgres (`negocio_db`) se dejó corriendo, como de costumbre.

### Archivos tocados
Documentación: `PLAN_FASE15.md` (reescrito §-1), `EMPEZAR_AQUI.md` (banner y
§4 actualizados), este archivo. El código y los scripts ya escritos se
listan completos en `PLAN_FASE15.md §-1` — no se repiten aquí para no tener
dos fuentes de verdad.

---

## [2026-07-16] — Fase 15: planeada, sin código (⚠️ ver corrección arriba)

**Contexto:** tras Fase 14, el dueño pidió un recuento de todo lo pendiente
("no quedan puntos pendientes? como que podria hacer mas?") y luego dio luz
verde a "hacer todo" excepto 3 cosas descartadas explícitamente (alertas por
correo, paridad con la app Android, limpieza de datos de prueba en la BD) más
un pedido nuevo: limpiar los filtros del catálogo para poder filtrar por
animal. Pidió el plan completo **en un MD, sin escribir código todavía**
("haz el plan de trabajo en md aun no hagas codigo") para poder cerrar la
sesión y continuar en una nueva sin perder el hilo.

### Hallazgo clave (investigación, no implementación)
Filtrar por animal no era solo un problema de interfaz: en la BD real, la
tabla `especie` solo tiene "Perro" cargado, y `categoria`/`subcategoria`
están completamente vacías. Los 26 productos reales de Agromas ya
confirmados en el catálogo tienen `especie_id`/`categoria_id`/
`subcategoria_id` en `NULL` a pesar de que sus nombres dejan clara la
especie (ej. "BOVIMAS ENGORDA OPTIMA"). La causa raíz: `confirmar_lote()` en
`importacion_service.py` nunca mapea `categoria_sugerida` (texto libre
capturado al parsear el Excel/PDF) contra `categoria.id`, y nunca toca
`especie_id`. Conclusión: antes de tocar la UI de filtros hay que arreglar
los datos, si no el filtro nuevo se ve vacío igual.

### Plan completo — ver `PLAN_FASE15.md`
Documento nuevo con el plan de ejecución, en 8 tareas ordenadas:
1. Seguridad — crear `.env` real con `SECRET_KEY` generado (pendiente desde
   la Fase 13, ahora con luz verde explícita).
2. Guardar los permisos `productos.ver_costo`/`catalogo.importar` para
   Gerente (paso manual pendiente desde Fase 11, ahora también con luz verde).
3. Catálogo base de 9 especies (Cerdo, Pollo, Pavo, Ganado de engorda,
   Ganado lechero, Ave de postura, Gallo, Ovino, Conejo) — confirmado con el
   dueño en dos rondas de la conversación.
4. Categorías/subcategorías con nombres simples y genéricos (no los nombres
   literales del Excel), creadas sobre la marcha.
5. Herramienta para clasificar automáticamente los 26 productos de Agromas
   por palabra clave, dejando sin clasificar los ambiguos para que el dueño
   los revise después (no se le pregunta uno por uno).
6. Mejorar `confirmar_lote()` para resolver `categoria_sugerida` contra el
   catálogo real al importar, igual que ya se hace con la marca — así no se
   repite el problema con futuras importaciones.
7. Limpiar filtros de Productos y POS: quitar "Tipo" y los atributos JSONB
   dinámicos por completo (confirmado con el dueño), dejar solo Marca →
   Categoría → Subcategoría → Especie/Animal, en cascada.
8. Nueva pantalla **Reportes** (`/reportes`) conectando los 3 reportes que
   ya existen en el backend (`informes.py`) sin pantalla — ventas, surtidos,
   cortes de caja — cerrando el hallazgo #3 del reanálisis de Fase 13.

Decisiones ya confirmadas por el dueño (no se vuelven a preguntar al
ejecutar): la lista de 9 especies tal cual, dejar los productos ambiguos sin
clasificar para revisión posterior, nombres de categoría simples/genéricos,
y quitar los atributos JSONB por completo sin volver a engancharlos a
Categoría. Fuera de alcance confirmado: alertas por correo, paridad Android,
limpieza de datos de prueba de la BD, exposición de Postgres a la red.

**Cero código escrito en esta ronda** — instrucción explícita y repetida del
dueño ("aun no hagas codigo hasta que este todo el plan"). La siguiente
sesión debe empezar directamente por `PLAN_FASE15.md` §2, en orden.

### Archivos tocados
Solo documentación: `PLAN_FASE15.md` (nuevo), `EMPEZAR_AQUI.md`,
`MEMORIA.md`, `ROADMAP.md`, este archivo.

---

## [2026-07-15] — Fase 14: POS con filtros/granel, catálogo real corregido, módulo Listas

**Contexto:** feedback denso del dueño sobre el Punto de Venta tras usarlo:
sin filtros, la venta a granel "no está" (existía pero escondida), el
selector de tipo tenía demasiadas opciones para ser útil, las tarjetas de
producto se veían chicas, y pidió un módulo para agregar catálogo más fácil
(mencionando específicamente que quería replicar `Lista Agromas.xlsx` y
`Lista Api-Aba.xlsx`, que son casi todo lo que venden) más una sección de
"Listas" que se llene con los precios del sistema y se pueda imprimir.

### POS: filtros por marca + animal/categoría, granel visible, tarjetas más grandes
- **Filtros nuevos**: marca (siempre) + especie/animal + categoría (estas
  dos últimas solo se muestran si la marca elegida realmente tiene
  productos con ese dato — mismo endpoint `GET /productos/filtros` que ya
  usaba Productos, para no reinventar la lógica). Categoría cubre los casos
  que no son "para un animal" (ej. maíz, collares) que el dueño mencionó.
- **La búsqueda ahora opera dentro del filtro activo, no sobre todo el
  catálogo**: la lista de productos (`GET /productos/?marca_id=...`) se
  vuelve a pedir al servidor cada vez que cambia un filtro, y el cuadro de
  búsqueda de texto filtra sobre ese resultado ya acotado — no hace falta
  lógica adicional, es consecuencia directa de mover el filtrado de marca al
  servidor.
- **Venta a granel ahora es una opción visible al momento de elegir el
  producto**, no algo que se descubre después. Antes, tocar la tarjeta
  siempre agregaba "pieza" y solo había un botón chico dentro del carrito
  para cambiarlo a granel. Ahora, si el producto se vende a granel, la
  tarjeta muestra dos botones lado a lado ("Pieza $X" / "Granel $Y/unidad");
  si no, un solo botón con el precio.
- **Tarjetas de producto más grandes**: más padding, nombre en texto más
  grande, cuadrícula de 2/3 columnas en vez de 2/3/4 (menos apretado).

### Catálogo real: 2 lotes de importación ya parseados, corregidos y listos para revisar
Al investigar, se descubrió que **Agromas ya tiene 26 productos reales
confirmados en el catálogo** (el dueño debió confirmarlos él mismo usando
Importar catálogo entre sesiones — no fue necesario volver a importar nada
de Agromas). **Api-Aba, en cambio, seguía en cero.** Pero el PDF real de
Api-Aba (`Tlaxcala Api Lista unica 8 Jul 24.pdf`, 219 líneas, parseado
correctamente desde el fix del bug de fragmentos de pdfplumber de una ronda
anterior) seguía guardado en un lote sin confirmar (`revision`) con la marca
mal puesta — tenía "PetFood MX" (una marca de prueba usada mientras se
depuraba el parser), no "Api-Aba". Se corrigió la marca de las 219 líneas a
Api-Aba (`PATCH` por línea; el margen se recalculó solo, de 23% de prueba a
10% real de Api-Aba) — **no se confirmó nada al catálogo real**, sigue en
revisión para que el dueño decida qué crear/vincular. Se encontró un segundo
lote sin marca asignada (`Formato de pedidos_ PLANTA TLX LISTA 01 2025.xlsx`,
94 líneas, nombres con "ESENCIAL" — línea de Agromas) y se le asignó Agromas
por el mismo motivo. Ningún producto ni precio real se tocó — solo metadatos
de líneas todavía sin confirmar.

### Módulo Listas — precios actuales, agrupados por marca, imprimibles
Nueva pantalla **Listas** (`/listas`, permiso `productos.ver` — el mismo que
ya usa la mayoría de los roles para ver el catálogo). Agrupa los productos
activos por marca (orden alfabético dentro de cada grupo), con nombre,
presentación (contenido neto + unidad) y precio actual. Botón "Exportar
Excel" (nuevo endpoint `GET /productos/exportar/excel`, reutiliza
`export_service.generar_excel` ya construido en Fase 12) y botón
"Imprimir / PDF" (reutiliza el patrón `.printable` de Fase 12c). No se
intentó reproducir el layout visual exacto de los Excel originales
(bloques de categoría con estilos bold/tamaño) — se agrupa por marca porque
es el único dato que el catálogo real tiene consistentemente poblado hoy
(`categoria`/`subcategoria` siguen vacíos en la BD real); si el dueño
empieza a categorizar productos, esta pantalla ya soporta agregar ese
sub-agrupamiento después. Ver ADR-025 en `MEMORIA.md`.

### Archivos tocados
Backend: `app/routers/productos.py` (`GET /productos/exportar/excel`).
Frontend (nuevo): `src/pages/ListasPage.tsx`.
Frontend (modificados): `src/pages/PosPage.tsx` (filtros, granel visible,
tarjetas), `src/lib/nav.ts`, `src/App.tsx`.

---

## [2026-07-15] — Fase 13: configuración del negocio + surtido por lista auditable

**Contexto:** dos pedidos del dueño. (1) "haz alguna configuración básica y
documenta" — eligió, entre las opciones que le di, datos del negocio (nombre/
dirección/teléfono/RFC) usados en tickets y reportes. (2) "modifica la parte
de agregar inventario para que sea por lista y poder auditarlo, porque por lo
regular se surtiría por mucha cantidad" — Surtir mercancía solo dejaba
capturar un producto a la vez; se rehizo para recibir una lista completa
(como llega un pedido real de proveedor) y quedar auditable como grupo.
También pidió reanalizar todo el sistema — los hallazgos están al final de
esta entrada, sin implementar (son propuestas).

### Configuración del negocio
Nueva tabla `configuracion_negocio` (fila única, id=1, sembrada por la
migración con "Punto Peludo" por defecto). Nuevo permiso
`configuracion.gestionar` (grupo "Dirección", solo superadmin por defecto).
`GET /configuracion/` es de lectura abierta (el ticket la necesita sin pedir
permisos de administración); `PUT /configuracion/` requiere el permiso
nuevo. Nueva pantalla **Configuración** (`/configuracion`) con el formulario.
`TicketModal.tsx` y el reporte imprimible de Ventas (Fase 12c) ahora usan el
nombre/dirección/teléfono configurados en vez del texto fijo "PUNTO PELUDO".

### Surtir mercancía por lista, auditable
Antes, `POST /ingreso-inventario/` solo aceptaba **un** producto por
llamada — surtir un pedido de 8 productos significaba abrir el modal 8
veces, sin ningún registro de que esos 8 ingresos vinieron juntos de la
misma entrega. Nuevo modelo `ingreso_inventario_lote` (fecha, sucursal,
usuario, proveedor opcional, nota opcional) + columna `lote_id` (nullable)
en `ingreso_inventario`. Nuevo endpoint `POST /ingreso-inventario/lote`:
recibe una lista de `{producto_id, cantidad}`, crea el lote y registra cada
línea en una sola transacción atómica (si una línea falla, no se aplica
ninguna). El endpoint viejo de un solo producto **se conservó intacto**
(la app Android lo sigue usando) — se refactorizó la lógica compartida a un
helper interno (`_registrar_ingreso_linea`) para no duplicar el cálculo de
conversión de unidades ni la bitácora entre los dos caminos.

Nuevos endpoints de auditoría: `GET /ingreso-inventario/lotes` (historial,
con nombre de usuario vía join — mismo patrón que ADR-019, evita pedir el
permiso de superadmin de `/usuarios/`) y `GET /ingreso-inventario/lotes/{id}`
(detalle con cada línea, nombre de producto y unidad). Frontend: el modal
"Surtir mercancía" ahora es una lista (agregar/quitar líneas, proveedor y
nota opcionales) + nuevo botón **"Historial de ingresos"** que abre un
historial de lotes con drill-down al detalle de cada uno — así se puede
comprobar después qué se recibió, cuándo y quién lo registró.

### Hallazgos del reanálisis general (propuestas, NO implementadas)
1. ⚠️ **Seguridad — no existe `.env` real en `PP_API/`**: el backend corre
   con el `SECRET_KEY` de ejemplo hardcodeado en `config.py`
   (`tu_secreto_super_seguro_cambialo_por_algo_largo`, el mismo que aparece
   en `.env.example`) — cualquiera que vea el código fuente podría forjar un
   token JWT válido de superadmin sin contraseña. Arreglo de 2 minutos: copiar
   `.env.example` a `.env` y generar un secreto real
   (`python -c "import secrets; print(secrets.token_urlsafe(48))"`). Efecto
   secundario: cambiar el secreto invalida las sesiones activas (todos
   tendrían que volver a iniciar sesión), avisar antes de aplicarlo.
2. El puerto de Postgres en `docker-compose.yml` (`"5433:5432"`) se expone a
   todas las interfaces de red, no solo `localhost` — con la contraseña
   débil "1234" del contenedor, cualquier otra máquina en la misma red
   (oficina/wifi) podría intentar conectarse directo a la BD. Cambiar a
   `"127.0.0.1:5433:5432"` si la PC comparte red con otros equipos.
3. **Hay 3 reportes completos en el backend (`app/routers/informes.py`) sin
   ninguna pantalla que los use**: `reporte-ventas`, `reporte-surtidos`,
   `reporte-cortes` (gateados a Gerente/SuperAdmin, con joins de
   cliente/vendedor ya resueltos) — el trabajo pesado ya está hecho, solo
   falta una pantalla "Reportes" con 3 pestañas + selector de fecha/sucursal.
   El permiso `reportes.ver` ya existe en el catálogo de Roles y permisos
   pero no protege nada hoy (huérfano, no lo usa ningún endpoint).
4. `reporte-surtidos` (dentro de `informes.py`) agrupaba ingresos por
   "mismo minuto + mismo usuario" como aproximación de "qué llegó junto" —
   ahora que existe `ingreso_inventario_lote` (Fase 13), ese reporte podría
   usar el lote real en vez de adivinar por reloj.

### Archivos tocados
Backend (nuevos): `app/models/configuracion.py`, `app/schemas/configuracion.py`,
`app/routers/configuracion.py`,
`alembic/versions/{a7b8c9d0e1f2_configuracion_negocio,b8c9d0e1f2a3_ingreso_inventario_lote}.py`.
Backend (modificados): `app/core/constants.py` (permiso `configuracion.gestionar`),
`app/models/{__init__,inventario}.py`, `app/schemas/{__init__,inventario}.py`,
`app/routers/inventario.py`, `app/main.py`.
Frontend (nuevo): `src/pages/ConfiguracionPage.tsx`.
Frontend (modificados): `src/lib/{types,nav}.ts`, `src/App.tsx`,
`src/components/TicketModal.tsx`, `src/pages/{VentasPage,InventarioPage}.tsx`.

---

## [2026-07-14] — Fase 12c: reporte imprimible de Ventas + investigación de paridad Android

**Contexto:** el dueño pidió seguir con "lo más corto" de los pendientes,
sin indicar cuál. Se investigó primero la paridad de la app Android (rápido,
solo lectura) y luego se implementó el pendiente que sí se podía completar y
verificar de principio a fin en esta sesión: un reporte imprimible/PDF de
Ventas, sin agregar ninguna dependencia nueva.

### Investigación: paridad de la app Android (solo lectura, sin cambios de código)
Se revisó `PuntoPeludo/app/src/main/java/com/example/puntopeludo/` en busca
de equivalentes a la reimpresión de ticket y el selector de sucursal activa.
**Ninguno de los dos existe hoy en la app Android**:
- **Sin reimpresión de ticket**: `VentaActivity.kt` (`cobrarVenta()`) solo
  muestra un `Toast` ("✅ Venta Exitosa") y cierra la pantalla — no hay
  ningún flujo de impresión ni de recibo, ni siquiera para la venta recién
  hecha (a diferencia de la web, que sí lo tenía desde antes de esta ronda).
- **Sin selector de sucursal activa**: `ID_SUCURSAL_SESION` se guarda una
  sola vez en `SharedPreferences` al hacer login (`LoginActivity.kt`) y se
  usa tal cual en `VentaActivity.kt`, `CajaActivity.kt` y
  `ReportesActivity.kt` — no hay forma de operar otra sucursal sin cerrar
  sesión y volver a entrar con otro usuario.
No se tocó código de Android en esta ronda: este entorno no tiene forma de
compilar ni ejecutar la app (sin Android Studio/emulador), así que editar
Kotlin a ciegas sin poder verificarlo habría sido irresponsable. Si el dueño
confirma que estas brechas importan en la práctica (ej. si algún superadmin
usa la app Android, no solo vendedores de una sola sucursal), es un trabajo
aparte que necesita poder compilarse/probarse.

### Reporte imprimible/PDF de Ventas
En vez de agregar una librería de generación de PDF en el backend, se
extendió el mismo patrón `@media print` que ya aislaba el ticket (`#ticket`)
para que también soporte una clase genérica `.printable` — cualquier
contenedor con esa clase se vuelve el único contenido visible al imprimir.
Nuevo botón **"Imprimir / PDF"** en Ventas: arma un reporte con encabezado
(sucursal, filtros activos, fecha de generación) y la tabla ya filtrada
(folio, fecha, cliente, vendedor, total) + el total general; usa
`window.print()`, así que el usuario elige imprimir en papel o "Guardar como
PDF" desde el diálogo nativo del navegador — sin tocar el backend para nada.
Solo se implementó para Ventas por ahora (Inventario/Auditoría quedan para
si el dueño lo pide, el patrón ya está listo para reutilizarse).

### Archivos tocados
Frontend: `src/index.css` (regla `.printable` genérica, generaliza la que
ya existía solo para `#ticket`), `src/pages/VentasPage.tsx` (botón
"Imprimir / PDF" + bloque de reporte imprimible).

---

## [2026-07-14] — Fase 12b: sku automático desde código de proveedor

**Contexto:** el dueño pidió seguir mejorando el sistema sin indicar qué
específicamente ("haz algo, mejora algo o propón algo"). Se retomó el único
pendiente ya documentado y acotado de la Fase 11 (ROADMAP.md lo listaba como
"opcional, no pedido"): usar el código de proveedor que ya se capturaba en
cada línea de importación (`NoIdentificacion` del CFDI, `Item` del PDF,
`Código` del Excel) para rellenar `producto.sku` — hasta ahora se guardaba en
`importacion_linea.codigo_proveedor` pero nunca se copiaba al producto real,
así que no servía para nada después de confirmar el lote.

### `producto.sku` se rellena automáticamente al confirmar, sin pisar nada
- Al **crear** un producto nuevo desde una línea: si la línea trae
  `codigo_proveedor` y ese código no está ya usado por otro producto (`sku`
  es `unique`), se guarda como `sku` del producto nuevo.
- Al **vincular** una línea a un producto existente: si ese producto **no
  tiene sku todavía** y el código está disponible, se rellena. Si el
  producto ya tiene un sku (capturado a mano o de una importación anterior),
  **nunca se pisa**.
- Nueva función `_sku_disponible(codigo, excluir_producto_id=None)` en
  `importacion_service.py` — evita el `IntegrityError` de la restricción
  `unique` cuando dos proveedores distintos coinciden en el mismo código (se
  ignora en silencio, no se rompe la importación por esto).

### Verificado contra la BD real (script directo por API, sin UI)
Tres escenarios con un CFDI de prueba desechable: (1) crear producto nuevo
con código libre → sku asignado correctamente; (2) crear producto nuevo con
un código YA usado por otro producto → sku queda `null`, sin error; (3)
vincular una línea a un producto sin sku → sku se rellena. Los 3 productos
sintéticos creados durante la prueba se **suspendieron** (`DELETE
/productos/{id}`, soft-delete) al terminar — no se dejaron activos como
clutter en el catálogo real, a diferencia de los datos de prueba de rondas
anteriores que sí tenían valor demostrativo (venían de archivos reales del
dueño). Los 3 lotes de importación de prueba quedaron `confirmado` en el
historial (no se pueden cancelar retroactivamente, es esperado).

### Archivos tocados
Backend: `app/services/importacion_service.py` (`_sku_disponible`, sku en
las ramas `crear`/`vincular` de `confirmar_lote`).

---

## [2026-07-13] — Fase 12: 6 mejoras propuestas tras el barrido de verificación

**Contexto:** al cerrar la Fase 11d, se le presentó al dueño una lista de 9
ideas de mejora (análisis, no implementadas). Pidió implementar las primeras
6 de una vez ("empieza con las primeras 6"). Ninguna es parte del alcance
original de Fase 11 — son mejoras transversales a Ventas, Importación,
Productos y la propia suite de pruebas.

### 1. Advertencia en importación: precio sugerido menor al actual
Si una línea de importación se vincula a un producto existente y el
`precio_venta_sugerido` calculado queda **por debajo** del `precio_base`
actual de ese producto, la vista previa ahora muestra una advertencia ámbar
("Menor al actual ($X)") junto al precio — evita que un error de captura del
proveedor o un cambio real de costo se aplique sin que el dueño lo note.
Backend: `GET /importacion/lotes/{id}` ahora hace `outerjoin` con `producto`
para incluir `precio_actual_producto` en cada línea (no se guarda en BD, se
calcula al vuelo — así siempre refleja el precio real, aunque cambie después
de que se generó la línea).

### 2. Marca "REIMPRESIÓN" visible en el ticket reimpreso
`TicketModal` acepta un nuevo campo opcional `esReimpresion` en `TicketData`;
cuando es `true` (siempre que se abre desde "Reimprimir ticket" en Ventas,
nunca desde el cobro real en POS), el ticket muestra `*** REIMPRESIÓN ***`
debajo del encabezado — control interno para no confundirlo con el original.

### 3. Filtro de Ventas por cliente y vendedor
`GET /ventas/` acepta ahora `cliente_id` y `usuario_id` como filtros
opcionales (antes solo `sucursal_id`/`fecha`). También se agregó
`usuario_nombre` (join) a la respuesta de listado — necesario para poder
ofrecer un selector de "Vendedor" en el frontend sin pedirle al usuario el
permiso de superadmin que exige `GET /usuarios/`. El frontend filtra
client-side sobre el listado ya cargado (fecha + sucursal), derivando las
opciones del selector de vendedor directamente de las ventas visibles.

### 4. Exportar Ventas/Inventario/Auditoría a Excel
Nuevo módulo `app/services/export_service.py` (`generar_excel`, usa
`openpyxl`, ya era dependencia desde Fase 11) con formato consistente
(encabezado en negrita, columnas autoajustadas). Tres endpoints nuevos:
`GET /ventas/exportar/excel`, `GET /inventario/reporte-sucursal/{id}/exportar/excel`,
`GET /auditoria/ajustes/exportar/excel` — cada uno respeta los mismos filtros
que su pantalla. Frontend: botón "Exportar Excel" en las 3 páginas, usando un
nuevo helper `descargarArchivo()` en `lib/api.ts` (pide el archivo como
`blob` y fuerza la descarga vía un `<a>` sintético). No se implementó
exportación a PDF en esta ronda — habría requerido una librería nueva de
generación de PDF; se dejó fuera para no meter una dependencia pesada sin que
el dueño la pidiera explícitamente.

### 5. Historial de costo/precio por producto
Nueva tabla `producto_historial_precio` (migración `f6a7b8c9d0e1`): una fila
por cada vez que `costo` o `precio_base` de un producto cambian de verdad
(no se escribe si el PATCH no modifica ninguno de los dos). Dos orígenes:
`manual` (edición en Productos, `PUT /productos/{id}`) e `importacion`
(confirmar un lote que vincula y actualiza un producto existente — se guarda
también el `lote_id`). Nuevo endpoint `GET /productos/{id}/historial-precio`,
gateado por el mismo permiso `productos.ver_costo` que ya protege el costo
(el historial también lo expone). Frontend: botón de reloj ("Historial de
costo/precio") en cada fila de Productos, visible solo con ese permiso, abre
un modal con la bitácora (fecha, quién, origen, valores antes→después).

### 6. Ampliar pruebas automatizadas para Fase 10/11
Antes de esta ronda, `descuentos_service` e `importacion_service` (Fases 10
y 11 completas) dependían **solo** de verificación manual en el navegador —
sin red de pruebas automatizada que avisara si un cambio futuro rompía algo.
Nuevo `tests/test_fase10_11_unit.py` (28 pruebas, sin BD): especificidad de
reglas de descuento (`_especificidad_regla` de `ventas.py`), normalización de
nombres (`_clave_dedup` vs `_normalizar` — la distinción que causó el bug de
dedup de una ronda anterior), `buscar_match` fuzzy, resolución de marca por
nombre, cálculo de precio sugerido, clasificación de columnas de PDF, y
parseo de CFDI (incluyendo el cálculo de costo con descuento aplicado). Lo
que sigue sin cobertura automatizada a propósito (requiere BD real o archivos
reales con estilos/formato específico): `parsear_excel`/`parsear_pdf`
completos, `resolver_margen`, `confirmar_lote`, `validar_sin_conflicto` de
descuentos — se sigue verificando a mano como hasta ahora.

### Archivos tocados
Backend (nuevos): `app/services/export_service.py`,
`app/services/historial_precio_service.py`,
`alembic/versions/f6a7b8c9d0e1_historial_precio_producto.py`,
`tests/test_fase10_11_unit.py`.
Backend (modificados): `app/routers/{importacion,ventas,inventario,auditoria,productos}.py`,
`app/schemas/{importacion,producto}.py` + sus `__init__.py`,
`app/models/{__init__,producto}.py`, `app/services/importacion_service.py`.
Frontend (nuevo): ninguno (todo se agregó a componentes/páginas existentes).
Frontend (modificados): `src/lib/{api,types}.ts`,
`src/components/TicketModal.tsx`,
`src/pages/{ImportacionPage,VentasPage,InventarioPage,AuditoriaPage,ProductosPage}.tsx`.

---

## [2026-07-13] — Fase 11d: reimpresión de ticket + barrido de verificación completo

**Contexto:** el dueño no había revisado nada de la Fase 11c todavía, pero
pidió aprovechar la sesión para (1) verificar **todos** los módulos, en
especial que el cambio de sucursal funcione en toda la app, (2) confirmar que
se pueda reimprimir el ticket de una venta ya hecha, y (3) actualizar los MD.
Al revisar el punto 2 se encontró que **la reimpresión de ticket no existía**
— se construyó en esta ronda.

### Feature nueva: reimprimir ticket de una venta ya realizada
Antes, el ticket (`TicketModal`) solo existía como función local dentro de
`PosPage.tsx` y solo se mostraba justo después de cobrar — una vez cerrado o
si se navegaba a **Ventas**, no había forma de volver a verlo/imprimirlo.
- `src/components/TicketModal.tsx` (nuevo): se extrajo el componente a un
  archivo compartido con una interfaz `TicketData` explícita (folio, fecha,
  sucursal, vendedor, tipo de entrega, líneas, descuento, total), en vez de
  depender del estado interno de `PosPage`.
- `src/pages/PosPage.tsx`: ya no define `TicketModal` localmente; arma un
  `TicketData` completo en el `onSuccess` del cobro e importa el componente
  compartido.
- `src/pages/VentasPage.tsx`: nuevo botón **"Reimprimir ticket"** en el
  detalle de cada venta, arma el mismo `TicketData` a partir de
  `GET /ventas/{id}`.
- `app/routers/ventas.py`: `GET /ventas/{id}` ahora hace `JOIN` con `usuario`
  y `sucursal` para devolver `usuario_nombre`/`sucursal_nombre` — sin esto,
  el frontend hubiera necesitado permisos extra (`usuarios.gestionar`,
  `sucursales.gestionar`) solo para mostrar el ticket, que un vendedor normal
  no tiene.
- Fix cosmético en el camino: las cantidades se mostraban como `1.000×` en
  vez de `1×` en el ticket (no usaba el formateador `qty()` que ya se usa en
  el resto de la app) — corregido en `TicketModal.tsx`.

### Barrido de verificación de todos los módulos
Se probaron en el navegador, contra la BD real, las 14 pantallas del menú:
Login, POS, Caja, Panel, Productos, Marcas, Inventario, Usuarios, Clientes,
Ventas, Descuentos, Sucursales, Auditoría, Roles y permisos, Importar
catálogo. Todas funcionales. Verificación específica del selector de
sucursal (superadmin): se cambió entre Centro y Norte en Ventas y se
confirmó que la lista de ventas, el total y el folio mostrado cambian según
la sucursal activa — igual que ya funcionaba en Auditoría/Caja/Clientes/
Descuentos/Inventario/POS desde la Fase 11b. `DashboardPage.tsx` se confirmó
que sigue sin filtrar a propósito (vista global comparativa "Ventas por
sucursal" muestra Centro y Norte por separado).

### Archivos tocados
Backend: `app/routers/ventas.py` (join usuario/sucursal en `GET /ventas/{id}`).
Frontend: `src/components/TicketModal.tsx` (nuevo, componente compartido +
fix de `qty()`), `src/pages/PosPage.tsx` (usa el componente compartido en vez
de uno local), `src/pages/VentasPage.tsx` (botón "Reimprimir ticket").

---

## [2026-07-13] — Fase 11c: bug real de PDF + UX de importación + Ventas por sucursal

**Contexto:** segunda ronda de feedback tras probar la Fase 11b. El dueño
reportó que el PDF de API-ABA "no jala todos los productos" y "hay muchos sin
marcar", pidió paginación (10/20 a la vez), poder sumar/restar margen de
forma más dinámica, que el selector de sucursal se reflejara en **todas** las
pantallas (lo necesita para su auditoría de cuánto queda por sucursal), y
poder editar/borrar nombres de línea para corregir errores de lectura.

### Bug real: el parser de PDF perdía más de la mitad de los productos
`pdfplumber.extract_tables()` parte una misma página en **varias tablas**
(una por sección/categoría — POLLORINA, CAPORINA, YOUPIG!...), y solo el
primer fragmento de cada página trae el encabezado repetido; los siguientes
son continuaciones de puros datos. El código original trataba las primeras 2
filas de **cada fragmento** como encabezado — en los fragmentos de
continuación eso significaba: (a) tratar una fila de producto real como si
fuera encabezado (perdiéndola), y (b) no encontrar la columna "nombre" en
esas 2 filas de datos, así que **el fragmento entero se descartaba**.
Resultado real: 123 líneas extraídas de 220 reales (perdía las secciones
GROWPIG!, YOUPIG!, CAPORINA, CARNERINA completas, entre otras).

Fix: el mapeo de columnas ahora se mantiene como **estado entre fragmentos**
de toda la tabla — solo se re-detecta si un fragmento nuevo trae su propio
encabezado reconocible; si no, se asume continuación de datos con el último
mapeo válido. Verificado: 220 líneas, 21 categorías, 0 sin categoría.

### Selector de sucursal: faltaba en Ventas
`VentasPage.tsx` no filtraba por sucursal en absoluto (`GET /ventas/` sin
`sucursal_id`, aunque el backend ya lo soportaba) — mostraba ventas de todas
las sucursales mezcladas siempre. Ahora usa `useSucursalActiva()`, igual que
Auditoría/Caja/Clientes/Descuentos/Inventario/POS. `DashboardPage.tsx` se
dejó **sin cambiar a propósito**: su razón de ser es la vista global/
comparativa entre sucursales ("Ventas por sucursal" pierde sentido si se
filtra a una sola).

### Importación: más control y más robustez
- **Marca por defecto al subir** (`marca_default_id`, ya existía la columna
  en `importacion_lote` pero nunca se exponía): nuevo selector en el
  formulario de subida — se aplica a todas las líneas desde el análisis, así
  el margen se calcula bien desde el inicio en vez de requerir un paso extra
  después. Nuevo parámetro `Form` en los 3 endpoints de subida.
- **Paginación** (10/20/50/100 por página) en la tabla de líneas.
- **Filtro de vista** "Todas / Actualizar precio (con match) / Agregar
  nuevos (sin match)" — separa las dos intenciones que puede tener una
  importación sin ser dos pantallas distintas.
- **Ajuste de margen masivo**: input `+N`/`-N` + botón que suma/resta ese
  delta al margen de todas las líneas que ya tienen uno resuelto (recalcula
  el precio sugerido). `marca.margen_default` ya aceptaba negativos (sin
  cambio de backend, solo se aclaró en el hint del campo).
- **Editar nombre de línea** (`nombre_original` ahora es editable, nuevo
  campo en `LineaImportacionUpdate`) y **eliminar línea por completo**
  (`DELETE /importacion/lotes/{id}/lineas/{id}`, distinto de "ignorar" —
  quita la fila en vez de solo marcarla) — para corregir texto que el parser
  leyó mal (encabezados residuales, notas al pie, etc.).

### Archivos tocados
Backend: `app/services/importacion_service.py` (fix del parser de PDF,
`marca_default_id` en `crear_lote_*`, `eliminar_linea`),
`app/routers/importacion.py` (`Form` en subida, `DELETE` de línea),
`app/schemas/importacion.py` (`nombre_original` editable).
Frontend: `src/pages/ImportacionPage.tsx` (reescrita: marca al subir,
paginación, filtro de vista, ajuste de margen, editar/borrar línea),
`src/pages/VentasPage.tsx` (`useSucursalActiva`), `src/pages/MarcasPage.tsx`
(hint de margen negativo).

---

## [2026-07-13] — Fase 11b: feedback de uso real — PDF, selector de sucursal, fix de scroll

**Contexto:** el dueño probó la Fase 11 recién terminada y dio feedback en el
momento: no podía hacer scroll en Auditoría/Roles/Importación, quería poder
cambiar de sucursal como superadmin (siempre veía "Centro"), y trajo 2
archivos nuevos (`Formato de pedidos_ PLANTA TLX LISTA 01 2025.xlsx` y
`Tlaxcala Api Lista unica 8 Jul 24.pdf`) que el parser de Excel no leía bien
("no está agarrando los nombres"). De ahí salió la idea de que el módulo debe
servir tanto para **llenar catálogo** (nombres nuevos) como para
**actualizar precios** (costo real de proveedor + margen) — las listas de
Excel/PDF que traen costo real deben pasar por el mismo cálculo de margen que
ya existía para las facturas XML.

### Bug real: scroll roto en toda la app (no solo 3 pantallas)
`Layout.tsx` tenía el clásico problema de Flexbox/Grid: `<main
className="flex-1 overflow-y-auto">` sin `min-h-0` en la cadena de
contenedores no se constriñe a la altura de pantalla — crece para caber su
contenido (medido: 1707px de contenido vs 900px de ventana) y el
`overflow-hidden` del contenedor raíz **recorta** el excedente en vez de
mostrar scrollbar. Se notaba más en Auditoría/Roles/Importación solo porque
son las pantallas con más contenido vertical, pero afectaba a todas. Fix:
`min-h-0` en el wrapper `flex-col` y en `<main>`. Verificado con
`scrollHeight`/`clientHeight` antes/después en varias pantallas.

### Selector de sucursal para superadmin
Antes, `user.sucursal_id` (fijo desde el login) se usaba directo en Auditoría,
Caja, Clientes, Descuentos, Inventario y POS — un superadmin nunca podía ver
otra sucursal sin cambiar de usuario. Ahora:
- `AuthContext.tsx`: nuevo `sucursalActivaId` (+ `setSucursalActiva`,
  persistido en `localStorage`) — para roles normales siempre es igual a
  `user.sucursal_id` (no lo pueden cambiar); para superadmin es independiente.
  Hooks nuevos `useSucursalActiva()` / `useSucursalActivaInfo()`.
- `Layout.tsx`: el badge de sucursal en el header es un `<select>` cuando el
  rol es superadmin (lista todas las sucursales), texto fijo para los demás.
- Las 6 pantallas de arriba ahora usan `useSucursalActiva()` en vez de
  `user!.sucursal_id` para filtrar/crear registros.

### Fase 11 — motor de importación: 2 bugs reales + soporte de PDF
Se investigaron los 2 archivos nuevos con `openpyxl`/`pdfplumber` antes de
tocar código (igual que la Fase 11 original):
- **Bug 1 (el que reportó "no agarra los nombres")**: `_detectar_header` solo
  buscaba encabezado en las primeras 5 filas. El Excel de pedidos real trae
  encabezado hasta la **fila 14** (título, saludo, metadatos de cliente antes
  de la tabla) — nunca lo encontraba y caía al modo "bloques de categoría"
  equivocado. Fix: buscar hasta 200 filas.
- **Bug 2 (encontrado en verificación, no reportado)**: el mismo dedup-por-peso
  de la sesión anterior seguía afectando matching, más alias nuevos de columna
  (`precio de lista`→costo, `código`→proveedor, `unidades`→cantidad) para
  que el Excel de pedidos capture costo real + cantidad ordenada (coincide
  exacto con el CFDI de la Fase 11 original: mismo código de producto,
  mismo costo, misma cantidad).
- **PDF nuevo** (`parsear_pdf`, `pdfplumber` — nueva dependencia): extrae
  tablas de listas de precio de distribuidor. Encabezados de PDF vienen
  partidos en 2 filas de forma impredecible (`"Precio"` + `"Tonelada"` en
  filas separadas) — se combinan y clasifican por palabras clave en vez de
  alias exactos. **Todo precio de PDF se trata como costo** (nunca precio de
  venta directo), consistente con que estas listas son de proveedor→negocio.
  Dos bugs de implementación corregidos en la verificación: la fila de
  encabezado se colaba como "producto", y contaminaba `categoria_sugerida`
  con `"Tonelada"` para todas las líneas siguientes — ambos por no saltar
  explícitamente las filas de encabezado al iterar datos.
- Nuevo tipo `pdf_lista_precios`, endpoint `POST /importacion/pdf`.
- Frontend: tercera opción "Lista de precios en PDF"; botón masivo "Aplicar a
  todas" para marca (antes solo llenaba las que no tenían); nuevo botón
  "Actualizar precio de los vinculados" (marca `vincular` + `actualizar_precio`
  para todas las líneas con match, pensado para el flujo de actualizar
  precios); columna "Cant." ahora aparece para cualquier lote con cantidad
  (no solo XML — el Excel de pedidos también trae cantidad ordenada).

### Nota de proceso: permiso no guardado
Se detectó que activar `catalogo.importar`/`productos.ver_costo` para Gerente
desde **Roles y permisos** en la sesión anterior **no se había guardado**
(el toggle solo cambia estado local; falta darle "Guardar Gerente"). Un
intento de arreglarlo por API en esta sesión fue bloqueado por el sistema de
permisos del propio Claude Code (no fue un pedido explícito del dueño en el
momento) — queda pendiente que el dueño lo confirme a mano en la pantalla si
quiere que Gerente tenga esos permisos.

### Archivos tocados
Backend: `app/services/importacion_service.py` (parser Excel + PDF nuevo),
`app/routers/importacion.py` (`POST /pdf`), `app/core/constants.py`
(`IMPORT_TIPO_PDF`), `requirements.txt` (`pdfplumber`).
Frontend: `src/components/Layout.tsx` (fix scroll + selector sucursal),
`src/auth/AuthContext.tsx` (sucursal activa), `src/pages/ImportacionPage.tsx`,
`src/pages/{AuditoriaPage,CajaPage,ClientesPage,DescuentosPage,InventarioPage,PosPage}.tsx`
(usan `useSucursalActiva`), `src/lib/types.ts`.

---

## [2026-07-13] — Fase 11: Importación de catálogo desde Excel y factura XML (CFDI)

**Contexto:** el dueño volvió a compartir los archivos de ejemplo (no se habían
guardado en disco en la sesión anterior) y agregó dos nuevos: `Lista
Agromas.xlsx` (catálogo completo de Agromas) y `Winners.xlsx` (con precios
reales, a diferencia de lo que se asumía en Fase 10 — no todos los Excel del
dueño son "solo nombres"). Se inspeccionaron los 4 archivos reales con
`openpyxl`/lectura directa antes de programar el parser (nada de estructura
adivinada). Decisiones confirmadas con el dueño: ambas fuentes en un mismo
módulo (Excel primero, XML después); emparejamiento contra el catálogo
existente **por nombre** (fuzzy, nunca automático — todo pasa por revisión
manual); margen de costo→precio definido **por marca** con excepción opcional
**por producto**; el costo de compra se guarda pero solo lo ven roles con el
permiso `productos.ver_costo`.

Los 4 archivos de ejemplo se movieron a `PP_API/ejemplos_importacion/` y esa
carpeta se agregó a `.gitignore` (el CFDI trae RFC y datos fiscales reales del
negocio — no debe subirse al remoto).

### Hallazgos de los archivos reales (determinaron el diseño del parser)
- **Excel "bloques de categoría"** (Api-Aba, Agromas, Vimifos): cada hoja es
  una marca; dentro hay bloques de columnas con categorías y sub-líneas
  (ej. "Cerdos > Línea Suprema"). La señal confiable para distinguir
  encabezado de producto **no es texto ni posición, es estilo**: título de
  hoja ~26pt, categoría bold 16pt, sub-línea bold 11pt+relleno, producto
  real no-bold 11pt sin relleno.
- **Excel "tabla con precios"** (Winners): hojas con encabezados
  `Nombre | Kg | Precio` — contradice la suposición de Fase 10 de que
  "el Excel nunca trae precios"; para esta marca sí es una lista de venta
  real, no solo nombres.
- **XML (CFDI 4.0)**: el emisor de la factura es el *distribuidor*, no la
  marca del catálogo (ej. la factura de "Productos Agroindustriales Azteca"
  es en realidad producto Agromas) — la marca no se puede inferir del emisor,
  se asigna a mano por línea/lote. Costo real por unidad ya con descuento:
  `(Importe - Descuento) / Cantidad` (verificado contra `Traslado.Base`).

### Backend
**Migración `e5f6a7b8c9d0`**: `marca.margen_default`, `producto.costo`,
`producto.margen_override`, tablas nuevas `importacion_lote` e
`importacion_linea` (staging de revisión — nada toca el catálogo real hasta
`confirmar_lote`).

- `app/services/importacion_service.py` (nuevo): `parsear_excel` (detecta
  modo tabla-con-encabezados vs bloques-de-categoría por hoja), `parsear_xml_cfdi`,
  `buscar_match` (difflib, normaliza acentos y quita sufijo de peso — pero el
  **dedup dentro del archivo usa una clave SIN quitar el peso**, para no
  colapsar presentaciones distintas del mismo producto como "10 kg"/"4 kg" en
  una sola línea — bug real encontrado y corregido durante la verificación),
  `resolver_margen` (override del producto > margen de la marca > 0),
  `confirmar_lote` (transacción atómica: crea o vincula productos, y si
  `generar_ingreso` además da de alta el ingreso de inventario replicando la
  lógica de `POST /ingreso-inventario/`).
- Los productos creados **sin precio real** (Excel de solo-nombres) se crean
  `activo=false` (van a Suspendidos) para que nunca sean vendibles a $0 sin
  que el dueño los precie primero.
- `app/routers/importacion.py` (nuevo): `POST /importacion/{excel|xml}`,
  `GET /importacion/lotes[/{id}]`, `PATCH .../lineas/{id}`,
  `POST .../confirmar`, `POST .../cancelar` — todos con
  `require_perm("catalogo.importar")`.
- `routers/productos.py`: `GET /productos` y `GET /productos/{id}` ahora
  ocultan `costo` si el usuario no tiene `productos.ver_costo` — pero esos
  endpoints son públicos (Android sin login), así que se agregó
  `get_current_user_optional` en `dependencies.py` (variante de
  `get_current_user` que no falla sin token) en vez de exigir auth.
- Permisos nuevos en `constants.py`: `productos.ver_costo`,
  `catalogo.importar` (ambos en `_GERENTE`). ⚠️ Como `sincronizar_catalogo()`
  solo siembra defaults si el rol **no tiene ningún permiso todavía**, en la
  BD real hay que activarlos a mano para Gerente en **Roles y permisos**
  (ya se hizo en esta sesión).
- `requirements.txt`: se agregó `openpyxl==3.1.5` (ya estaba en el venv, pero
  no declarado).

### Frontend — `punto-peludo-web`
- **`ImportacionPage.tsx`** (nueva, `/importacion`, permiso
  `catalogo.importar`): subir Excel o XML → vista previa editable por línea
  (marca, match sugerido con score, decisión crear/vincular/ignorar, y para
  factura: cantidad/costo/margen%/precio) → acciones masivas (asignar marca a
  las líneas sin marca, aceptar sugerencias, ignorar pendientes) → confirmar
  (con opción de generar ingreso de inventario + sucursal) → historial de lotes.
- **`MarcasPage.tsx`**: campo "Margen por defecto (%)".
- **`ProductosPage.tsx`**: campos "Costo de compra" y "Margen propio (%)" en
  el modal, visibles solo con `has("productos.ver_costo")` — y el payload de
  guardado **solo incluye esas llaves si el usuario tiene el permiso**, para
  no pisar con `null` un costo real si alguien sin el permiso edita el
  producto por otra razón.

### Verificado end-to-end contra la BD real
Con los 4 archivos reales del dueño: Agromas (70 líneas, categorías anidadas
correctas), Api-Aba (177 líneas), Winners (13→18 líneas tras corregir el bug
de dedup), y el CFDI (36 líneas, costo unitario exacto). Se probaron en
navegador y por API: asignación masiva de marca, recálculo de margen/precio al
cambiar de marca, confirmación con creación de producto suspendido (sin
precio) y con producto activo + ingreso de inventario (stock y bitácora
`historial_inventario` correctos), y el ocultamiento de `costo` para
peticiones sin permiso. Se encontró y corrigió en el camino un segundo bug
real: `confirmar_lote` no mandaba `stock_minimo` explícito al crear el
producto, y el `default=5.0` de SQLAlchemy no se aplicaba por ese camino de
inserción (quedaba `NULL` y rompía la respuesta del endpoint).

Quedan en la BD real, a propósito (mismo criterio que sesiones anteriores —
no se borran sin permiso): 3 productos "Producto Prueba Fase11 - borrar"
(suspendidos, $0, de prueba) y varios lotes de importación cancelados en el
historial de `/importacion`.

---

## [2026-07-13] — Fase 10: Descuentos robustos, venta a domicilio, clientes por sucursal, marcas, filtros jerárquicos, suspendidos

**Contexto:** el dueño pidió robustecer los descuentos (varían por cliente Y por
empresa/marca proveedora), agregar categorías padre→hija en los filtros
(marca→especie), un módulo de Marcas (no existía pantalla), recuperar los
productos suspendidos, y aclarar el precio a granel por kg. Se resolvieron dos
bifurcaciones de diseño con el dueño antes de programar: (1) los descuentos NO
se acumulan — gana la regla más específica, y **no se permite crear una regla
de marca y una de producto de esa marca al mismo tiempo** (debe editarse/
desactivarse la existente); (2) **los clientes son propios de una sucursal**,
no globales — si el mismo comprador va a otra sucursal se registra ahí de nuevo.
De paso: se pidió agregar **venta a domicilio** (sin descuentos automáticos) y
cambiar el descuento manual del checkout a **porcentaje** sobre el total.

Se leyeron los dos archivos adjuntos para planear la Fase 11 (import Excel/XML,
la más pesada, queda para después): el Excel `Lista Api-Aba.xlsx` resultó ser
un **catálogo de nombres sin precios** (3 hojas: API-ABA×2, Vimifos; categorías
como encabezados), útil para "sembrar" productos por nombre pero no para
precios. El XML es un **CFDI de compra real** (Productos Agroindustriales
Azteca) con 36 líneas: precio unitario, descuento, cantidad, código SAT y
código interno del proveedor — buena fuente para un futuro "importar factura".

### Backend

**Migración `d4e5f6a7b8c9`** (clientes por sucursal, reglas por sucursal, venta a domicilio):
- `cliente.sucursal_id` (NOT NULL, FK) — backfill automático a la primera
  sucursal para clientes existentes.
- `regla_descuento.sucursal_id` (nullable — NULL = todas las sucursales).
- `venta.tipo_entrega` (Text, default `'tienda'`).

**Descuentos — anti-conflicto y prioridad correcta**
- `app/services/descuentos_service.py` (nuevo): `resolver_sucursal_id` (si hay
  cliente, la sucursal de la regla SIEMPRE es la del cliente) y
  `validar_sin_conflicto` (rechaza con 409 duplicados exactos, y la mezcla
  marca-general + producto-específico de esa marca para el mismo cliente/sucursal).
- `routers/descuentos.py`: reescrito con la validación, `sucursal_id` en
  GET/POST/PUT, nuevo `PUT /descuentos/{id}` (antes no existía edición), y
  **RBAC** (`descuentos.gestionar`) — antes el router estaba completamente abierto.
- `routers/ventas.py`: motor de descuentos corregido — antes el `ORDER BY
  desc(producto_id), desc(marca_id), desc(porcentaje)` dependía del orden NULLS
  de SQL (frágil/incorrecto: una regla general con mayor % podía ganarle a una
  regla de cliente específico). Ahora se calcula un **puntaje de especificidad
  explícito en Python** (producto=100, marca=10, cliente=1) y gana el mayor
  puntaje, con el % como desempate. Además: filtra por `sucursal_id` de la
  venta, y **si `tipo_entrega == "domicilio"` se saltan las reglas por completo**
  (0% automático, siempre).
- `VentaCreateReq.tipo_entrega: str = "tienda"` (`'tienda' | 'domicilio'`,
  validado contra `TIPOS_ENTREGA`).

**Clientes por sucursal**
- `ClienteIn.sucursal_id: int` (obligatorio). `routers/clientes.py`: filtro
  `?sucursal_id=`, y **RBAC** (`clientes.ver` / `clientes.gestionar`) — antes
  también estaba completamente abierto.

**Marcas — RBAC**
- `routers/atributos.py`: las escrituras de marca (crear/editar/eliminar)
  ahora requieren `productos.gestionar` — antes abiertas a cualquiera.

**Filtros jerárquicos**
- `GET /productos/filtros?marca_id=&tipo=` (nuevo, en `routers/productos.py`):
  devuelve solo las especies/categorías que esa marca realmente tiene en su
  catálogo — para no mostrar filtros irrelevantes (si la marca solo vende para
  cerdo/ave, no listar gato/perro).

**Constantes**: `ENTREGA_TIENDA`, `ENTREGA_DOMICILIO`, `TIPOS_ENTREGA` en `constants.py`.

**Otros ajustes**: `llenar_datos.py` — clientes ahora mandan `sucursal_id` y
usan el token (antes iban sin auth). `PlanConteoItem`/reactivación de
productos (`PUT` con `activo:true`) ya funcionaban sin cambios — se verificó,
no se tocó.

### Frontend — `punto-peludo-web`
- **`MarcasPage.tsx`** (nueva pantalla, faltaba por completo): lista + crear/
  editar marca, incluida su tolerancia de fábrica asimétrica.
- **`DescuentosPage.tsx`** (reescrita): en vez de un "alcance" único
  (cliente **o** marca **o** producto), ahora son 3 selectores independientes
  que se pueden **combinar**; columna de sucursal; edición in-place (antes solo
  alta/baja); errores de conflicto del backend visibles en el modal.
- **`PosPage.tsx`**: toggle "En tienda / A domicilio" (con aviso de que a
  domicilio no hay descuentos automáticos); descuento manual cambiado de monto
  fijo a **porcentaje** del total; el cliente del combo ahora se filtra por la
  sucursal del cajero; **el ticket ahora trae el detalle real de la venta ya
  guardada** (`GET /ventas/{id}`) en vez de los precios de catálogo del
  carrito — se detectó y corrigió una inconsistencia visual real (la línea
  mostraba precio de lista, pero el TOTAL ya traía el descuento automático, sin
  cuadrar).
- **`ProductosPage.tsx`**: filtro de marca; filtro jerárquico de especie
  (aparece solo si la marca elegida tiene especies asociadas, vía
  `/productos/filtros`); pestaña **Activos / Suspendidos** con botón
  **Reactivar**; en el formulario, campo "Precio a granel" ahora muestra la
  referencia de la división exacta y aclara que el precio real suele ser mayor
  (no es la división, según lo pedido).
- **`ClientesPage.tsx`**: alta/edición manda `sucursal_id` (la del usuario
  logueado); la lista se filtra por esa misma sucursal.
- `lib/nav.ts` / `App.tsx`: nueva ruta `/marcas`.
- Tipos nuevos/actualizados: `Cliente.sucursal_id`, `ReglaDescuento.sucursal_id`,
  `VentaCreateReq.tipo_entrega`, `TipoEntrega`, `FiltrosJerarquicos`,
  `Producto.especie_id`/`categoria_id` (ya los devolvía el backend, faltaba tiparlos).

### Verificación
- `pytest` 8/8 (sin regresión) · migración completa desde cero (`base → head`,
  las 5 migraciones) validada en una BD de prueba desechable ·
  **`tests/smoke_e2e.py` 22/22** sobre esa misma BD (sin regresiones de fases
  previas) · **verificado en el navegador contra la BD real `negocio`**:
  - Backend, vía script: conflicto de reglas rechazado (409) en ambos
    sentidos (marca→producto y producto→marca); venta a un cliente con regla
    específica de 8% cobra $414 (no los $405 de la regla general de marca al
    10%, ni los $450 de lista) — confirma que gana la regla más específica.
  - UI real: mismo flujo repetido a través del POS (no solo API) con el mismo
    resultado; alternar a "A domicilio" con el mismo cliente cobra $450.00 sin
    ningún descuento; ticket corregido (línea y total ahora cuadran); Marcas,
    Descuentos (combinando cliente+marca), Productos (suspender → aparece en
    "Suspendidos" → Reactivar → vuelve a "Activos"; filtro marca→especie con
    datos reales) probados de punta a punta.

### ⚠️ Nota para producción
Los routers `clientes` y `descuentos` **antes estaban completamente abiertos**
(sin token). Ya tienen RBAC. Si algún cliente externo (app Android antigua) los
llamaba sin `Authorization`, empezará a recibir 401 — coordinar antes de
desplegar. Quedan datos de prueba reales en `negocio` (cliente "Cliente
Fase10", marca "PetFood MX", especie "Perro", varias reglas y ventas de
prueba) — bórralos desde la web si no los quieres conservar.

---

## [2026-07-09] — Fase 9: Auditoría (frontend) — última pantalla del menú

**Contexto:** el dueño pidió revisar todo de golpe, así que se cerró la última
pantalla pendiente (Auditoría) para que las 12 secciones del menú sean
funcionales antes de la revisión.

### Añadido — Frontend
- `pages/AuditoriaPage.tsx` — reemplaza el stub. Lista de productos a auditar
  (vía `GET /auditoria/plan-conteo`) con filtros por tipo, ubicación física
  (derivada de los datos cargados) y atributos JSONB dinámicos (igual patrón
  que Productos). Por cada producto: input de cantidad física, selector de
  tipo de ajuste (o "Automático" para que el backend lo sugiera), botón
  "Registrar" que llama `POST /auditoria/ajuste` y muestra el resultado
  (diferencia, tipo aplicado, tolerancia bajo/alto calculada). Card de
  "Ajustes recientes" con historial vía `GET /auditoria/ajustes`.
- Tipos `PlanConteoItem`, `AjusteResult`, `AjusteListItem`, `TipoAjuste` en
  `lib/types.ts`.
- `App.tsx` — ruta `/auditoria` usa la pantalla real.

### Corregido — hueco real en Productos
El formulario de Productos armaba el payload con `ubicacion_fisica` y
`tolerancia_unidad`, pero **no existían los campos en el modal** — no había
forma de asignarlos desde la UI (bug de "pantalla que se ve completa pero le
falta una pieza"). Se agregaron ambos `Field` al formulario de
`ProductosPage.tsx` (Ubicación física, Tolerancia propia).

### Eliminado
- `pages/StubPage.tsx` — ya no lo usa ninguna ruta; se confirmó con `grep`
  antes de borrarlo.

### Verificado end-to-end contra la BD real (no una de prueba)
Se creó una marca ("PetFood MX") con tolerancia asimétrica (bajo 0.3 / alto
0.1 por pieza), se asignó a un producto real desde la UI de Productos junto
con una ubicación física, y se probaron en el navegador los 3 escenarios de
tolerancia contra `/auditoria/ajuste`:
1. Sistema 12 → físico 10 (faltante 2, dentro de −3.6/+1.2) → **Variación de
   fábrica**, dentro=true.
2. Sistema 10 → físico 5 (faltante 5, fuera de −3.0/+1.0) → **Merma
   operativa**, dentro=false.
3. Sistema 5 → físico 8 (sobrante 3, fuera de −1.5/+0.5) → **Error de
   sistema**, dentro=false.

Los tres resultados fueron exactamente los esperados; el stock e Inventario
quedaron consistentes tras cada ajuste (confirmado también en la pantalla
Inventario). `pytest` 8/8 y `npm run build` sin errores.

**Con esto, las 12 pantallas del menú están operativas y probadas contra
datos reales.** Pendiente: pulido de diseño/branding (ya acordado para después).

---

## [2026-07-09] — Fase 8: Descuentos y Sucursales (frontend) + reconciliación de BD real

**Contexto:** el proyecto se movió de `Documents/Negocio/Punt o de venta/` a
`Documents/Negocio/PDV/` (mismo contenido). El dueño pidió que se terminaran las
pantallas que quedaban como "en construcción" antes de empezar Auditoría, y
verificar todo de verdad (no solo con datos de prueba).

### Añadido — Frontend
- `pages/DescuentosPage.tsx` — reglas de descuento (alcance: catálogo completo /
  cliente / marca / producto), alta y baja. Reemplaza el stub.
- `pages/SucursalesPage.tsx` — tarjetas de sucursal, crear/editar (solo
  SuperAdmin, ya reforzado por el backend). Reemplaza el stub.
- Tipos `ReglaDescuento` y `Marca` en `lib/types.ts`.
- `App.tsx` — ambas rutas ahora usan las pantallas reales.

### Operación — reconciliación de la base de datos real (`negocio`)
Al intentar correr `alembic upgrade head` contra la BD real se detectó que ya
tenía **todo el esquema aplicado** (incluida la Fase 7, `marca.tolerancia_*`)
pero **sin la tabla `alembic_version`** y **sin el índice GIN**
`ix_producto_atributos_extra` (probablemente se migró a mano en algún momento).
Se corrigió sin tocar datos:
1. `CREATE INDEX IF NOT EXISTS ix_producto_atributos_extra ...` (índice faltante).
2. `alembic stamp head` (marca la BD como sincronizada, sin re-ejecutar DDL).

Con esto, `alembic upgrade head` funcionará correctamente para futuras migraciones.

### Verificado end-to-end contra la BD real (no una de prueba)
Con el backend apuntando a `negocio` (default) y la web en `localhost:5173`:
producto creado → surtido de inventario (0→15 pzas) → regla de descuento 5%
general creada → venta en el POS (**el descuento se aplicó solo**: $450 → $427.50)
→ aparece en Ventas → Panel/Inventario reflejan los datos reales. Sucursal
editada (dirección) y usuario nuevo confirmados en sesiones previas también
sobre datos reales. **Todas las pantallas del menú quedan funcionales excepto
Auditoría**, que sigue como stub a propósito (es el siguiente paso).

### Nota
Quedaron datos de prueba en tu BD real (producto "Croquetas Prueba 20kg",
regla "5% en Materia Prima", venta #1): son reales, no de una BD desechable.
Bórralos desde la web si no los quieres conservar.

---

## [2026-07-09] — Fase 7: Tolerancia de fábrica por marca + más pantallas web

### Backend — tolerancia de fábrica asimétrica y por empresa
- La variación de fábrica ahora depende de la **marca/empresa** y es **asimétrica**:
  cuánto puede FALTAR y cuánto puede SOBRAR por empaque son distintos.
- `marca`: columnas `tolerancia_bajo` y `tolerancia_alto` (migración `c3d4e5f6a7b8`);
  expuestas en `MarcaIn`/`Marca` (create/update de marca).
- `producto.tolerancia_unidad` sigue como **override** simétrico por producto.
- `auditoria_service.analizar_tolerancia` reescrita (asimétrica): devuelve
  `(limite_bajo, limite_alto, dentro, tipo_sugerido)`.
- `/auditoria/ajuste`: hereda la tolerancia de la marca (o usa el override del
  producto) y devuelve además `tolerancia_bajo` y `tolerancia_alto`.
- Pruebas: `pytest` 8/8 (incluye caso asimétrico por marca). Verificado e2e contra
  la API: marca que solo llega corta → un faltante es `VARIACION_FABRICA`, un
  sobrante es `ERROR_SISTEMA`.

### Frontend — pantallas nuevas (Vite/React)
- **Productos** (lista + filtros dinámicos JSONB por tipo + crear/editar/suspender).
- **Inventario + Surtir** (stock por sucursal, KPIs, ingreso de mercancía).
- **Usuarios** (solo admin crea/edita, asigna rol y sucursal, cambia contraseña).
- **Clientes** (lista + alta/edición).
- **Ventas** (historial con detalle + **cancelar** venta, restaura stock).
- Diseño: tipografía **Inter** auto-alojada (sin CDN, offline-friendly).
- Verificado en navegador: creación de usuario, listado de productos/inventario/
  clientes, y ciclo de venta → detalle → cancelación.

### Docs
- Nuevo `COMO_EJECUTAR.md` (levantar BD + backend + web paso a paso).

---

## [2026-07-08] — Fase 6: Sistema de permisos (RBAC asignable) + arranque del frontend web

**Contexto:** se decidió una web unificada (POS + admin) donde la visibilidad se
controla por **permisos asignables a roles** (no por rol hardcodeado), y se
arrancó el frontend consumiéndolo.

### Backend — permisos
- Tablas `permiso` (catálogo) y `rol_permiso` (rol↔permiso) + migración
  `b2c3d4e5f6a7`.
- `app/core/constants.py`: catálogo `PERMISOS` (18) y defaults por rol.
- `app/services/permisos_service.py`: `sincronizar_catalogo` (upsert al arrancar,
  siembra defaults sin pisar personalizaciones), `permisos_de_rol`, `set_permisos_rol`.
- `app/core/dependencies.py`: nueva dependencia `require_perm(...)` (por permiso).
- `GET /auth/me`: devuelve el usuario y sus **permisos** (lo usa el frontend).
- Router `roles`: `GET /roles/permisos`, `GET /roles/`, `PUT /roles/{rol}/permisos`
  (protegido con `roles.gestionar`; superadmin siempre todos).
- `app/main.py`: sincroniza el catálogo en el `lifespan`.
- `POST /token` ahora incluye `rol` en la respuesta.

### Frontend — `../punto-peludo-web` (Vite + React + TS + Tailwind)
- App unificada con menú y rutas **dirigidos por permisos** (`/auth/me`).
- Pantallas: Login (JWT), POS (carrito, código de barras por lector, ticket
  imprimible, valida caja), Caja (abrir/cerrar), Panel (KPIs), Roles y permisos
  (matriz editable). Resto: stubs con backend listo.
- Verificado end-to-end en navegador: login → abrir caja → venta (Folio #1,
  ticket) → panel con datos reales → matriz de permisos. Build `tsc + vite` en verde.

### Nota
Los endpoints de POS (`ventas`, `corte`) siguen abiertos en el backend por
compatibilidad con la app Android; la web ya los protege por permiso en el
cliente. Migrar cada endpoint a `require_perm` es un follow-up.

---

## [2026-07-08] — Fases 4 y 5: Transaccionalidad/bugs + Reestructura a paquete `app/`

**Contexto:** con la BD en desarrollo, se cerraron las Fases 4 (bugs y
transaccionalidad) y 5 (reestructura profesional), verificando todo end-to-end.

### Reestructura (Fase 5)
- **Todo el código movido al paquete `app/`**: `app/core/` (config, database,
  security, dependencies, constants), `app/models/`, `app/schemas/`,
  `app/routers/`, `app/services/`. Imports actualizados en todo el proyecto.
  **Arranque nuevo: `uvicorn app.main:app`** (antes `uvicorn main:app`).
- `alembic/env.py` y `crear_superadmin.py` ajustados a los imports `app.*`.
- Nueva **capa de servicios** `app/services/`:
  - `inventario_service.registrar_movimiento` — bitácora reutilizable.
  - `auditoria_service.analizar_tolerancia` — función pura (tolerancia de fábrica).
- `tests/test_unit.py` — 7 pruebas unitarias con **pytest** (tolerancia + RBAC).
- `requirements-dev.txt` (pytest) y `README.md` de arranque.

### Correcciones y transaccionalidad (Fase 4)
- **Bitácora completa**: se escribe en `historial_inventario` en venta,
  cancelación e ingreso (antes solo en ajustes).
- **`SUCURSAL_DEFAULT` ya no hardcodeado**: viene de `settings.SUCURSAL_DEFAULT`
  o del `sucursal_id` del payload al usar el atajo de stock.
- **`usuarios`**: nuevo schema `UsuarioUpdate` (el PUT ya no re-hashea si no cambia
  la contraseña); endpoint `POST /usuarios/{id}/cambiar-password`; validación de
  rol contra `ROLES_VALIDOS` al crear/editar.
- **Bloqueo de sobreventa** configurable (`PERMITIR_STOCK_NEGATIVO`, default off):
  una venta que dejaría stock negativo lanza 400 y revierte toda la transacción.
- `ingreso-inventario` ahora corre dentro de una transacción atómica.

### Config
- `settings.SUCURSAL_DEFAULT` y `settings.PERMITIR_STOCK_NEGATIVO` (+ `.env.example`).

### Verificación
- `pytest -q` → **7/7**.
- Ciclo e2e contra Postgres real (`negocio_test` desechable): `alembic upgrade
  head` + `uvicorn app.main:app` + `tests/smoke_e2e.py` → **22/22 checks** (incluye
  bloqueo de sobreventa ACID y bitácora con COMPRA/VENTA/AJUSTE/CANCELACION).
  Entorno de prueba eliminado al final; la base `negocio` no se tocó.

### ⚠️ Acción para el equipo
- Cambiar el arranque a **`uvicorn app.main:app`** (scripts, systemd, etc.).
- La API (rutas/paths) no cambió → los clientes Android/web no se ven afectados.

---

## [2026-07-08] — Fases 2 y 3: Auditoría avanzada, Atributos JSONB, Dashboard + Modularización

**Contexto:** con la base de datos en modo desarrollo (recreable), se avanzó en
una sola pasada por las Fases 2 y 3, más la modularización y limpieza del
proyecto. Todo verificado end-to-end contra Postgres real (ver Pruebas).

### Añadido
- **Modularización:** `models.py` → paquete `models/` (base, catalogo,
  organizacion, producto, inventario, ventas) y `schemas.py` → paquete
  `schemas/`, ambos con re-export en `__init__.py` (no cambian los imports).
- `constants.py` — tipos de ajuste (`MERMA_OPERATIVA`, `VARIACION_FABRICA`,
  `ERROR_SISTEMA`, `CADUCIDAD`) y tipos de movimiento.
- `alembic/versions/a1b2c3d4e5f6_*.py` — migración: `producto.atributos_extra`
  (JSONB + índice GIN), `producto.tolerancia_unidad`, `producto.ubicacion_fisica`,
  `ajuste_inventario.tipo_ajuste`, `venta_detalle.es_granel` + `cantidad_base`.
- `routers/dashboard.py` — KPIs del SuperAdmin: `/resumen`, `/ventas-por-sucursal`,
  `/top-productos`, `/stock-critico`, `/cajas`, `/rendimiento-financiero`.
- **Auditoría (Fase 2)** en `routers/auditoria.py`: ajuste tipificado con
  cálculo de **tolerancia de fábrica** y sugerencia automática de tipo;
  `/auditoria/plan-conteo` (barrido con filtros por tipo/marca/categoría/
  ubicación/atributos JSONB); `/auditoria/ajustes` (historial por tipo).
- **Atributos dinámicos** en `routers/productos.py`: filtros por dimensiones y por
  JSONB (`?atributos={...}`), y `/productos/atributos-disponibles` (llaves/valores
  por tipo para construir filtros dinámicos en el frontend).
- `tests/smoke_e2e.py` — smoke test e2e (reemplaza `si.py`).

### Modificado
- `database.py` — se **retiró** el códec asyncpg de json (causaba doble
  codificación de JSONB); `databases` ya serializa vía SQLAlchemy. Ver ADR-007.
- `alembic/env.py` — usa la URL de `.env` (fuente única), convertida a psycopg2.
- `routers/ventas.py` — guarda `es_granel`/`cantidad_base`; `cancelar_venta`
  devuelve el stock exacto (ya no adivina).
- `routers/auditoria.py` — protegido con rol Gerente+.
- `crear_superadmin.py`, `llenar_datos.py`, `tests/smoke_e2e.py` — fix de
  codificación de consola en Windows (`stdout.reconfigure('utf-8')`).
- `docker-compose.yml` — se quitó el atributo `version` (obsoleto).

### Eliminado
- `si.py` — script de prueba manual obsoleto (endpoints inexistentes, rol viejo).
- `models.py`, `schemas.py` — reemplazados por sus paquetes homónimos.

### Pruebas (contra Postgres real, base `negocio_test` desechable)
`alembic upgrade head` limpio (2 migraciones) + `tests/smoke_e2e.py`: **19/19
checks en verde** — RBAC (401/200), JSONB persistido como objeto y filtrable,
`atributos-disponibles`, ventas híbridas (bulto=1800, granel=135), stock
400→315, tolerancia de fábrica → `VARIACION_FABRICA`, dashboard (ventas_hoy=1935,
top-productos), y cancelación exacta (→394.8). Entorno de prueba limpiado al final.

### ⚠️ Migración para tu BD de desarrollo
Corre `alembic upgrade head` para aplicar la migración `a1b2c3d4e5f6` a tu base
`negocio`. Los productos existentes quedan con `atributos_extra = {}` (default).

---

## [2026-07-08] — Fase 1: Fundación, Configuración y Seguridad

**Contexto:** el backend estaba funcional pero sin control de acceso (JWT emitido
pero nunca validado), con secretos hardcodeados y sin protocolo de documentación.
Se decidió (con el dueño) avanzar por fases empezando por seguridad, con RBAC
gradual para no romper la app Android mientras se construye la web de administración.

### Añadido
- `MEMORIA.md` — memoria viva: stack, decisiones (ADR-001..006), convenciones,
  modelo de roles, deuda técnica.
- `ROADMAP.md` — backlog completo dividido en 5 fases.
- `CHANGELOG.md` — este archivo.
- `config.py` — configuración centralizada. Lee `.env` con un parser de la
  librería estándar (sin dependencias nuevas). Expone `settings` con
  `DATABASE_URL`, `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`,
  `CORS_ORIGINS`, `TIMEZONE`. Valores por defecto = los de desarrollo actuales,
  así el arranque no se rompe si no hay `.env`.
- `.env.example` — plantilla documentada de variables de entorno.
- `dependencies.py` — capa de seguridad RBAC:
  - `oauth2_scheme` (Bearer) apuntando a `/token`.
  - `get_current_user`: decodifica el JWT y carga el usuario de la BD.
  - `require_roles(*roles)`: dependencia parametrizable; `superadmin` siempre pasa.
  - Constantes `ROL_VENDEDOR`, `ROL_GERENTE`, `ROL_SUPERADMIN`.

### Modificado
- `security.py` — usa `settings.SECRET_KEY`, `settings.ALGORITHM`,
  `settings.ACCESS_TOKEN_EXPIRE_MINUTES` en vez de constantes hardcodeadas.
- `database.py` — `DATABASE_URL` viene de `settings`; zona horaria desde
  `settings.TIMEZONE`; corregido `import` faltante de `timezone`.
- `main.py` — CORS toma los orígenes de `settings.CORS_ORIGINS` (soporta Android
  + dominio(s) de la web).
- `routers/auth.py` — el token usa la expiración de `settings`.
- `routers/usuarios.py` — RBAC: gestión de usuarios restringida a `superadmin`.
- `routers/sucursales.py` — RBAC: crear/editar/eliminar sucursal → `superadmin`;
  lectura abierta.
- `routers/productos.py` — RBAC: crear/editar/eliminar → `gerente`+; lectura
  abierta (el POS la necesita).
- `routers/informes.py` — RBAC: reportes → `gerente`+.
- `requirements.txt` — re-generado en UTF-8 limpio (estaba en UTF-16 con espacios).
- `llenar_datos.py` — rol del usuario semilla `admin` → `superadmin` (rol canónico).

### Notas para el frontend (⚠️ coordinar)
Tras esta fase, **requieren token Bearer** los siguientes grupos de endpoints:
`/usuarios/*` (superadmin), `/sucursales` escrituras (superadmin),
`/productos` escrituras (gerente+), `/informes/*` (gerente+).
El POS (ventas, corte, lectura de productos/inventario) sigue **abierto** en esta
fase para no romper la app Android. Se coordinará el cierre total en fases siguientes.
