# Empezar aquí — traspaso de sesión

> **Si eres una IA retomando este proyecto: lee este archivo completo antes de
> tocar nada.** No le preguntes al usuario "qué se hizo antes" — todo está aquí
> y en los MD que este archivo enlaza. Si necesitas más detalle de una
> decisión puntual, ve a `MEMORIA.md` (los ADR) o `CHANGELOG.md` (qué archivo
> se tocó y por qué, en orden cronológico inverso).

> ## ✅ FASE 15: VERIFICADA end-to-end (2026-07-16)
> El código de la Fase 15 se había escrito por error (una sesión
> mal-interpretó "escríbelo" —que se refería al MD del plan— como luz verde
> para programar) y la sesión anterior se cortó antes de verificar nada. Una
> sesión de retoma **ya verificó todo de punta a punta sin reescribir código**:
> 37 pytest + `smoke_e2e.py` en verde, y cada pantalla probada en el navegador
> contra la BD real (Productos, POS, Reportes, y regresión del resto). Detalle
> en `CHANGELOG.md` ("Fase 15 VERIFICADA") y `PLAN_FASE15.md §-1`.
> **Sigue sin commitear** (el dueño commitea a mano). Decisiones que aún son
> del dueño: clasificar los 4 productos Agromas ambiguos (se ven con el botón
> "Sin especie" en Productos) y confirmar/cancelar los 2 lotes de importación
> en `revision`.

Última actualización: **2026-07-17**. Fase 14, **Fase 15** y **Fase 16**
(módulo Listas gráfico) están **completadas**. El hallazgo de seguridad de
Fase 13 (`.env` con `SECRET_KEY` de ejemplo) quedó resuelto y verificado en
Fase 15: existe un `.env` real con secreto generado de 64 chars, el backend
arranca limpio y el login funciona con él. Nota: al levantar el backend en
Fase 15 se detectó que el `.venv` no tenía `openpyxl`/`pdfplumber` (sí en
`requirements.txt`); ya instalados — si recreas el venv, corre `pip install
-r requirements.txt`.

