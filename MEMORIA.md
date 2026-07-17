# MEMORIA DEL PROYECTO — PP_API (ERP + POS Multi-Sucursal)

> 👉 **¿Sesión nueva? Lee primero [`EMPEZAR_AQUI.md`](EMPEZAR_AQUI.md).**
> Documento vivo. Registra decisiones arquitectónicas, convenciones de código,
> dependencias y estado del sistema. **Leer esto antes de tocar cualquier lógica.**

Última actualización: **2026-07-13**

---

## 1. Visión

ERP híbrido + POS multi-sucursal para un negocio de venta de alimento para animales,
accesorios y farmacia veterinaria. Objetivo: que la gerencia opere, audite y decida
desde el celular sin estar físicamente en los locales.

**Clientes del backend (importante):**
- **App Android** → POS del cajero (Vendedor).
- **Página web** (en construcción) → Panel de administración (SuperAdmin / Gerente).
- El backend es una **API REST agnóstica al cliente**: ambos consumen los mismos
  endpoints JSON y el mismo login JWT. No se duplica lógica por cliente.

---

## 2. Stack Tecnológico

| Capa | Tecnología | Notas |
|------|-----------|-------|
| Framework | FastAPI 0.116 | `redirect_slashes=False` |
| Acceso a datos | `databases` 0.9 (async) + SQLAlchemy **Core** 2.0 | ⚠️ NO ORM: se usan objetos `Table`, no clases declarativas |
| Driver | asyncpg 0.30 | URL: `postgresql+asyncpg://...` |
| Base de datos | PostgreSQL 15 (Docker, puerto host **5433**) | ver `docker-compose.yml` |
| Migraciones | Alembic 1.17 | `target_metadata = metadata` de `models.py` |
| Auth | python-jose (JWT) + passlib/bcrypt | |
| Validación | Pydantic 2.11 | |
| Config | `app/core/config.py` (stdlib, lee `.env` sin dependencias extra) | |
| Estructura | Paquete `app/` (core/models/schemas/routers/services) | arranque `uvicorn app.main:app` |
| Pruebas | pytest (unitarias) + `tests/smoke_e2e.py` (integración) | `requirements-dev.txt` |

### Cómo correr el proyecto
```bash
# 1. Levantar la base de datos
docker compose up -d

# 2. Activar entorno e instalar dependencias (si es entorno nuevo)
#    .\venv\Scripts\Activate.ps1   (Windows PowerShell)
pip install -r requirements.txt

# 3. Aplicar migraciones
alembic upgrade head

# 4. Crear el SuperAdmin inicial (bootstrap de acceso, requerido por el RBAC)
python crear_superadmin.py            # Admin / admin123 por defecto

# 5. Correr la API
uvicorn app.main:app --reload

# 6. (Opcional) Poblar datos de prueba — requiere la API corriendo
python llenar_datos.py

# 7. (Opcional) Smoke test end-to-end — requiere la API corriendo
python tests/smoke_e2e.py
```
La configuración sensible vive en `.env` (ver `.env.example`). Si no existe `.env`,
se usan valores por defecto de desarrollo.

### Estructura del proyecto
```
PP_API/
├─ app/                   # Paquete de la aplicación
│  ├─ main.py             # App FastAPI + CORS + registro de routers
│  ├─ core/               # Núcleo transversal
│  │  ├─ config.py        # Settings desde .env (stdlib, sin deps)
│  │  ├─ database.py      # Instancia `databases` + utilidades de fecha
│  │  ├─ security.py      # Hash de password + JWT
│  │  ├─ dependencies.py  # RBAC: get_current_user + require_roles
│  │  └─ constants.py     # Constantes de dominio (tipos de ajuste, movimientos)
│  ├─ models/             # Tablas SQLAlchemy Core, por dominio (+ __init__ re-export)
│  ├─ schemas/            # Modelos Pydantic, por dominio (+ __init__ re-export)
│  ├─ routers/            # Endpoints por dominio (incl. dashboard.py, auditoria.py)
│  └─ services/           # Lógica de negocio reutilizable (inventario, auditoría)
├─ crear_superadmin.py    # Bootstrap del 1er SuperAdmin (directo a BD)
├─ llenar_datos.py        # Seed vía API (se autentica)
├─ alembic/               # Migraciones (env.py usa la URL de .env)
└─ tests/                 # Unitarias (pytest) + smoke e2e
```
Imports internos: `from app.core.database import ...`, `from app.models import ...`,
`from app.services.inventario_service import ...`. Arranque: `uvicorn app.main:app`.

---

## 3. Decisiones Arquitectónicas (ADR resumido)

### ADR-001 — Multi-Tenant por columna `sucursal_id` (aislamiento lógico)
Todas las tablas transaccionales llevan `sucursal_id` (FK a `sucursal`). No hay
base de datos por sucursal; el aislamiento es lógico vía filtros. El SuperAdmin
puede ver todo o filtrar por una sucursal.
Tablas con `sucursal_id`: `usuario`, `inventario`, `ingreso_inventario`,
`ajuste_inventario`, `historial_inventario`, `corte_caja`, `venta`.

### ADR-002 — Inventario en unidad mínima transaccional
El stock en `inventario.cantidad` **siempre** está en la unidad más pequeña
(kilos, mililitros, piezas sueltas), usando `Numeric(12,3)`. Los "bultos/sacos"
se convierten a la unidad base multiplicando por `producto.contenido_neto`.

### ADR-003 — Venta híbrida (paquete cerrado vs. granel)
Un mismo producto se vende cerrado (`precio_base`) o fraccionado
(`precio_granel`). La venta descuenta del stock en unidad base. Toda venta y
operación de caja corre bajo **transacción atómica** (`async with database.transaction()`).

### ADR-004 — RBAC gradual (decidido 2026-07-08)
Se implementa control de acceso por roles en `dependencies.py`. Se aplica
**gradualmente**: primero a superficies de administración (usuarios, sucursales,
informes, escrituras de catálogo), dejando el POS operable para que la app
Android migre sin romperse. Roles canónicos: `vendedor`, `gerente`, `superadmin`.

### ADR-005 — Atributos dinámicos: modelo HÍBRIDO (decidido 2026-07-08)
Se conservan las FKs relacionales de alto valor para KPIs/joins
(`marca_id`, `categoria_id`, `subcategoria_id`, `especie_id`, `etapa_id`) y se
**agrega** una columna `producto.atributos_extra` tipo **JSONB** para los
atributos variables por tipo de producto (sabor, talla, dosis, presentación,
material...). El frontend construye filtros dinámicos según `tipo_producto`.
_(Pendiente de implementar — Fase 2.)_

### ADR-006 — Config por entorno, sin secretos en código (decidido 2026-07-08)
`SECRET_KEY`, `DATABASE_URL`, `CORS_ORIGINS`, etc. se leen de `.env` vía
`config.py`. `config.py` usa solo la librería estándar (parser `.env` propio)
para **no** agregar dependencias nuevas ni romper el arranque si falta un paquete.
`alembic/env.py` también toma la URL de `settings` (convertida a psycopg2), así
`.env` es la **fuente única** de la conexión para app y migraciones.

### ADR-007 — JSONB: serialización vía SQLAlchemy, NO códec asyncpg (2026-07-08)
`databases` ya aplica los procesadores de tipo de SQLAlchemy, por lo que
`producto.atributos_extra` (JSONB) se serializa dict→jsonb y se lee jsonb→dict
automáticamente. **NO** registrar además un códec `set_type_codec` de json en
asyncpg: causa **doble codificación** (el valor se guarda como string y
`jsonb_typeof` da "string", rompiendo los filtros `->>`). Filtros JSONB con
`producto.c.atributos_extra[clave].astext == valor`. Para SQL crudo con
`databases`, usar `text(sql).bindparams(...)` (no pasar `values=` con un
`TextClause`, truena con `.values()`).

### ADR-008 — Modularización por dominio (2026-07-08)
`models.py` → paquete `models/` (base, catalogo, organizacion, producto,
inventario, ventas) y `schemas.py` → paquete `schemas/`, ambos con re-export en
`__init__.py` para conservar `from models import X` / `from schemas import Y`.
### ADR-027 — Export de plantilla: regenerar con openpyxl, no copiar el .xlsx original (2026-07-17)
El plan de Fase 16 (§4.5) proponía copiar el `.xlsx` original y solo escribir
la columna de precio, por fidelidad máxima. Pero el dueño también pidió que
la estructura fuera **editable desde la web** (§6.6) — una vez que se puede
agregar/quitar/reordenar filas desde `/listas`, las filas del archivo
original ya no reflejan necesariamente la estructura vigente. Copiar
celda-por-celda un archivo cuyas filas ya no corresponden a los datos reales
habría producido un Excel con contenido viejo o desalineado. Se optó por
**reconstruir el libro con openpyxl** (`generar_excel_plantilla`,
`export_service.py`) a partir de `lista_plantilla_fila` en vivo — incluyendo
título, tinte de color por nivel de encabezado y paneles A-D/E-H — en vez de
copiar el archivo fuente. **Lección**: una decisión de diseño tomada antes de
ver todas las demás decisiones puede quedar invalidada por una decisión
posterior en el mismo documento — conviene revisar las dependencias entre
puntos de la lista de decisiones, no solo resolverlos de forma independiente.

### ADR-026 — Vínculo plantilla↔producto: contexto de encabezados, nunca adivinar (2026-07-17)
El dueño decidió alinear los nombres en el origen en vez de pedir un sistema
de matching difuso (ver PLAN_FASE16.md §4.2, §6.2) — pero eso no elimina la
necesidad de un primer vínculo automático al sembrar la estructura por
primera vez (`resolver_vinculos`, `lista_plantilla_service.py`) ni de poder
re-vincular con el botón "Reimportar". El resolver implementado matchea por
palabras normalizadas con dos reglas de seguridad no negociables: (1)
cualquier palabra que el producto traiga de más allá de las de la plantilla
debe explicarse por el contexto de encabezados (sección/línea) bajo el que
cae la fila — si no, se descarta como candidato — y (2) si más de un producto
sigue calificando, la fila se deja **sin vincular** en vez de adivinar. La
razón concreta: una primera versión sin la regla (1) enlazó el "Desarrollo"
de la línea Cerdos/Suprema con "POLLAS DESARROLLO 25 kg" solo porque
compartían esa palabra — un cruce de especie real que habría puesto un precio
equivocado en producción. Con las dos reglas, el resolver automático
enlazó 15/26 productos reales de Agromas de forma segura; los 4 restantes
resolubles (palabras como "CP" o "PRE-INICIADOR" que no aparecen en ningún
encabezado ancestro) se vincularon a mano vía el CRUD de edición — la razón
de ser de que la plantilla sea editable no es solo estética, es también la
red de seguridad para lo que el automatismo deja abierto a propósito. **Lección**:
en un catálogo con nombres cortos genéricos repetidos en varias líneas
("Crecimiento", "Engorda", "Inicio"), el riesgo real no es dejar un precio
vacío — es completarlo con el producto equivocado; el diseño debe
tratar ambos errores con pesos muy distintos.