> ## ✅ FASE 16 — Módulo Listas gráfico: COMPLETADA (2026-07-17)
> El dueño pidió volver **gráfico** el módulo **Listas** y, en la misma
> sesión, dio luz verde explícita para programarlo ("empieza a programar la
> fase 16 has todo tu como te dije") después de confirmar las 8 decisiones de
> `PLAN_FASE16.md §6`. Se implementó completo: parser de las plantillas Excel
> (clasifica encabezado/producto por formato de celda, dos paneles
> independientes), vínculo automático producto↔plantilla por nombre con
> reglas de contexto para no cruzar especies (nunca "adivina"), nueva tabla
> `lista_plantilla_fila` **editable desde la web** (CRUD completo, no solo
> lectura — decisión §6.6), export Excel fiel al estilo de marca, y
> `ListasPage.tsx` con la vista gráfica de dos paneles + pestañas para las 3
> hojas de Api-Aba. 48 pytest en verde (11 nuevas) + verificado en el
> navegador contra la BD real. Detalle técnico completo en §5h y en
> `CHANGELOG.md` ("Fase 16")/`MEMORIA.md` (ADR-026, ADR-027).
> **Sigue sin commitear** (el dueño commitea a mano). Decisión pendiente del
> dueño: confirmar si los 26 productos Agromas ya confirmados deben
> **renombrarse** al nombre corto de la plantilla, o si vincularlos (lo que
> se hizo, sin tocar el nombre) es suficiente — ver §5h.

---

## 1. Qué es esto en una frase

**Punto Peludo**: ERP + POS multi-sucursal para un negocio de alimento animal,
accesorios y farmacia veterinaria (México). Un backend FastAPI sirve a dos
clientes: una app Android (POS del cajero) y una web React (panel de
administración + POS también). Todo vive bajo `Documents/Negocio/PDV/`
(⚠️ esta carpeta se llamaba `Punt o de venta` antes del 2026-07-13; si ves esa
ruta en documentación vieja o en la memoria persistente de Claude, es la
misma carpeta renombrada, no un proyecto distinto).

| Carpeta | Qué es | Stack |
|---|---|---|
| `PP_API/` | Backend | FastAPI + SQLAlchemy Core (NO ORM) + `databases` async + PostgreSQL + Alembic |
| `punto-peludo-web/` | Frontend web | Vite + React + TypeScript + Tailwind |
| `PuntoPeludo/` | App Android | Kotlin (POS del cajero; no se tocó el código en ninguna sesión — sí se investigó su paridad con la web en Fase 12c, ver §5e) |

## 2. Estado actual: todo funcional, incluida la importación de catálogo

### ✅ Hallazgo de seguridad del `.env` — RESUELTO y verificado (Fase 15)
Ya existe un `.env` real en `PP_API/` con un `SECRET_KEY` generado de 64 chars
(no el de ejemplo). Verificado en Fase 15: el backend arranca limpio con él y
el login (Admin/admin123) funciona. `.env` está en `.gitignore`, nunca se
commitea. Efecto ya asumido: al generar el secreto se invalidaron las sesiones
JWT viejas — sólo hay que volver a iniciar sesión, nada más.
Sigue pendiente (fuera del alcance de Fase 15): el puerto de Postgres en
`docker-compose.yml` se expone a toda la red local, no solo a `localhost`
(§5f tiene el detalle completo de este y los demás hallazgos del reanálisis
de Fase 13).

- **Las 17 pantallas del menú web están implementadas y verificadas contra la
  BD real**: Login, POS, Caja, Panel, Productos, Marcas, Inventario, Usuarios,
  Clientes, Ventas, Descuentos, Sucursales, Auditoría, Roles y permisos,
  Importar catálogo, Configuración, Listas, y ahora **Reportes** (Fase 15).
- **Backend**: RBAC por permisos (no por rol hardcodeado), multi-sucursal,
  auditoría con tolerancia de fábrica asimétrica por marca, motor de
  descuentos con anti-conflicto, venta a domicilio, clientes por sucursal,
  **importación de catálogo desde Excel, factura XML/CFDI y PDF** (Fase 11).
- **Reimpresión de ticket** (Fase 11d, ver §5b): en **Ventas**, el detalle de
  cualquier venta ya realizada tiene un botón "Reimprimir ticket" que abre el
  mismo ticket imprimible que se ve al cobrar en POS. Desde Fase 12 (ver
  §5c), además muestra un aviso `*** REIMPRESIÓN ***` para no confundirlo
  con el original.
- **6 mejoras (Fase 12)**: advertencia de precio menor en importación,
  filtro de Ventas por cliente/vendedor, exportar Ventas/Inventario/
  Auditoría a Excel, historial de costo/precio por producto, y 28 pruebas
  automatizadas nuevas para Fase 10/11. Ver §5c para el detalle.
- **sku automático desde importación (Fase 12b)**: al confirmar un lote, el
  código de proveedor de cada línea rellena `producto.sku` si está libre y
  el producto no tenía uno. Ver §5d.
- **Reporte imprimible/PDF de Ventas + investigación Android (Fase 12c)**:
  botón "Imprimir / PDF" en Ventas (sin dependencia nueva); investigación de
  solo lectura del código Android que confirmó que no tiene reimpresión de
  ticket ni selector de sucursal. Ver §5e.
- **Configuración del negocio + surtir por lista auditable (Fase 13)**: nueva
  pantalla **Configuración** (nombre/dirección/teléfono/RFC usados en el
  ticket y reportes); "Surtir mercancía" ahora acepta una lista completa de
  productos en un solo ingreso, con **"Historial de ingresos"** para
  auditar. Ver §5f (incluye los 4 hallazgos del reanálisis general que pidió
  el dueño, ninguno implementado a propósito).
- **POS con filtros/granel visibles + módulo Listas (Fase 14, esta ronda)**:
  el Punto de Venta ahora filtra por marca + especie/animal + categoría, la
  búsqueda queda acotada al filtro activo, la venta a granel es una opción
  visible en la tarjeta (antes escondida), y las tarjetas son más grandes.
  Se corrigieron 2 lotes de importación reales del dueño que estaban mal
  etiquetados (sin confirmarlos — esa decisión sigue siendo suya). Nueva
  pantalla **Listas** (`/listas`): precios actuales agrupados por marca,
  exportables a Excel e imprimibles. Ver §5g.
- **Fase 15 — VERIFICADA y completada (ver banner arriba, `CHANGELOG.md`
  "Fase 15 VERIFICADA" y [`PLAN_FASE15.md`](PLAN_FASE15.md) §-1)**: las 8
  tareas del plan (seguridad `.env`, permisos de Gerente, catálogo de 9
  especies/7 categorías, clasificación de 22 de los 26 productos de Agromas,
  mejora de la importación, filtros en cascada de Productos y POS sin "Tipo"
  ni JSONB, y nueva pantalla **Reportes**) quedaron **probadas end-to-end**:
  37 pytest + `smoke_e2e.py` en verde y cada pantalla verificada en el
  navegador contra la BD real. Sin commitear todavía (el dueño commitea a
  mano). Pendiente sólo del dueño: clasificar los 4 productos Agromas ambiguos
  (botón "Sin especie" en Productos) y confirmar/cancelar los 2 lotes en
  `revision`.
- **Pulido de diseño/branding** (colores, logo, tipografía): sigue fuera de
  alcance. El dueño dijo explícitamente "eso después" — no lo ataques a
  menos que te lo pida.
- **Explícitamente descartado, no lo propongas de nuevo**: alertas de stock
  por correo (nunca se va a hacer), paridad con la app Android (necesita un
  entorno donde compilar Kotlin, no disponible aquí), limpieza de datos de
  prueba en la BD real (solo si el dueño lo pide explícitamente), puerto de
  Postgres expuesto a la red (hallazgo válido de Fase 13 pero fuera del
  alcance que pidió el dueño para Fase 15).

## 3. Cómo arrancar todo

Instrucciones completas y solución de problemas en **`COMO_EJECUTAR.md`**.
Resumen:
```bash
# terminal 1 — base de datos + API
cd PP_API
docker compose up -d
alembic upgrade head          # si es la primera vez en esta máquina
python crear_superadmin.py    # solo si no existe el usuario Admin
uvicorn app.main:app --reload

# terminal 2 — web
cd ../punto-peludo-web
npm run dev                   # http://localhost:5173
```
Login: **`Admin` / `admin123`**.

**Los procesos de backend/web que yo (la sesión anterior) dejé corriendo en
background NO persisten entre sesiones de Claude Code** — si el usuario dice
que ya no responden, es normal, hay que relanzarlos con lo de arriba.

⚠️ **Quirks conocidos de este entorno sandbox (no del proyecto)**:
1. A veces el puerto 8000 queda "fantasma" — `netstat` muestra un PID
   escuchando ahí pero ni `Get-Process` ni `taskkill` lo encuentran, y aun
   así el bind falla con "address already in use". Si te topas con esto:
   espera unos segundos y reintenta, o usa un puerto libre distinto (ej.
   8080, 8300) y actualiza `punto-peludo-web/.env` → `VITE_API_URL` para que
   coincida — pero antes de terminar la sesión, regresa `.env` a
   `http://127.0.0.1:8000` (el estándar del proyecto).
2. **Docker Desktop y cualquier proceso que hayas dejado corriendo
   (backend, `npm run dev`) NO sobreviven entre turnos largos de
   conversación** — no solo entre sesiones distintas de Claude Code. Pasó
   dos veces en la sesión que cerró con este traspaso: `docker ps` dejó de
   responder (`docker Desktop` se había cerrado solo) después de un rato sin
   usarlo, incluso dentro de la misma conversación. Si `docker compose up -d`
   falla con un error de pipe/conexión, lanza `Docker Desktop.exe`
   (`C:\Program Files\Docker\Docker\Docker Desktop.exe`) y espera ~20s antes
   de reintentar. **Al cierre de esta sesión, ni el backend ni `npm run dev`
   quedaron corriendo a propósito** (no tenía caso dejarlos, no iban a
   sobrevivir al cambio de sesión) — vas a tener que levantar todo desde
   cero con los comandos de arriba, incluido `docker compose up -d`.

## 4. ⚠️ Cosas que hay que saber antes de tocar código

### 4.1 Hay cambios SIN COMMITEAR en ambos repos
Ni yo ni sesiones previas hicimos `git commit` de los cambios de la Fase 10
(ni de partes de fases anteriores en el frontend). Antes de asumir que algo
"no existe", corre `git status` — probablemente el archivo sí está, solo no
está commiteado. **No hagas commit sin que el usuario lo pida explícitamente**
(así es como él trabaja: commitea manualmente cuando quiere).

Al cierre de esta sesión (Fase 10 a Fase 15-sin-verificar acumuladas), sin
commitear en `PP_API/` — **modificados**: `.gitignore`, los 4 MD
(`MEMORIA/ROADMAP/CHANGELOG/COMO_EJECUTAR`), `requirements.txt`,
`llenar_datos.py`, `app/core/{constants,dependencies}.py`, `app/main.py`,
`app/models/{__init__,catalogo,inventario,organizacion,producto,ventas}.py`,
`app/routers/{atributos,auditoria,clientes,descuentos,inventario,productos,ventas,informes}.py`
(`productos.py`: `GET /productos/exportar/excel` de Fase 14 + `subcategoria_id`
y `GET /productos/filtros` extendido de Fase 15 sin verificar;
`informes.py`: `reporte-surtidos` reescrito para agrupar por `lote_id` real,
Fase 15 sin verificar),
`app/schemas/{__init__,catalogo,inventario,producto,ventas}.py`,
`app/services/importacion_service.py` (Fase 15 sin verificar: resuelve
`categoria_id` en `confirmar_lote`); y **nuevos**:
`EMPEZAR_AQUI.md`, `.env` (Fase 15 sin verificar: `SECRET_KEY` real generado
— **está en `.gitignore`, nunca debe commitearse**),
`alembic/versions/{d4e5f6a7b8c9,e5f6a7b8c9d0,f6a7b8c9d0e1,a7b8c9d0e1f2,b8c9d0e1f2a3}_*.py`,
`app/{models,routers,schemas}/{importacion,configuracion}.py`,
`app/services/{descuentos,export,historial_precio}_service.py`,
`tests/test_fase10_11_unit.py`, `PLAN_FASE15.md` (ya NO es solo el plan —
ver su §-1, documenta código ya escrito sin verificar),
`sembrar_especies.py`, `clasificar_agromas.py` (scripts de Fase 15 sin
verificar, ya corridos contra la BD real).
(`desktop.ini` en la raíz también sale como sin trackear — es un archivo de
Windows, no de este proyecto, ignóralo.)

**Fase 16 (esta ronda) añade, sin commitear todavía**: `.gitignore`
(+`app/assets/plantillas/`), `PLAN_FASE16.md`/`EMPEZAR_AQUI.md`/
`CHANGELOG.md`/`MEMORIA.md`/`ROADMAP.md` (documentación), `app/main.py`
(+router `listas`), `app/models/{__init__,lista_plantilla}.py`,
`app/schemas/{__init__,lista_plantilla}.py`, `app/core/constants.py`
(+`LISTA_PLANTILLA_MARCAS`), `app/services/export_service.py`
(+`generar_excel_plantilla`); y **nuevos**: `app/routers/listas.py`,
`app/services/lista_plantilla_service.py`,
`alembic/versions/c9d0e1f2a3b4_lista_plantilla_fila.py`,
`tests/test_fase16_unit.py`, `app/assets/plantillas/*.xlsx` (gitignored, no
va a aparecer en `git status` — copia de `ejemplos_importacion/`).

Sin commitear en `punto-peludo-web/` — **modificados**: `README.md`,
`src/App.tsx` (+ruta `/reportes`, Fase 15 sin verificar),
`src/auth/AuthContext.tsx`, `src/components/Layout.tsx`,
`src/index.css` (regla `.printable` genérica, Fase 12c),
`src/lib/{api,nav,types}.ts` (`nav.ts`+`types.ts` con la entrada/tipos de
Reportes, Fase 15 sin verificar),
`src/pages/{CajaPage,ClientesPage,InventarioPage,PosPage,ProductosPage,VentasPage}.tsx`
(`InventarioPage.tsx` reescrita en Fase 13: surtir por lista + historial;
`PosPage.tsx` reescrita en Fase 14, filtros reordenados en Fase 15 sin
verificar; `ProductosPage.tsx` reescrita en Fase 15 sin verificar: se quitó
Tipo/JSONB, se agregó Categoría/Subcategoría/Especie),
`src/pages/StubPage.tsx` (borrado); y **nuevos**: `AuditoriaPage.tsx`,
`ConfiguracionPage.tsx`, `DescuentosPage.tsx`, `ImportacionPage.tsx`,
`ListasPage.tsx`, `MarcasPage.tsx`, `SucursalesPage.tsx`,
`ReportesPage.tsx` (Fase 15 sin verificar), `src/components/TicketModal.tsx`.
`ListasPage.tsx` fue **reescrita de nuevo en Fase 16** (vista gráfica de dos
paneles + edición de estructura); `src/lib/types.ts` también gana los tipos
`ListaPlantilla*`/`PlantillaDisponible`/`ImportarPlantillaResumen` de Fase 16.
(`.env` de este repo, el del frontend, también sale modificado en
`git status` — ver la nota del puerto "fantasma" arriba en §3 antes de
asumir que su valor actual es el correcto; debería decir
`http://127.0.0.1:8000` al cierre de una sesión normal — se confirmó así al
cierre de esta.)

Los 4 archivos de ejemplo de Fase 11 (`Lista Agromas.xlsx`, `Lista
Api-Aba.xlsx`, `Winners.xlsx`, el CFDI XML) están en
`PP_API/ejemplos_importacion/`, que está en `.gitignore` a propósito (traen
RFC y datos fiscales reales del negocio) — no van a aparecer en `git status`
y no deberían subirse al remoto.

### 4.2 La BD real `negocio` tiene una mezcla de datos reales y de prueba
No es una base desechable — es la que usa el dueño. Durante las últimas
sesiones se dejaron ahí registros de verificación real (no se borraron porque
no es mi lugar decidir borrar datos sin permiso). Al 2026-07-15:
- Usuario: `Admin` (superadmin) — real, es el del dueño.
- Clientes: `dad` (id 1) y `Cliente Fase10` (id 34) — **el segundo es mío, de
  prueba**; el primero parece del dueño (nombre raro, probablemente prueba suya).
- Productos: `Croquetas Prueba 20kg` (id 1, **mío, de prueba**, stock **5**
  tras la prueba de surtido por lista de Fase 13, antes 3), `Agromas cerdo
  engorda` (id 2, **del dueño**, lo creó él entre sesiones, stock **0**
  Bulto — se probó y se revirtió al valor original, ver §5f), y de la
  verificación de Fase 11: `MAS CARNE 12% ESENCIAL 25 kg` (id 6, **mío, de
  prueba** — `precio_base` **$215.00** desde Fase 12, stock **10** pza — se
  probó y se revirtió al valor original en Fase 13, ver §5f) / `BORREGO
  ESENCIAL 25 kg` ×2 (id 7 stock **24** pza tras Fase 13, id 8 sin cambios,
  **míos, de prueba**, activos con costo/precio/stock reales — vinieron de
  importar el CFDI de ejemplo) y 3× `Producto Prueba Fase11 - borrar`
  (**míos, de prueba, suspendidos, $0** — no son vendibles, quedaron así a
  propósito). De la verificación de Fase 12b (ver §5d): `Producto Nuevo
  Prueba SKU 10 kg`, `Producto Duplicado Prueba SKU 5 kg`, `Producto Sin Sku
  Prueba` (ids 9-11, **míos, de prueba, suspendidos**).
- Configuración del negocio (Fase 13, ver §5f): nombre "Punto Peludo"
  (default, sin cambiar), dirección "Calle Falsa 123, Col. Centro" y
  teléfono "55 1234 5678" — **datos de prueba míos, no reales del dueño**,
  fáciles de identificar y reemplazar desde `/configuracion` cuando el dueño
  tenga los datos reales del negocio.
- Historial de ingresos (`/inventario` → "Historial de ingresos", nuevo en
  Fase 13): 2 lotes de prueba — uno con productos reales del dueño (ids 2 y
  6, proveedor "Proveedor de prueba", **el stock ya se revirtió**, ver §5f)
  y otro con productos de prueba (ids 1 y 7, proveedor "Proveedor Prueba
  Fase13"). No hay endpoint para borrarlos (es bitácora de auditoría a
  propósito) — no afectan el stock real, se pueden ignorar.
- Marcas: `PetFood MX` (id 1, **mía, de prueba**, tolerancia 0.3/0.1,
  **margen_default 20%** — lo puse yo para probar el cálculo de margen de
  Fase 11), `z` (id 2, **del dueño**, nombre placeholder, margen_default 0%),
  `Agromas` (id 3, **real, margen_default 16%**) y `Api-Aba` (id 4, **real,
  margen_default 10%**) — estas dos últimas las creó el dueño, no yo. ⚠️
  **Nueva, encontrada en Fase 16, no documentada antes**: `SmokeMarca` (id 5)
  + producto `Smoke Bulto 40kg` (id 38) + una regla de descuento — quedaron
  de una corrida anterior de `tests/smoke_e2e.py` que no se limpió sola (el
  script no es idempotente). Tienen una venta real (`venta_detalle`)
  asociada — **no se pueden borrar sin romper esa venta**, así que
  `smoke_e2e.py` va a seguir fallando en el paso `POST /marcas/` (colisión de
  nombre único) hasta que alguien decida qué hacer con ellos. No es un bug de
  Fase 16, es preexistente — no lo confundas con datos reales del negocio.
- ⚠️ **Importante — el catálogo real ya no es tan sparse como decían
  versiones viejas de este archivo**: al investigar en Fase 14 se encontró
  que **Agromas ya tiene 26 productos reales confirmados** (nombres reales:
  "POLLO ENGORDA CP 25 kg", "CERDO SUPREMA CRECIMIENTO 25KG", etc.) — el
  dueño debió confirmar uno de los lotes de importación por su cuenta entre
  sesiones, sin que yo lo hiciera. **Api-Aba, en cambio, sigue en 0
  productos.** Antes de asumir que el catálogo real está vacío, corre
  `GET /productos/?marca_id=X` para cada marca y confírmalo tú mismo — no
  confíes en snapshots viejos de este archivo.
- ⚠️ **Nuevo, Fase 15 sin verificar**: tabla `especie` pasó de 1 fila
  ("Perro") a 10 — se agregaron Cerdo(2), Pollo(3), Pavo(4), Ganado de
  engorda(5), Ganado lechero(6), Ave de postura(7), Gallo(8), Ovino(9),
  Conejo(10), todas **reales**, no de prueba. Tabla `categoria` pasó de 0 a
  7 filas: Suprema(1), Óptima(2), Súper Yema(3), CP(4), Porcimas(5),
  Regio(6), Más Lechón(7), también reales. De los 26 productos reales de
  Agromas, **22 quedaron con `especie_id`/`categoria_id` asignados**
  (clasificación automática por palabra clave, ver `PLAN_FASE15.md §-1`); 4
  siguen sin clasificar a propósito (`AGROMIX MIGAJA CC` ×2, `ESPUELA DE ORO
  MP`, `INVENCIBLE 26 INICIO`) para que el dueño los revise — la pantalla
  Productos tiene un botón "Sin especie" para encontrarlos rápido. El rol
  Gerente también quedó con `productos.ver_costo` y `catalogo.importar`
  agregados. **Nada de esto se verificó en el navegador todavía.**
- `/importacion` (pantalla de Fase 11): historial con muchos lotes
  `cancelado` de mis pruebas (Agromas, Api-Aba, Winners, CFDI, e intentos
  fallidos de Fase 11c antes de arreglar el bug del PDF) — no tocaron el
  catálogo real, se pueden ignorar o borrar sin riesgo. También hay varios
  lotes de prueba `confirmado` de la verificación de Fase 12b (nombres de
  archivo `_test_sku*.xml`) — sí crearon/vincularon productos reales, pero
  esos productos quedaron suspendidos (ver arriba), así que no afectan el
  catálogo vendible.
  **Siguen 2 lotes reales en `revision`** (no confirmados, es decisión del
  dueño): el PDF `Tlaxcala Api Lista unica 8 Jul 24.pdf` (**219 líneas**, ya
  con el bug de fragmentos de PDF corregido desde hace varias rondas) y el
  Excel `Formato de pedidos_ PLANTA TLX LISTA 01 2025.xlsx` (94 líneas). En
  Fase 14 se corrigió la marca de ambos — el PDF tenía "PetFood MX" puesta
  (marca de prueba usada mientras se depuraba el parser, ya no tiene sentido
  para un archivo que es literalmente "Api Lista") y el Excel no tenía
  ninguna marca — ahora el PDF tiene Api-Aba (margen recalculado a 10% real)
  y el Excel tiene Agromas (nombres con "ESENCIAL", línea de Agromas). **No
  se confirmó ninguno de los dos** — solo se corrigieron metadatos de líneas
  todavía `pendiente`, sigue siendo el dueño quien decide crear/vincular
  cada línea. Si el historial tiene MÁS de un lote en `revision` con el
  mismo nombre de archivo, el más reciente (fecha/hora más nueva) es el
  bueno — los anteriores son intentos de depuración, cancélalos.
- Reglas de descuento: 4 activas, mezcla de mías (`Cliente VIP marca 8%`) y
  del dueño (`5% en Materia Prima`, `er4`, `wqe` — nombres placeholder, obvio
  que las creó probando la UI).
- Ventas #1 a #10 — todas de pruebas (mías o del dueño probando).

**No borres nada de esto sin preguntar.** Si el dueño quiere limpiar la BD de
pruebas antes de ir a producción, es su decisión — ofrécele hacerlo, no lo
hagas por tu cuenta.

### 4.3 La memoria persistente de Claude está en la ruta VIEJA
El sistema de memoria entre sesiones de Claude Code guarda archivos en
`C:\Users\baruc\.claude\projects\<hash-de-la-ruta>\memory\`. Como la carpeta
se renombró de `Punt o de venta` a `PDV`, **la memoria de sesiones anteriores
vive bajo el hash de la ruta VIEJA**
(`C--Users-baruc-Documents-Negocio-Punt-o-de-venta-PP-API`), no bajo la nueva.
Una sesión nueva iniciada desde `PDV/` probablemente NO la va a ver
automáticamente. **Por eso existe este archivo — no dependas de la memoria de
Claude, todo lo que importa está en los MD de este repo.** Si quieres migrar
esa memoria a la ruta nueva, es opcional y de bajo valor (este archivo ya
cubre lo importante).

## 5. Fase 11 — Importación desde Excel/XML/PDF: COMPLETADA (3 rondas)

Ya no es la siguiente tarea grande — se implementó en una primera sesión y se
amplió/corrigió en dos rondas más con feedback de uso real del dueño. Detalle
técnico completo en `CHANGELOG.md` (entradas Fase 11, 11b, 11c) y `MEMORIA.md`
(ADR-015, ADR-016, ADR-017). Resumen para no tener que ir a buscarlo:

- Pantalla **Importar catálogo** (`/importacion`), módulo aparte de Productos
  como pidió el dueño. Soporta **Excel** (dos formatos, detectados por hoja:
  solo nombres agrupados por categoría, o tabla con encabezados que puede
  traer precio de venta directo O costo de proveedor — `openpyxl`), **factura
  XML/CFDI**, y **PDF** de listas de precio de distribuidor (`pdfplumber`,
  nueva dependencia).
- Todo pasa por vista previa editable — nada se crea automático, el dueño
  decide `crear`/`vincular`/`ignorar` por línea. Botones masivos: asignar
  marca a todas, aceptar sugerencias, marcar vinculados para actualizar
  precio, ignorar pendientes.
- El precio de XML y PDF **siempre** se trata como costo (pasa por el cálculo
  de margen de la marca); el de Excel depende de qué encabezado traiga la
  columna (`Precio` = venta directa, `Precio de lista`/`Costo` = costo).
- Dos bugs reales de parseo encontrados y corregidos en la segunda ronda
  (búsqueda de encabezado limitada a 5 filas cuando el archivo real lo trae
  hasta la fila 14; encabezados de PDF colándose como fila de "producto") —
  detalle en `CHANGELOG.md`.
- Único trabajo pendiente relacionado (opcional, no pedido): guardar el
  código de proveedor (`NoIdentificacion`/`Item`/`Código`) como
  `producto.sku` para poder emparejar por código en importaciones futuras
  del mismo proveedor, en vez de solo nombre.

## 5b. Ronda 4 (esta sesión) — Reimpresión de ticket + verificación total

El dueño no había revisado nada de la Fase 11c todavía, pero pidió aprovechar
la sesión para verificar **todo** el sistema (sobre todo el cambio de
sucursal) y confirmar que se pudiera reimprimir el ticket de una venta ya
hecha. Detalle técnico en `CHANGELOG.md` ("Fase 11d") y `MEMORIA.md`
(ADR-018). Resumen:

- **Reimpresión de ticket construida desde cero** (no existía): en Ventas,
  el detalle de cualquier venta tiene un botón "Reimprimir ticket" que abre
  el mismo componente de ticket que usa POS al cobrar
  (`src/components/TicketModal.tsx`, extraído de `PosPage.tsx` para
  compartirse). `GET /ventas/{id}` ahora devuelve `usuario_nombre` y
  `sucursal_nombre` (join en el backend) para no exigirle permisos extra al
  vendedor solo por ver el ticket.
- **Barrido de verificación**: las 14 pantallas del menú probadas contra la
  BD real — todas funcionales. Se puso atención especial al selector de
  sucursal (superadmin): se confirmó que cambiar entre Centro/Norte actualiza
  correctamente Ventas (folio, lista, total), además de las 6 pantallas que
  ya lo tenían desde la ronda 11b (Auditoría, Caja, Clientes, Descuentos,
  Inventario, POS). `DashboardPage.tsx` se confirmó que **sigue sin filtrar a
  propósito** (es la vista global/comparativa entre sucursales).
- Fix cosmético encontrado en el camino: las cantidades en el ticket se
  mostraban como `1.000×` en vez de `1×` (no usaba el formateador `qty()` que
  ya se usa en el resto de la app) — corregido.
- No se encontraron bugs funcionales nuevos en el barrido (a diferencia de
  las rondas 11b/11c, donde sí aparecieron bugs reales de parseo).

## 5c. Fase 12 (esta ronda) — 6 mejoras propuestas, implementadas

Al cerrar la Fase 11d se le presentó al dueño una lista de 9 ideas de mejora
(análisis, no implementadas de entrada). Pidió implementar las primeras 6 de
una vez. Detalle técnico completo en `CHANGELOG.md` ("Fase 12") y
`MEMORIA.md` (ADR-019, ADR-020). Resumen:

1. **Advertencia de precio menor en importación**: la vista previa marca en
   ámbar cuando el precio sugerido de una línea vinculada queda por debajo
   del precio actual del producto (posible error o cambio real de costo que
   convenga revisar antes de aplicar).
2. **Marca "REIMPRESIÓN"** visible en el ticket solo cuando se abre desde
   Ventas (nunca en el cobro original de POS).
3. **Filtro de Ventas por cliente y vendedor** — el selector de vendedor se
   arma con los nombres ya presentes en las ventas cargadas, sin pedirle al
   backend el endpoint de usuarios (restringido a superadmin). Ver ADR-019.
4. **Exportar a Excel** en Ventas, Inventario y Auditoría (`openpyxl`, botón
   "Exportar Excel" en cada pantalla, respeta los filtros activos). No se
   agregó exportación a PDF — se dejó fuera para no meter una dependencia
   nueva sin que el dueño la pidiera explícitamente.
5. **Historial de costo/precio por producto**: nueva tabla
   `producto_historial_precio`, botón de reloj en cada fila de Productos
   (mismo permiso que ver costo) que abre un modal con la bitácora de
   cambios. Se registra tanto en edición manual como al confirmar una
   importación que actualiza un producto vinculado. Ver ADR-020.
6. **28 pruebas automatizadas nuevas** (`tests/test_fase10_11_unit.py`, sin
   BD) para Fase 10 (especificidad de reglas de descuento) y Fase 11
   (matching/normalización, cálculo de margen, parseo de CFDI) — antes
   dependían solo de verificación manual. Suite completa: 37 pruebas
   (`pytest -q` desde `PP_API/`).

**Quedaron sin implementar (ideas #7-9 de la lista original de 9)**, por si
el dueño las quiere en una próxima ronda: alertas proactivas de stock
crítico, revisar paridad de la app Android con la web (selector de sucursal,
reimpresión de ticket), y limpieza de datos de prueba en la BD real antes de
producción.

Verificado en el navegador contra la BD real: precio de importación con
advertencia (se subió un XML de prueba `_test_warning_precio.xml` con un
producto que hace match 100% contra `MAS CARNE 12% ESENCIAL 25 kg` y un
precio de venta sugerido de $120 contra un precio actual de $215 — se vio la
advertencia correctamente y **se canceló el lote después de verificar**, vía
`POST /importacion/lotes/{id}/cancelar`, no quedó en el historial como
`revision`); reimpresión con badge; filtro de Ventas (cliente y vendedor,
incluida la combinación); exportación a Excel de las 3 pantallas (se
confirmó `Content-Type` y tamaño de archivo no vacío vía `fetch` directo,
además del botón real en la UI); historial de precio (se editó el precio de
`MAS CARNE 12% ESENCIAL 25 kg` de $198.88 a **$215.00 como parte de la
prueba — quedó así, es un cambio real en la BD, no se revirtió**, siguiendo
el mismo criterio de rondas anteriores de dejar los datos de prueba
documentados en vez de revertidos).

## 5d. Fase 12b (esta ronda) — sku automático desde código de proveedor

El dueño pidió seguir mejorando sin indicar qué específicamente ("no sé qué
puedes seguir haciendo, haz algo, mejora algo o propón algo, ya después lo
valido"). Se cerró el único pendiente ya documentado y acotado que quedaba
de Fase 11 (evitó proponer algo nuevo desde cero, y evitó tocar cosas
riesgosas como permisos o borrado de datos). Detalle técnico en
`CHANGELOG.md` ("Fase 12b") y `MEMORIA.md` (ADR-021).

- Al confirmar un lote, el `codigo_proveedor` de cada línea (capturado desde
  siempre — `NoIdentificacion` del CFDI, `Item` del PDF, `Código` del Excel
  — pero nunca usado después de la vista previa) ahora rellena `producto.sku`
  tanto al **crear** un producto nuevo como al **vincular** uno existente que
  no tuviera sku todavía. Nunca pisa un sku ya capturado; nunca truena por
  duplicado (se verifica disponibilidad antes, con `_sku_disponible`).
- Verificado con un script directo por API (no por UI, es un cambio de lógica
  pura de backend): crear con código libre, crear con código ya usado por
  otro producto (debe quedar sin sku, sin error), vincular a un producto sin
  sku. Los 3 escenarios dieron el resultado esperado.
- **Datos de prueba dejados en la BD real**: 3 productos sintéticos
  (`Producto Nuevo Prueba SKU 10 kg`, `Producto Duplicado Prueba SKU 5 kg`,
  `Producto Sin Sku Prueba`, ids consecutivos justo después de los últimos
  documentados en §4.2) — a diferencia de los datos de prueba de rondas
  anteriores, estos no tenían valor demostrativo real (no venían de archivos
  del dueño), así que se **suspendieron** (`activo=false`, soft-delete vía
  `DELETE /productos/{id}`) al terminar en vez de dejarlos activos. 3 lotes
  de importación de prueba quedaron `confirmado` en el historial de
  `/importacion` (no se pueden cancelar retroactivamente una vez
  confirmados, es el comportamiento normal de la app).

## 5e. Fase 12c (esta ronda) — reporte imprimible de Ventas + Android

El dueño pidió seguir con "lo más corto" de los pendientes, sin decir cuál.
Detalle técnico en `CHANGELOG.md` ("Fase 12c") y `MEMORIA.md` (ADR-022).

**Investigación de la app Android** (solo lectura, sin cambios de código —
ver razón abajo): se revisó `PuntoPeludo/app/src/main/java/com/example/puntopeludo/`
buscando equivalentes a dos features de la web:
- **Reimpresión de ticket**: NO existe. `VentaActivity.kt` → `cobrarVenta()`
  solo hace `Toast.makeText(..., "✅ Venta Exitosa")` y `finish()` — ni
  siquiera muestra un ticket de la venta recién hecha, mucho menos permite
  reimprimir una anterior.
- **Selector de sucursal activa**: NO existe. `ID_SUCURSAL_SESION` se guarda
  una vez en `SharedPreferences` al hacer login (`LoginActivity.kt`) y así
  se queda — `VentaActivity.kt`, `CajaActivity.kt`, `ReportesActivity.kt` lo
  leen tal cual, sin forma de cambiarlo sin cerrar sesión.
- **No se implementó nada de esto**: este entorno no tiene Android
  Studio/emulador/SDK para compilar o correr la app, así que editar Kotlin
  sin poder verificarlo habría sido irresponsable (mismo criterio que usa
  este proyecto para features web: no se reporta como "hecho" algo que no
  se pudo probar). Si el dueño confirma que esto le importa en la práctica
  (¿algún superadmin usa la app Android, o solo vendedores de una sola
  sucursal?), es trabajo aparte que necesita un entorno donde sí se pueda
  compilar/probar.

**Reporte imprimible/PDF de Ventas** (sí implementado y verificado):
- Nuevo botón "Imprimir / PDF" en Ventas. En vez de agregar una librería de
  PDF al backend, se generalizó el mecanismo que ya aislaba el ticket al
  imprimir (`@media print` + `#ticket`) a una clase reutilizable
  `.printable` (`src/index.css`) — cualquier pantalla puede usar el mismo
  patrón. El reporte incluye encabezado (sucursal, filtros activos, fecha de
  generación) y la tabla ya filtrada + total. `window.print()` deja que el
  usuario elija papel o "Guardar como PDF" desde el navegador.
- Verificado sin poder disparar un print real desde la automatización del
  navegador (los diálogos de impresión son del sistema operativo, no de la
  página) — en su lugar se confirmó: (1) el contenido del bloque
  `.printable` es correcto y completo (incluyendo que el texto de "filtros
  activos" cambia bien al aplicar un filtro), (2) `display: none` en
  pantalla normal (no estorba), (3) la regla `@media print` compilada en el
  CSS real del navegador es exactamente la esperada (incluyendo la clase de
  Tailwind `print:block`). El mecanismo es idéntico al del ticket, que ya se
  verificó visualmente con screenshot en una ronda anterior.
- Solo se hizo para Ventas (no Inventario/Auditoría) para mantener esto
  acotado — el patrón `.printable` ya está listo para reutilizarse ahí si
  se pide.

## 5f. Fase 13 (esta ronda) — Configuración del negocio + surtido por lista + reanálisis

Dos pedidos concretos del dueño: (1) "haz alguna configuración básica y
documenta" — le di 3 opciones (datos del negocio / variables de entorno /
despliegue), eligió **datos del negocio**. (2) "modifica la parte de agregar
inventario para que sea por lista y poder auditarlo, porque por lo regular se
surtiría por mucha cantidad... analiza todo de nuevo y propón cambios".
Detalle técnico en `CHANGELOG.md` ("Fase 13") y `MEMORIA.md` (ADR-023).

**Configuración del negocio**: nueva tabla `configuracion_negocio` (fila
única), nueva pantalla `/configuracion` (nombre, dirección, teléfono, RFC),
nuevo permiso `configuracion.gestionar` (solo superadmin por defecto). El
ticket (`TicketModal.tsx`) y el reporte imprimible de Ventas (Fase 12c) ya
no muestran "PUNTO PELUDO" fijo — usan lo que esté configurado. Verificado en
vivo: se guardó dirección "Calle Falsa 123, Col. Centro" y teléfono
"55 1234 5678" reales de prueba (quedaron guardados, son datos de prueba
fáciles de identificar y sobrescribir — no hay forma de "resetear" sin pisar
con datos reales, así que se dejaron ahí a propósito) y se confirmó que
aparecen en el ticket reimpreso.

**Surtir mercancía por lista, auditable**: el modal "Surtir mercancía" ya no
captura un producto a la vez — ahora es una lista (agregar/quitar líneas,
cada una con su producto y cantidad), más proveedor/nota opcionales. Nuevo
`POST /ingreso-inventario/lote` (transacción atómica: si una línea falla,
ninguna se aplica) + nuevo botón **"Historial de ingresos"** que abre un
listado de lotes pasados con drill-down al detalle de cada uno (qué
productos, cuánto de cada uno, quién y cuándo). El endpoint viejo de un solo
producto (`POST /ingreso-inventario/`, usado por la app Android) **se dejó
intacto** — se verificó explícitamente que sigue funcionando después del
refactor que compartió lógica entre ambos.
Verificado en vivo: se registró un lote con 2 líneas (`Croquetas Prueba
20kg` +2, `BORREGO ESENCIAL 25 kg` +1 — ambos productos de prueba, no del
dueño), se confirmó que el inventario subió correctamente, y que el
historial muestra el lote con drill-down correcto al detalle. **Nota
importante de limpieza**: antes de esta verificación final se probó también
`POST /ingreso-inventario/lote` por API directa contra dos productos
**reales del dueño** (`MAS CARNE 12% ESENCIAL 25 kg` id 6, `Agromas cerdo
engorda` id 2) — ese movimiento se **revirtió** de inmediato usando
`PUT /inventario/{id}` (endpoint normal de la app, no un bypass) leyendo el
valor exacto de antes desde `GET /auditoria/historial`, así que el stock de
esos 2 productos quedó igual que antes de la prueba. Sí quedaron 2 lotes de
prueba en el historial de `/ingreso-inventario/lotes` (uno con esos 2
productos reales por $9 y $12 respectivamente vía curl, proveedor "Proveedor
de prueba"; otro con los 2 productos de prueba vía la UI, proveedor
"Proveedor Prueba Fase13") — no se pueden borrar (no hay endpoint de borrado,
es un registro de auditoría a propósito), bórralos manualmente en la BD si
molestan, o ignóralos, no afectan el stock real.

**Reanálisis general — 4 hallazgos, ninguno implementado a propósito**:
1. ⚠️ **Seguridad — no existe `.env` real**: ver la advertencia completa en
   §2, arriba de todo este archivo.
2. El puerto de Postgres en `docker-compose.yml` (`"5433:5432"`) se expone a
   toda la red local, no solo a `localhost` — con la contraseña débil "1234"
   del contenedor. Cambiar a `"127.0.0.1:5433:5432"` si te preocupa (oficina
   con wifi compartido, por ejemplo).
3. **Hay 3 reportes completos y funcionales en `app/routers/informes.py`
   sin ninguna pantalla en la web**: `reporte-ventas`, `reporte-surtidos`,
   `reporte-cortes` — todos por rango de fecha y sucursal, con nombres de
   cliente/vendedor ya resueltos vía join, gateados a Gerente/SuperAdmin.
   El permiso `reportes.ver` existe en el catálogo (aparece en Roles y
   permisos) pero no protege nada — ningún endpoint lo exige, es huérfano.
   Es probablemente la mejora de mayor valor pendiente: el backend ya está
   listo, solo falta una pantalla "Reportes" con 3 pestañas + selector de
   fecha/sucursal.
4. `reporte-surtidos` (dentro de `informes.py`) agrupa ingresos por "mismo
   minuto + mismo usuario" como aproximación de qué llegó junto en una
   entrega — ahora que existe `ingreso_inventario_lote` (esta misma ronda),
   ese reporte podría usar el lote real en vez de adivinar por reloj.

## 5g. Fase 14 (esta ronda) — POS con filtros/granel + módulo Listas

Feedback denso del dueño tras usar el Punto de Venta él mismo. Detalle
técnico en `CHANGELOG.md` ("Fase 14") y `MEMORIA.md` (ADR-024, ADR-025).

**POS — filtros, granel visible, tarjetas más grandes**:
- Nuevos filtros: **marca** (siempre visible) + **especie/animal** y
  **categoría** (solo aparecen si la marca elegida tiene productos con ese
  dato — mismo endpoint `GET /productos/filtros` que ya usaba Productos, no
  se construyó nada nuevo en el backend). Categoría cubre lo que el dueño
  describió como "tipo en algunos casos, como maíz, collares" — productos
  que no están ligados a un animal específico.
- La lista de productos ahora se pide al servidor con los filtros aplicados
  (`GET /productos/?marca_id=&especie_id=&categoria_id=`), así que la
  búsqueda de texto queda automáticamente acotada al filtro activo — es
  consecuencia de mover el filtrado al servidor, no lógica extra.
- **Venta a granel visible desde la tarjeta**: antes, tocar la tarjeta
  siempre agregaba "pieza" (`addProducto(p, false)` fijo) y solo se podía
  cambiar a granel con un botón chico DESPUÉS de que ya estaba en el
  carrito — nada indicaba en la tarjeta que el producto admitía granel.
  Ahora, si `se_vende_a_granel` y tiene `precio_granel`, la tarjeta muestra
  dos botones lado a lado ("Pieza $X" / "Granel $Y/unidad"); si no, un solo
  botón con el precio normal.
- Tarjetas más grandes (más padding, texto más grande, grid de 2/3 columnas
  en vez de 2/3/4).
- Verificado en vivo: filtro de marca probado con Agromas (26 productos) y
  Api-Aba (0, correctamente "Sin resultados"); búsqueda de "pollo" con el
  filtro Agromas activo devolvió solo productos Agromas con "pollo" en el
  nombre; tarjeta de "Agromas cerdo engorda" mostró correctamente los
  botones Pieza/Granel.

**Catálogo real: se encontraron y corrigieron 2 lotes reales mal
etiquetados** — ver el detalle completo en §4.2 (sección de datos de
prueba/reales), porque afecta directamente qué hay en la BD real. Resumen:
Agromas ya tenía 26 productos reales confirmados (el dueño lo hizo por su
cuenta, no yo); Api-Aba seguía en 0, pero su lista real (PDF, 219 líneas) ya
estaba parseada y solo tenía la marca mal puesta (un valor de prueba de
rondas anteriores) — se corrigió sin confirmar nada. Un segundo lote
(Excel de pedidos, 94 líneas, también Agromas) tampoco tenía marca — también
se corrigió. **Ninguno de los dos lotes se confirmó** — siguen en
`revision`, es decisión del dueño.

**Módulo Listas** (`/listas`, permiso `productos.ver`): precios actuales del
catálogo agrupados por marca (orden alfabético), con "Exportar Excel"
(nuevo `GET /productos/exportar/excel`, reutiliza `generar_excel` de Fase
12) e "Imprimir / PDF" (reutiliza el patrón `.printable` de Fase 12c/13). Se
agrupa **solo por marca** — no por categoría/sub-línea como los Excel
originales del dueño — porque `categoria_id`/`subcategoria_id` siguen vacíos
en todos los productos reales; agrupar por algo que no tiene datos habría
producido una pantalla inútil. Si el dueño empieza a categorizar productos,
la pantalla ya está lista para ese sub-agrupamiento después. Verificado en
vivo: los 3 grupos de marca reales (Agromas 26, PetFood MX 4, z 1) se
mostraron correctamente, exportar a Excel funcionó desde el botón real de la
UI, y el bloque imprimible tiene el contenido correcto (oculto en pantalla).

**Nota operativa de esta sesión**: el puerto 8000 quedó en el estado
"fantasma" descrito en §3 durante esta ronda (varios reinicios seguidos del
backend mientras se depuraba por qué no aparecía una ruta nueva). Se usó el
puerto **8300** para el resto de la verificación. Revisa
`punto-peludo-web/.env` al empezar la próxima sesión — debería decir
`http://127.0.0.1:8000`; si no, es porque el puerto 8000 seguía sin
liberarse al cerrar esta sesión.

## 5h. Fase 16 (esta ronda) — Módulo Listas gráfico

El dueño pidió "cambiar el módulo de listas de forma gráfica" reproduciendo
`Lista Agromas.xlsx`/`Lista Api-Aba.xlsx` con precios automáticos del
catálogo. Se le pasó primero por las 7+1 decisiones de `PLAN_FASE16.md §6`
(ver el banner de arriba para el resumen de cada una) y, tras confirmarlas,
pidió explícitamente empezar a programar. Detalle técnico completo en
`CHANGELOG.md` ("Fase 16") y `MEMORIA.md` (ADR-026, ADR-027).

**Cómo funciona**: `app/services/lista_plantilla_service.py` parsea
`Lista Agromas.xlsx`/`Lista Api-Aba.xlsx` (copiadas a `app/assets/plantillas/`,
gitignored) a una lista ordenada de nodos por panel (izq/der) — clasifica
cada fila como encabezado (negrita + relleno de color de marca; nivel 1/2/3
según qué tan oscuro es el tinte) o producto (sin relleno), caminando cada
panel de arriba a abajo; ignora el título que cruza los dos paneles. Los
nodos se guardan en la nueva tabla `lista_plantilla_fila` (migración
`c9d0e1f2a3b4`) — un modelo de "esquema" plano (marca/hoja/panel/orden/tipo/
nivel/texto/producto_id), no un árbol de tablas fijo, para que la estructura
se pueda editar (agregar/mover/quitar filas) sin migraciones nuevas.

**El vínculo fila↔producto es automático pero deliberadamente conservador**
(`resolver_vinculos`): matchea por palabras normalizadas, exige que cualquier
palabra extra del producto se explique por el contexto de encabezados
ancestros (evita que "Desarrollo" bajo Cerdos se enganche con "POLLAS
DESARROLLO" solo por compartir la palabra), y si más de un producto sigue
calificando lo deja SIN vincular en vez de adivinar. Con esto, 15 de los 26
productos Agromas ya confirmados quedaron vinculados automáticamente; 4 más
se vincularon a mano vía el CRUD de edición (nombres con palabras como "CP"
o "PRE-INICIADOR" que no aparecen en ningún encabezado de la plantilla) —
**19/26 en total**. Los 6 restantes quedaron sin vincular a propósito: 4 son
duplicados exactos de otro producto ya vinculado (mismo nombre, sin `sku`,
dato de calidad preexistente — no se tocaron ni se borraron) y 1
(`INVENCIBLE 26 INICIO`) es el mismo caso ambiguo que Fase 15 ya había
dejado sin clasificar (la plantilla dice "267", el producto dice "26").

**Decisión de alcance que tomé sin preguntar de nuevo** (documentada para que
el dueño la revise): pidió "acoplar" los nombres del catálogo a la
plantilla — se interpretó como **vincular sin renombrar** `producto.nombre`
(ese nombre también lo usan POS, tickets e inventario; convertirlo al nombre
corto de la plantilla, ej. "CERDO SUPREMA CRECIMIENTO 25KG" → "Crecimiento",
sería una regresión de usabilidad ahí). Si el dueño de verdad quiere
renombrar los 26 productos al nombre corto, es un cambio acotado y
reversible, pendiente de que lo confirme.

**Api-Aba** (0 productos confirmados en el catálogo) muestra las 3 hojas
(`Hoja1`, `Hoja2`, `Vimifos`) completamente vacías de precio — es lo
esperado, no un bug. De paso se descubrió que alguien (el dueño, fuera de
esta sesión) subió la propia `Lista Api-Aba.xlsx` como importación de
catálogo el mismo día (lote `revision` id 29, sin precios porque la
plantilla los trae vacíos) — no se tocó, sigue en revisión.

**Backend nuevo**: router `app/routers/listas.py` (`GET
/listas/plantillas-disponibles`, `GET /listas/plantilla?marca_id=`, `POST
/listas/plantilla/importar?marca_id=` para regenerar desde el archivo
original, CRUD `POST/PUT/DELETE /listas/plantilla-filas[...]` +
`/reordenar`, `GET /listas/plantilla/exportar/excel?marca_id=`). El export
Excel **no copia el `.xlsx` original** como proponía el plan — se reconstruye
con openpyxl desde los datos vigentes de `lista_plantilla_fila`, porque una
vez que la estructura es editable desde la web el archivo fuente ya no
refleja necesariamente lo que hay que exportar (ver ADR-027).

**Frontend**: `ListasPage.tsx` muestra la vista gráfica de dos paneles con
el color de marca cuando la marca tiene plantilla (Agromas naranja
`#ED7D31`, Api-Aba verde `#70AD47`, pestañas si hay varias hojas); cae a la
tabla plana anterior para marcas sin plantilla (Enfoque B de respaldo). Modo
"Editar estructura" (permiso `productos.gestionar`): mover, editar
texto/nivel/producto vinculado, eliminar, agregar filas nuevas. Botón
"Reimportar" (permiso `catalogo.importar`) para regenerar desde el archivo
original — con confirmación porque reemplaza cualquier edición manual.

**Verificado**: 11 pruebas unitarias nuevas (`tests/test_fase16_unit.py`,
sin BD) contra un `.xlsx` sintético armado en el propio test — suite
completa **48 pytest en verde**. En el navegador contra la BD real: vista
gráfica de Agromas (19 precios visibles) y Api-Aba (3 pestañas, vacío como
se espera); edición inline vinculando "Agrimix Migaja CC" a su producto real
(quedó vinculado, cambio real en BD, no se revirtió — es un vínculo
correcto); agregar una fila de prueba y eliminarla (confirmado por API
directa, ver nota abajo); botones condicionados al permiso correcto. Sin
errores de consola. `tests/smoke_e2e.py` no se re-corrió limpio esta ronda
por datos `SmokeMarca` que ya quedaron atascados de una sesión anterior
(colisión de nombre único al crear la marca de prueba, no relacionado con
Fase 16 — no se tocó porque esos datos de prueba tienen una venta real
asociada, no es seguro borrarlos sin permiso).

⚠️ **Quirk de esta sesión, no del proyecto**: el botón "Eliminar fila" del
modo edición usa `window.confirm()` (mismo patrón que ya usan
`ProductosPage`/`VentasPage`/`ImportacionPage`/`DescuentosPage` — no es una
elección nueva de Fase 16). El diálogo nativo **cuelga la automatización del
navegador de este entorno** (no a un usuario real haciendo clic): un
`click()` disparado por JavaScript sobre el botón deja la pestaña sin
responder porque el `confirm()` bloqueante nunca se resuelve solo. Si te pasa
lo mismo verificando en este sandbox, no esperes a que se destrabe — cierra
la pestaña (`tabs_close`) y abre una nueva; para probar el DELETE en sí, usa
la API directamente (`requests.delete(...)`) en vez de clickear el botón.

## 6. Decisiones de negocio que YA están resueltas (no las vuelvas a preguntar)

Confirmadas explícitamente por el dueño — el detalle técnico de cada una está
en `MEMORIA.md` (buscar el ADR correspondiente), esto es solo el resumen:

- Los descuentos **nunca se acumulan**: gana la regla más específica
  (producto > cliente+marca > marca > cliente > general). No se puede tener
  a la vez un descuento de marca y uno de producto de esa marca para el mismo
  cliente/sucursal — el backend lo rechaza (409).
- Los **clientes son propios de una sucursal**, no globales. Si el mismo
  comprador va a otra sucursal, se registra ahí como cliente nuevo.
- Las reglas de descuento **pueden variar por sucursal** (vía la sucursal del
  cliente, o explícitamente en reglas de marca).
- **Venta a domicilio** = cero descuentos automáticos, siempre, sin excepción.
- El descuento manual del checkout es **porcentaje** del total, no monto fijo.
- Tolerancia de fábrica en auditoría es **asimétrica y por marca/empresa**
  (puede faltar X, puede sobrar Y — no son iguales).
- El pulido visual/branding se pospuso a propósito — no es que se haya
  olvidado.
- Importación de catálogo: emparejamiento contra productos existentes
  **siempre por nombre** (nunca por código); **nada se crea automático** — el
  dueño aprueba cada línea en la vista previa; el margen de venta se define
  **por marca** con excepción opcional por producto; el costo de compra se
  guarda pero **solo lo ven roles con permiso** (no vendedores).

## 7. Mapa de documentación (quién dice qué)

| Archivo | Para qué sirve |
|---|---|
| **`EMPEZAR_AQUI.md`** (este) | Punto de entrada único. Léelo primero siempre. |
| `PLAN_FASE16.md` | Plan del módulo Listas gráfico (Agromas/Api-Aba) — **implementado y verificado**, ver §5h de este archivo y `CHANGELOG.md` ("Fase 16"). §6 tiene las 8 decisiones que confirmó el dueño (2026-07-17). |
| `MEMORIA.md` | Decisiones arquitectónicas (ADR numerados), convenciones, modelo de roles. El "por qué" de cada cosa no obvia. |
| `ROADMAP.md` | Backlog por fases, qué está ✅ y qué ⬜. El detalle de la Fase 11 también vive aquí. |
| `CHANGELOG.md` | Qué archivo se tocó y por qué, en cada iteración, en orden cronológico inverso (lo más reciente arriba). |
| `COMO_EJECUTAR.md` | Cómo levantar todo, paso a paso, con solución de problemas comunes. |
| `punto-peludo-web/README.md` | Lo mismo que arriba pero específico del frontend (estructura, cómo funcionan los permisos en el cliente). |

Si algo en este archivo contradice a los otros MD, **confía en `CHANGELOG.md`**
(es el más granular y cronológico) y avísale al usuario de la inconsistencia.