### ADR-025 — Listas: agrupar por lo que el catálogo real tiene, no por lo ideal (2026-07-15)
El dueño pidió una pantalla de listas de precio "como" `Lista Agromas.xlsx`
(bloques por categoría/sub-línea dentro de cada marca). El catálogo real
tiene `categoria_id`/`subcategoria_id` como columnas desde el diseño
original (ADR-005), pero en la BD real están **vacías en todos los
productos** — nadie las ha llenado todavía. Construir el agrupamiento por
categoría de todos modos habría producido una pantalla con un solo grupo
"Sin categoría" gigante por marca, sin ningún valor real. Se optó por
agrupar **solo por marca** (el único dato consistentemente poblado hoy) y
dejar la estructura del código lista para agregar el sub-agrupamiento por
categoría después, sin rediseñar nada, en cuanto el catálogo tenga esos
datos. **Lección**: cuando el pedido implica reproducir una estructura de
datos que el sistema técnicamente soporta pero que en la práctica está
vacía, construir para los datos que SÍ existen — una función "completa" que
no puede mostrar nada útil es peor que una simple que sí lo hace.

### ADR-024 — Corregir metadatos de un lote sin confirmar es seguro; confirmarlo no (2026-07-15)
Al investigar el catálogo real se encontraron dos lotes de importación reales
del dueño (`Api-Aba`, 219 líneas; `Formato de pedidos`, 94 líneas) atascados
en `revision` con la marca mal asignada — una tenía una marca de prueba
("PetFood MX") puesta durante la depuración del parser de PDF en una ronda
anterior, la otra no tenía ninguna. Se corrigió el `marca_id` de todas las
líneas de ambos lotes por API directa (recalculando el margen automáticamente
al cambiar de marca — comportamiento ya existente de `actualizar_linea`,
ver Fase 11). **No se confirmó ninguno de los dos lotes.** La distinción
importa: editar metadatos de una línea `pendiente` (marca, margen) no toca
`producto` ni `inventario` — es completamente reversible y no afecta nada
que el dueño vea en su catálogo de venta. Confirmar (`crear`/`vincular`) sí
escribe en la BD real y es la decisión que, por regla establecida desde
Fase 11, le corresponde solo al dueño. **Lección**: "no tocar el catálogo
real sin que el dueño decida" no significa "no tocar nada" — la vista previa
de una importación es exactamente el lugar diseñado para prepararse antes de
esa decisión, y dejarla en mal estado (marca de prueba puesta) le habría
hecho más difícil al dueño revisarla cuando llegue el momento.

### ADR-023 — Ingreso por lista: helper compartido, no dos caminos divergentes (2026-07-15)
`POST /ingreso-inventario/` (un solo producto) ya lo usaba la app Android —
no se podía tocar su contrato. Para "surtir por lista" se agregó
`POST /ingreso-inventario/lote` (varias líneas), pero en vez de duplicar la
lógica de conversión de unidades + upsert de inventario + bitácora en los
dos endpoints, se extrajo a `_registrar_ingreso_linea(...)`, que NO abre su
propia transacción — quien la llama decide el alcance transaccional. El
endpoint viejo abre una transacción y llama al helper una vez; el nuevo abre
UNA transacción, crea el lote, y llama al helper una vez por línea — si
cualquier línea falla (ej. producto inexistente), ninguna se aplica.
**Lección**: cuando dos endpoints comparten lógica de negocio pero uno debe
componerse en un batch atómico, sacar la transacción del helper y dejarla en
manos del llamador es lo que permite reusar la misma función en ambos casos
sin romper la atomicidad del lote.

### ADR-022 — Reportes en PDF vía impresión del navegador, no una librería nueva (2026-07-14)
Para "exportar a PDF" (Ventas, y en el futuro Inventario/Auditoría), la
opción obvia era agregar una librería de generación de PDF en el backend
(ej. `reportlab`, `weasyprint`) — pero eso mete una dependencia nueva, con su
propio manejo de fuentes/layout, solo para producir algo que el navegador ya
sabe hacer. En vez de eso, se generalizó el mismo mecanismo de aislamiento
que ya usaba el ticket (`#ticket` + `@media print` + `visibility:hidden` en
el resto del `body`, ver ADR-018) a una clase reutilizable `.printable`.
Cualquier pantalla puede renderizar un bloque `<div className="printable
hidden print:block">` con su propio contenido de reporte (visible SOLO al
imprimir) y un botón que llama `window.print()` — el usuario elige imprimir
en papel o "Guardar como PDF" desde el diálogo nativo del navegador, sin que
el backend genere ni sirva ningún archivo. **Lección**: antes de agregar una
dependencia para "generar PDF", considerar si el requisito real es
"imprimible" — el navegador ya lo resuelve gratis, y evita mantener layout
de PDF en dos lugares (backend Y frontend) a la vez.

### ADR-021 — sku automático desde importación: solo rellena, nunca pisa (2026-07-14)
`producto.sku` es `unique, nullable`. Al confirmar un lote, si una línea trae
`codigo_proveedor` (`NoIdentificacion`/`Item`/`Código` según el origen) se
usa como `sku` — pero con dos guardas: (1) **nunca se sobreescribe** un sku
que el producto ya tenga (capturado a mano o de una importación previa —
gana el primero que llegó, no el más reciente), y (2) se verifica primero
que ningún OTRO producto ya tenga ese código (`_sku_disponible`), porque dos
proveedores distintos pueden coincidir en un código sin ser el mismo
producto — intentar insertarlo de todos modos violaría la restricción
`unique` y tronaría toda la transacción de `confirmar_lote` a medio camino.
**Lección**: cuando un campo `unique` se rellena desde datos externos poco
confiables (aquí, el código de un proveedor), la función que decide el valor
final debe consultar la unicidad explícitamente en vez de dejar que la BD la
valide al insertar — un `IntegrityError` a mitad de una transacción con
muchas líneas es peor (rollback de todo el lote) que simplemente no asignar
ese campo opcional.

### ADR-019 — Filtros derivados del listado ya cargado, no de un endpoint restringido (2026-07-13)
Al agregar el filtro "Vendedor" en Ventas, la opción obvia era poblar el
`<select>` desde `GET /usuarios/` — pero ese router está restringido a
`superadmin` (ADR de gestión de usuarios), así que un Gerente o Vendedor
viendo sus propias ventas no podría usar el filtro. Se resolvió agregando
`usuario_nombre` (join) a la respuesta de `GET /ventas/` y derivando las
opciones del `<select>` del lado del cliente, a partir de los
`{usuario_id, usuario_nombre}` únicos ya presentes en el listado cargado
(mismo patrón para "Cliente", reutilizando la query de `clientes` que la
pantalla ya tenía). **Lección**: cuando una pantalla necesita opciones de
filtro que técnicamente vienen de un recurso restringido, antes de exponer
ese recurso (o duplicar su lógica en un endpoint nuevo), revisar si los datos
ya visibles en la pantalla alcanzan para derivar las opciones — evita abrir
una superficie de permisos nueva por una mejora de UX menor.

### ADR-020 — Bitácora de precio: una fila por cambio real, no por cada PATCH (2026-07-13)
`producto_historial_precio` (Fase 12) solo escribe una fila cuando `costo` o
`precio_base` **realmente cambian de valor** — no cuando el campo viene en el
payload pero es igual al actual (`registrar_cambio_precio` compara antes de
insertar). Esto importa porque `confirmar_lote` (Fase 11) puede vincular
muchas líneas por corrida, y sin este filtro la bitácora se llenaría de
entradas "el precio cambió de $X a $X" cada vez que una importación trae el
mismo costo que ya estaba. La misma función se usa desde dos orígenes
distintos (`PUT /productos/{id}` con `origen='manual'` y `confirmar_lote` con
`origen='importacion'` + `lote_id`) — un solo punto de escritura evita que la
lógica de "¿esto cuenta como cambio?" diverja entre los dos caminos.

### ADR-018 — Reimpresión de ticket: componente compartido, no reconstruido (2026-07-13)
El dueño pidió verificar que se pudiera reimprimir el ticket de una venta ya
hecha desde **Ventas** — no existía: `TicketModal` era una función local
dentro de `PosPage.tsx`, acoplada al estado del flujo de cobro, y solo se
mostraba en el instante posterior a cobrar. En vez de reconstruir el ticket
en `VentasPage.tsx` con su propio marcado (duplicando estilos de impresión y
arriesgando que diverjan con el tiempo), se extrajo a
`src/components/TicketModal.tsx` con una interfaz de datos explícita
(`TicketData`) que no sabe nada de POS ni de Ventas — ambas pantallas arman
ese objeto desde su propia fuente (el resultado del cobro en un caso,
`GET /ventas/{id}` en el otro) y le pasan el mismo componente. **Lección**:
cuando un componente de UI con lógica de presentación no trivial (aquí,
`@media print` + layout de ticket) empieza a necesitarse desde un segundo
flujo, extraerlo con una interfaz de datos propia vale más que dejarlo vivir
dentro de la pantalla que lo originó.

Para que `GET /ventas/{id}` sirviera para esto sin exigir permisos que un
vendedor normal no tiene (`usuarios.gestionar`, `sucursales.gestionar` — los
necesarios para resolver nombre de vendedor/sucursal por separado), el
endpoint ahora hace `JOIN` con `usuario` y `sucursal` y devuelve
`usuario_nombre`/`sucursal_nombre` directamente en la respuesta.

### ADR-017 — pdfplumber parte una página en varias tablas: mapeo de columnas como estado (2026-07-13)
`page.extract_tables()` de `pdfplumber` no siempre devuelve **una** tabla por
página — cuando hay secciones/categorías dentro de la misma tabla visual
(ej. "POLLORINA", "CAPORINA", "YOUPIG!..." en la lista de precios de
API-ABA), pdfplumber la parte en **varios fragmentos**, y solo el primero
trae el encabezado repetido; el resto son continuaciones de puros datos sin
encabezado propio. Tratar las primeras N filas de cada fragmento como
encabezado (lo que hacía el código original) pierde datos de dos formas a la
vez: descarta filas de producto real creyendo que son encabezado, Y descarta
el fragmento completo cuando esas 2 primeras filas (datos reales) no
contienen ninguna palabra clave de columna reconocible. En este archivo
concreto costó casi la mitad del catálogo (123 de 220 líneas reales).
**Fix**: mantener el mapeo de columnas detectado como variable que persiste
ENTRE fragmentos — solo se reemplaza si un fragmento nuevo trae su propio
encabezado válido; si no, se asume continuación y se procesan todas sus
filas como datos. **Lección**: al parsear tablas de PDF con `pdfplumber`
(o cualquier librería similar), nunca asumir "una tabla = una unidad con su
propio encabezado" — verificar contra el archivo real cuántos fragmentos
devuelve por página antes de decidir la lógica de encabezado.

### ADR-016 — Selector de sucursal para superadmin + fix de scroll global (2026-07-13)
**Scroll roto en toda la app, no solo 3 pantallas**: `Layout.tsx` tenía
`<main className="flex-1 overflow-y-auto">` sin `min-h-0` en la cadena
flex/grid — el contenedor crecía para caber el contenido en vez de quedarse
al tamaño de pantalla y scrollear internamente; el `overflow-hidden` del
contenedor raíz recortaba el excedente sin mostrar scrollbar. Se notaba en
las pantallas con más contenido (Auditoría, Roles, Importación) pero era un
bug de layout global. **Lección**: si un `overflow-y-auto` "no hace nada" en
un layout flex/grid anidado, sospechar primero de `min-height` faltante antes
de buscar el bug pantalla por pantalla.

**Sucursal activa vs sucursal del usuario**: se separó el concepto de "a qué
sucursal pertenece este usuario" (`user.sucursal_id`, fijo desde el login) de
"qué sucursal estoy viendo/operando ahora" (`sucursalActivaId` en
`AuthContext`, con `useSucursalActiva()`/`useSucursalActivaInfo()`). Solo
superadmin puede cambiarla (selector en el header); para los demás roles
ambas coinciden siempre — no pueden operar fuera de su sucursal asignada.
Aplica a las 6 pantallas que antes usaban `user!.sucursal_id` directo
(Auditoría, Caja, Clientes, Descuentos, Inventario, POS) — incluyendo POS,
así que un superadmin puede registrar una venta a nombre de otra sucursal si
cambia el selector (a propósito, no es un descuido).

### ADR-015 — Importación de catálogo: Excel + XML/CFDI (2026-07-13)
Cuatro decisiones tomadas con el dueño antes de programar (no eran obvias):

1. **Ambas fuentes en un mismo módulo** (`/importacion`), Excel primero y XML
   después, compartiendo la misma infraestructura de revisión.
2. **Emparejamiento por nombre** (fuzzy, `difflib`) contra el catálogo
   existente — nunca por código, porque de las facturas "lo único que importa
   es el nombre" (palabras del dueño). El match es siempre una **sugerencia**,
   nunca se aplica solo.
3. **Nada se crea automático**: toda fila queda en `decision='pendiente'`
   hasta que el dueño decida `crear`/`vincular`/`ignorar` en la vista previa.
   `confirmar_lote` es la única función que escribe en el catálogo real.
4. **Margen de venta por marca** (`marca.margen_default`, %), con excepción
   opcional por producto (`producto.margen_override` — gana sobre el de la
   marca). El costo de compra se guarda en `producto.costo` pero **solo lo ven
   roles con el permiso `productos.ver_costo`** — no vendedores.

Hallazgo importante de los archivos reales (invalida un supuesto de
[[protocolo-docs-vivos]]/ADR-014): **no todos los Excel del dueño son "solo
nombres sin precio"** — `Winners.xlsx` trae hojas `Nombre|Kg|Precio` con
precios de venta reales. El parser detecta el modo por hoja (busca una celda
"Nombre" en las primeras filas) en vez de asumir un formato único.

Para el modo "bloques de categoría" (Api-Aba/Agromas/Vimifos, sin encabezados
de tabla), la señal para distinguir categoría/sub-línea de un producto real
**es el estilo de la celda, no el texto ni la posición**: título de hoja
~26pt, categoría bold ≥14pt, sub-línea (ej. "Línea Suprema") bold <14pt con
relleno, producto real no-bold sin relleno. Verificado contra los 3 archivos
reales antes de darlo por bueno.

El emisor de un CFDI es el *distribuidor*, no la marca del catálogo (una
factura de "Productos Agroindustriales Azteca" resultó ser 100% productos
Agromas) — la marca de las líneas de un XML se asigna a mano, nunca se infiere
del emisor.

Un producto creado desde una línea **sin precio real** (Excel de solo-nombre)
se crea `activo=false` (cae en Suspendidos) — nunca vendible a $0 por
accidente; el dueño lo precia y reactiva a mano, reusando el flujo que ya
existía desde ADR-014.

Dos bugs reales encontrados y corregidos durante la verificación end-to-end
(no en el diseño, en la implementación — dejar constancia para no repetirlos):
- El dedup de líneas dentro de un mismo archivo usaba la misma normalización
  que el fuzzy-match (que quita el sufijo de peso para comparar), así que
  colapsaba presentaciones distintas del mismo producto ("Hound Adulto 10 kg"
  vs "4 kg") en una sola línea. Se separaron las dos normalizaciones:
  `_clave_dedup` (conserva el peso) vs `_normalizar` (lo quita, solo para
  comparar similitud).
- `confirmar_lote` insertaba el producto nuevo sin pasar `stock_minimo`
  explícito; el `default=5.0` de SQLAlchemy Core (client-side, no
  `server_default`) no se aplicaba por ese camino de inserción `insert().values()`
  vía `databases`, y la columna quedaba `NULL` — rompía la respuesta del
  `GET /productos/{id}` contra el schema. Moraleja: con `databases`/inserts
  crudos, pasar siempre explícito lo que en otros endpoints llega implícito
  vía el `.model_dump()` de un schema Pydantic con default.

### ADR-014 — Descuentos robustos, venta a domicilio, clientes por sucursal (2026-07-13)
Tres decisiones tomadas con el dueño (no eran obvias, se preguntaron explícitamente):

1. **Los descuentos NUNCA se acumulan**: gana la regla más específica
   (producto > marca+cliente > marca > cliente > general), calculado con un
   **puntaje explícito en Python** (`_especificidad_regla` en `routers/ventas.py`;
   producto=100, marca=10, cliente=1) — NO depender de `ORDER BY` con NULLs de
   SQL (es frágil y antes tenía un bug real: una regla general con % más alto
   podía ganarle a una regla de cliente específico con % más bajo).
2. **No se permite mezclar** un descuento de marca (general) con descuentos de
   producto de esa misma marca, para el mismo cliente+sucursal — el backend
   rechaza con 409 (`app/services/descuentos_service.py::validar_sin_conflicto`).
   Hay que editar/desactivar la regla existente antes de crear la que choca.
3. **Los clientes son propios de una sucursal** (`cliente.sucursal_id`
   obligatorio), no globales — si el mismo comprador va a otra sucursal se
   registra ahí como cliente nuevo. `regla_descuento.sucursal_id` (nullable)
   se resuelve automáticamente a la sucursal del cliente cuando la regla tiene
   `cliente_id` (`resolver_sucursal_id`); para reglas solo de marca es opcional.

Además: **venta a domicilio** (`venta.tipo_entrega`) — si es a domicilio, el
motor de descuentos automáticos se salta por completo (0% siempre), sin
importar qué reglas existan. El descuento manual del checkout pasó de monto
fijo a **porcentaje** sobre el total (solo cambio de UI, el backend sigue
recibiendo un monto ya calculado).

`clientes`, `descuentos` y las escrituras de `marcas` **no tenían RBAC** (URLs
abiertas) — se cerraron con `require_perm`/`require_roles` en esta fase.

Nuevo: pantalla **Marcas** (CRUD, no existía), filtro jerárquico marca→especie
(`GET /productos/filtros`, solo devuelve especies que esa marca realmente
tiene) y vista de productos **Suspendidos** con **Reactivar** (el backend ya
soportaba `activo:true` vía el PUT existente; solo faltaba la UI).

Ver [[protocolo-docs-vivos]] — investigación sobre Excel/XML para Fase 11
(importación) documentada en ROADMAP.md, no implementada aún a propósito.

### ADR-013 — Auditoría (frontend), última pantalla del menú (2026-07-09)
`pages/AuditoriaPage.tsx` reemplaza el stub: lista de `GET /auditoria/plan-conteo`
filtrable (tipo/ubicación/atributos JSONB), captura de cantidad física por
producto, tipo de ajuste opcional (o automático), y registro contra
`POST /auditoria/ajuste`, mostrando el resultado (diferencia, tolerancia
bajo/alto, tipo aplicado) + historial de ajustes recientes. `StubPage.tsx`
eliminado (ya sin consumidores). Se encontró y corrigió un hueco real: el
formulario de Productos armaba el payload con `ubicacion_fisica` y
`tolerancia_unidad` pero no tenía esos campos en el modal — imposible
asignarlos desde la UI. Se agregaron. Verificado end-to-end en navegador
contra la BD real con una marca de tolerancia asimétrica real (bajo 0.3/alto
0.1): los 3 escenarios (dentro de tolerancia, faltante fuera, sobrante fuera)
dieron el tipo sugerido correcto en cada caso. **Con esto, las 12 pantallas
del menú son funcionales y verificadas.**

### ADR-012 — Descuentos y Sucursales (frontend) + reconciliación de BD (2026-07-09)
Se cerraron las dos últimas pantallas "en construcción" del frontend:
**Descuentos** (`pages/DescuentosPage.tsx`, reglas por catálogo/cliente/marca/
producto) y **Sucursales** (`pages/SucursalesPage.tsx`, crear/editar). Con esto,
**todas las pantallas del menú son funcionales excepto Auditoría** (pendiente
a propósito, es el siguiente paso).

Se verificó todo **contra la BD real `negocio`** (no una de prueba), lo que
reveló que esa base ya tenía el esquema completo aplicado manualmente en algún
momento, pero **sin tabla `alembic_version`** ni el **índice GIN** de
`producto.atributos_extra`. Se reconcilió sin tocar datos: se creó el índice
faltante y se corrió `alembic stamp head`. Lección: **antes de correr
`alembic upgrade head` contra una BD desconocida, verificar primero si ya tiene
tablas** (`\dt`) — si las tiene pero falta `alembic_version`, usar
`alembic stamp head` en vez de `upgrade head` (que fallaría intentando crear
tablas ya existentes).

Nota de infraestructura: el proyecto se movió de
`Documents/Negocio/Punt o de venta/` a `Documents/Negocio/PDV/` (mismo
contenido, todas las rutas relativas siguen funcionando).

### ADR-011 — Tolerancia de fábrica asimétrica y por marca (2026-07-09)
La variación de fábrica depende de la **empresa (marca)** y no es simétrica:
`marca.tolerancia_bajo` (cuánto puede FALTAR por empaque) y `marca.tolerancia_alto`
(cuánto puede SOBRAR). `producto.tolerancia_unidad` es un **override** simétrico por
producto (si >0 gana). `analizar_tolerancia(contenido_neto, cantidad_sistema,
diferencia, tol_bajo, tol_alto)` escala por nº de empaques y decide dentro/fuera;
`/auditoria/ajuste` hereda de la marca y devuelve `tolerancia_bajo`/`tolerancia_alto`.
Ej.: marca que solo llega corta → un faltante es VARIACION_FABRICA, un sobrante es
ERROR_SISTEMA.

### ADR-010 — RBAC por permisos asignables a roles (2026-07-08)
Se pasó de gatear solo por rol a un sistema de **permisos** (tabla `permiso` +
`rol_permiso`). El rol sigue siendo un string en `usuario.rol`; sus permisos se
guardan en BD y son editables desde la web (`/roles/{rol}/permisos`). `superadmin`
tiene todos de forma implícita. `GET /auth/me` devuelve los permisos del usuario;
el frontend arma menú y rutas a partir de ellos. Dependencia `require_perm(...)`
disponible (los endpoints POS siguen abiertos por compat. con Android; migrar
cada uno es follow-up). Catálogo en `constants.PERMISOS`, se sincroniza al arrancar.

**Frontend web:** proyecto `../punto-peludo-web` (Vite+React+TS+Tailwind) consume
esta API. Primera entrega: Login, POS, Caja, Panel, Roles y permisos.

### ADR-009 — Paquete `app/` + capa de servicios (2026-07-08)
Todo el código de la app vive bajo `app/` (`core/`, `models/`, `schemas/`,
`routers/`, `services/`). Los routers se apoyan en `app/services/` para lógica
reutilizable: `inventario_service.registrar_movimiento` (bitácora, dentro de la
transacción del router) y `auditoria_service.analizar_tolerancia` (función pura,
testeable). Arranque: `uvicorn app.main:app`. Reglas de negocio configurables en
`settings`: `SUCURSAL_DEFAULT`, `PERMITIR_STOCK_NEGATIVO`.

---

## 4. Convenciones de Código

- **Idioma**: nombres de tablas/campos/endpoints en **español** (`producto`,
  `sucursal_id`, `/ventas`). Mantenerlo.
- **Dinero**: `Numeric(10,2)`. **Cantidades/peso**: `Numeric(12,3)`.
- **Fechas**: se guardan en UTC (`datetime.now(timezone.utc)`), se devuelven al
  cliente en hora local CDMX vía `fecha_local_iso()` / `fecha_local_iso_simple()`
  (en `database.py`).
- **Soft-delete** en `producto` (`activo=False`), no borrado físico.
- **Roles canónicos** (en minúsculas): `vendedor`, `gerente`, `superadmin`.
  Definidos como constantes en `dependencies.py`.
- Routers en `routers/`, cada uno con su `APIRouter(prefix=..., tags=...)`.

---

## 5. Modelo de Roles (RBAC)

| Rol | Alcance |
|-----|---------|
| **vendedor** | Solo POS de su sucursal: ver inventario de su sucursal, abrir/cerrar su caja, registrar ventas. NO modifica catálogo ni ve reportes globales. |
| **gerente** | Su sucursal: ajustes de inventario, mermas, reportes de su sucursal, supervisar cortes de sus vendedores. |
| **superadmin** | Irrestricto: crear sucursales, catálogo global, reglas de descuento, KPIs de todo el negocio. **Siempre pasa cualquier check de rol.** |

`require_roles(...)` incluye a `superadmin` implícitamente en el set permitido.

---

## 6. Deuda Técnica / Bugs Conocidos (rastreados en ROADMAP)

Resueltos (2026-07-08):
- ✅ `venta_detalle` guarda `es_granel` + `cantidad_base`; cancelación exacta.
- ✅ `ajuste_inventario` tipifica con `tipo_ajuste`.
- ✅ `database.py` importaba `timezone` faltante (corregido).
- ✅ `si.py` (scratch) eliminado; reemplazado por `tests/smoke_e2e.py`.
- ✅ `SUCURSAL_DEFAULT` ya no está hardcodeado: viene de `settings` (o del payload).
- ✅ `usuarios` PUT usa `UsuarioUpdate` (no re-hashea si no cambia contraseña);
  hay endpoint `POST /usuarios/{id}/cambiar-password` y validación de rol.
- ✅ Se escribe `historial_inventario` en ventas, cancelaciones e ingresos
  (vía `app/services/inventario_service.registrar_movimiento`).
- ✅ Bloqueo de sobreventa configurable (`PERMITIR_STOCK_NEGATIVO`).
- ℹ️ `venv/` NO estaba versionado (0 archivos en git); ya está bien ignorado.

Pendientes menores:
- Migrar más lógica de negocio de los routers a `app/services/` (parcial).
- `tipo_producto` como FK real en vez de texto libre (opcional).

---

## 7. Estado por Fases (resumen — detalle en ROADMAP.md)

- **Fase 1 — Fundación y Seguridad** → ✅ completada
- **Fase 2 — Auditoría tipificada + Atributos JSONB** → ✅ completada
- **Fase 3 — Dashboard SuperAdmin (KPIs)** → ✅ completada
- **Fase 4 — Transaccionalidad + fix bugs** → ✅ completada
- **Fase 5 — Reestructura profesional (paquete `app/`)** → ✅ completada
  (pendiente opcional: capa de servicios más amplia)
- **Fase 6 — Permisos asignables a roles + arranque del frontend web** → ✅ completada
- **Fase 7 — Tolerancia de fábrica asimétrica por marca** → ✅ completada
- **Fase 8 — Descuentos y Sucursales (frontend) + reconciliación de BD real** → ✅ completada
- **Fase 9 — Auditoría (frontend), última pantalla del menú** → ✅ completada
- **Fase 10 — Descuentos robustos, domicilio, clientes por sucursal, marcas,
  filtros jerárquicos, suspendidos** → ✅ completada
- **Fase 11 — Importación desde Excel/XML/PDF, reimpresión de ticket** → ✅
  completada (4 rondas: núcleo Excel+XML, feedback de uso real con PDF y
  selector de sucursal, robustez del parser de PDF + UX de importación,
  reimpresión de ticket + barrido de verificación — ver ROADMAP.md y
  CHANGELOG.md para el detalle de cada ronda)
- **Fase 12 — 6 mejoras post-verificación**: advertencia de precio menor en
  importación, marca de reimpresión en el ticket, filtro de Ventas por
  cliente/vendedor, exportación a Excel (Ventas/Inventario/Auditoría),
  historial de costo/precio por producto, y ampliación de pruebas
  automatizadas para Fase 10/11 → ✅ completada (ver ADR-019, ADR-020 y
  CHANGELOG.md)
- **Fase 12b — sku automático desde código de proveedor al importar** → ✅
  completada (ver ADR-021) — cierra el único pendiente que había quedado
  documentado desde la Fase 11 original.
- **Fase 12c — reporte imprimible/PDF de Ventas + investigación de paridad
  Android** → ✅ completada (ver ADR-022) — Android quedó documentado como
  investigación, sin cambios de código (no hay forma de compilar/probar
  Kotlin en este entorno).
- **Fase 13 — Configuración del negocio + surtido por lista auditable** → ✅
  completada (ver ADR-023). Incluye un reanálisis general del sistema con 4
  hallazgos propuestos (no implementados): falta `.env` real (`SECRET_KEY`
  corriendo con el valor de ejemplo), puerto de Postgres expuesto a la red,
  reportes ya construidos en el backend (`informes.py`) sin pantalla en la
  web, y `reporte-surtidos` que podría usar el lote real en vez de agrupar
  por reloj — detalle completo en `CHANGELOG.md` ("Fase 13").
- **Fase 14 — POS con filtros/granel visibles + módulo Listas** → ✅
  completada (ver ADR-024, ADR-025). Incluye la corrección de metadatos de
  2 lotes de importación reales del dueño que estaban mal etiquetados
  (Api-Aba, Agromas) — sin confirmar nada al catálogo, esa decisión sigue
  siendo del dueño.
- **Fase 15 — datos de catálogo (especies/categorías) + filtros limpios +
  seguridad + Reportes** → ✅ **completada y verificada (2026-07-16)**.
  El código se había escrito por error (malentendido de "escríbelo" cuando el
  dueño solo pedía terminar el plan en MD), y la sesión se cortó antes de
  probar nada. Una sesión de retoma **verificó todo end-to-end sin reescribir
  código**: confirmó el estado real (git + BD), levantó los servicios, corrió
  37 pytest + `smoke_e2e.py` en verde, y probó cada pantalla en el navegador
  (Productos con filtros en cascada + modal que guarda especie/categoría; POS
  con cascada y botones granel; Reportes con 3 pestañas y `reporte-surtidos`
  agrupando por lote real; regresión de las demás pantallas sin errores). La
  razón de fondo que motivó la fase — `confirmar_lote()` nunca mapeaba
  `categoria_sugerida` a `categoria_id` ni tocaba `especie_id`, dejando los 26
  productos Agromas con esos campos en `NULL` — quedó corregida y verificada.
  Detalle completo en el CHANGELOG ("Fase 15 VERIFICADA") y `PLAN_FASE15.md
  §-1`. Hallazgo al levantar: el `.venv` no tenía `openpyxl`/`pdfplumber`
  instalados (sí en `requirements.txt`); ya instalados. Decisiones que siguen
  siendo del dueño: clasificar los 4 productos Agromas ambiguos y confirmar
  los 2 lotes de importación pendientes.

**Las 17 pantallas del menú del frontend son funcionales y verificadas**
(16 + la nueva **Reportes** de Fase 15), incluidas **Importar catálogo** y
**Listas**. El paso manual de guardar los permisos
`productos.ver_costo`/`catalogo.importar` para Gerente ya no está pendiente
— se hizo y se verificó dentro de la Fase 15.

Todo verificado end-to-end contra Postgres real con `tests/smoke_e2e.py`
(**22 checks en verde**: RBAC, JSONB, ventas híbridas, tolerancia de fábrica,
dashboard, cancelación exacta, bloqueo de sobreventa ACID, bitácora completa) +
`pytest` (**37 unitarias**: 8 de tolerancia asimétrica y RBAC + 28 de Fase
10/11 — matching de importación, cálculo de margen, parseo de CFDI,
especificidad de reglas de descuento, agregadas en Fase 12 — + 1 de
`crear_superadmin`) + verificación manual en navegador contra la **BD real**
`negocio` (producto → surtido → descuento → venta con descuento
auto-aplicado → historial → auditoría con tolerancia asimétrica en 3
escenarios; en Fase 11, las 14 pantallas del menú probadas contra la BD real
incluyendo cambio de sucursal activa y reimpresión de ticket; en Fase 12, las
6 mejoras nuevas verificadas en vivo, incluyendo un lote de importación de
prueba con match real contra un producto existente para confirmar la
advertencia de precio, cancelado después de verificar; en Fase 13, la
Configuración probada guardando datos reales y confirmando que el ticket y
el reporte de Ventas los reflejan, y el ingreso por lista probado con 2
líneas + historial con drill-down al detalle, verificando también que el
endpoint viejo de un solo producto — usado por Android — no se rompió; en
Fase 14, los filtros del POS probados en vivo contra el catálogo real —26
productos Agromas, 0 Api-Aba— confirmando que el filtro de marca acota
correctamente y que la búsqueda queda limitada al filtro activo, y el
módulo Listas verificado mostrando los 3 grupos de marca reales con
Exportar Excel funcionando).
