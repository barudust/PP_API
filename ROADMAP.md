# ROADMAP — PP_API

> 👉 **¿Sesión nueva? Lee primero [`EMPEZAR_AQUI.md`](EMPEZAR_AQUI.md).**
> Backlog (⬜) · En progreso (🚧) · Completado (✅). Mover/tachar tareas al avanzar.
> Trabajo por fases; se revisa con el dueño entre fases.

Última actualización: **2026-07-16**

---

## ✅ FASE 1 — Fundación, Configuración y Seguridad (COMPLETADA)

- ✅ Crear `MEMORIA.md`, `ROADMAP.md`, `CHANGELOG.md` (protocolo de trabajo)
- ✅ `config.py`: configuración centralizada por `.env` (sin dependencias nuevas)
- ✅ `.env.example` con variables documentadas
- ✅ Sacar `SECRET_KEY` y `DATABASE_URL` del código → leer de `config`
- ✅ CORS configurable por `.env` (soporte Android + web)
- ✅ `dependencies.py`: `get_current_user` (JWT) + `require_roles(...)` (RBAC)
- ✅ Constantes de rol canónicas: `vendedor`, `gerente`, `superadmin`
- ✅ Aplicar RBAC **gradual** a superficies de administración:
  - `usuarios` (todo) → superadmin
  - `sucursales` (escrituras) → superadmin
  - `productos` (crear/editar/borrar) → gerente+
  - `informes` (reportes) → gerente+
- ✅ `requirements.txt` re-generado en UTF-8 limpio
- ✅ Alinear roles del seed (`llenar_datos.py`: `admin` → `superadmin`)
- ⬜ **(Revisión con dueño)** Confirmar qué endpoints puede exigir token sin
  romper la app Android actual, y coordinar el frontend.

## ✅ FASE 2 — Auditoría Física Avanzada + Inventario Heterogéneo (COMPLETADA)

**Auditoría tipificada (Stocktaking):**
- ✅ Catálogo `tipo_ajuste` en `constants.py`: `MERMA_OPERATIVA`,
  `VARIACION_FABRICA`, `ERROR_SISTEMA`, `CADUCIDAD`
- ✅ Columna `ajuste_inventario.tipo_ajuste` (migración a1b2c3d4e5f6)
- ✅ Lógica de **tolerancia de fábrica**: calcula la tolerancia esperada según
  nº de empaques y sugiere `VARIACION_FABRICA` si la diferencia cae dentro
- ✅ Campo `producto.tolerancia_unidad` (variación esperada por empaque)
- ✅ Endpoint `GET /auditoria/plan-conteo` con filtros (tipo/marca/categoría/
  ubicación/atributos JSONB) — pensado para celular
- ✅ Campo `producto.ubicacion_fisica` para el barrido ordenado
- ✅ Endpoint `GET /auditoria/ajustes` (historial de ajustes por tipo)

**Atributos dinámicos (híbrido FK + JSONB):**
- ✅ Columna `producto.atributos_extra` JSONB (migración)
- ✅ Índice GIN sobre `atributos_extra`
- ✅ Schemas Pydantic aceptan `atributos_extra`, `tolerancia_unidad`, `ubicacion_fisica`
- ✅ `GET /productos/atributos-disponibles?tipo=` (llaves/valores para filtros dinámicos)
- ✅ Filtro de productos por atributos JSONB y por dimensiones relacionales
- ⬜ (Opcional, pendiente) Catálogo `tipo_producto` como FK real en vez de texto libre

## ✅ FASE 3 — Dashboard SuperAdmin (KPIs) (COMPLETADA)

Router `dashboard` (solo superadmin, filtro opcional por `sucursal_id`):
- ✅ `GET /dashboard/resumen` — ventas hoy/semana/mes, tickets, stock crítico, cajas
- ✅ `GET /dashboard/ventas-por-sucursal`
- ✅ `GET /dashboard/top-productos` (por ingreso y cantidad)
- ✅ `GET /dashboard/stock-critico` (consolidado o por sucursal)
- ✅ `GET /dashboard/cajas` (abiertas ahora + cerradas hoy con diferencia)
- ✅ `GET /dashboard/rendimiento-financiero` (ventas, descuentos, descuadre de caja)

## ✅ FASE 4 — Transaccionalidad y Corrección de Bugs (COMPLETADA)

- ✅ `venta_detalle`: `es_granel` + `cantidad_base` (adelantado en Fase 2)
- ✅ Reescribir `cancelar_venta` usando `cantidad_base` (no inferencia)
- ✅ Escribir en `historial_inventario` en venta / cancelación / ingreso
  (vía `services/inventario_service.registrar_movimiento`)
- ✅ Quitar `SUCURSAL_DEFAULT=1` hardcodeado → `settings.SUCURSAL_DEFAULT` o payload
- ✅ `usuarios` PUT con `UsuarioUpdate` (no re-hashea si no cambia contraseña) +
  endpoint `POST /usuarios/{id}/cambiar-password`
- ✅ Validación de rol permitido al crear/editar usuario (`ROLES_VALIDOS`)
- ✅ Bloqueo de stock negativo configurable (`PERMITIR_STOCK_NEGATIVO`)
- ✅ `ingreso-inventario` ahora corre en transacción atómica

## ✅ FASE 5 — Reestructura Profesional (COMPLETADA)

- ✅ Paquete `models/` por dominio + re-export
- ✅ Paquete `schemas/` por dominio + re-export
- ✅ `constants.py` para constantes de dominio
- ✅ `alembic/env.py` usa la URL de `.env` (fuente única)
- ✅ Smoke test e2e en `tests/smoke_e2e.py` (reemplaza al viejo `si.py`)
- ✅ Limpieza: eliminado `si.py`; `docker-compose.yml` sin `version` obsoleto
- ✅ **Migrado todo a paquete `app/`** (core/, models/, schemas/, routers/, services/)
- ✅ Capa de servicios inicial (`inventario_service`, `auditoria_service`)
- ✅ `venv/` verificado: NO estaba versionado (ya bien ignorado)
- ✅ Tests con pytest (`tests/test_unit.py`) + `requirements-dev.txt`
- ✅ `README.md` de arranque
- ⬜ (Opcional) Mover más lógica de negocio a `app/services/`
- ⬜ (Opcional) `tipo_producto` como FK real en vez de texto libre

## ✅ FASE 6 — Permisos + arranque del frontend web (COMPLETADA)

- ✅ Tablas `permiso` + `rol_permiso` (migración `b2c3d4e5f6a7`)
- ✅ Catálogo de 18 permisos + defaults por rol (sync al arrancar)
- ✅ `GET /auth/me` (usuario + permisos) · `require_perm(...)`
- ✅ Router `roles` (catálogo, matriz por rol, edición)
- ✅ Frontend `../punto-peludo-web` (Vite+React+TS+Tailwind), app unificada por permisos
- ✅ Pantallas: Login, POS (carrito/código de barras/ticket), Caja, Panel, Roles
- ✅ Verificado e2e en navegador (venta real → ticket → dashboard)

### Frontend — pantallas
- ✅ Productos (lista + filtros dinámicos JSONB + crear/editar/suspender)
- ✅ Inventario (ver stock de sucursal + KPIs) y Surtir (ingreso de mercancía)
- ✅ Usuarios (solo admin: crear/editar, asignar rol y sucursal, cambiar contraseña)
- ✅ Clientes (lista + alta/edición)
- ✅ Ventas (historial + detalle + cancelar)
- ✅ Descuentos (reglas por catálogo/cliente/marca/producto, alta + baja)
- ✅ Sucursales (tarjetas + crear/editar)
- ✅ Auditoría (conteo por producto con filtros de tipo/ubicación/atributos +
  registro de ajuste con tolerancia asimétrica por marca + historial reciente)
- ✅ Diseño base: tipografía Inter (auto-alojada), marca Punto Peludo
- **Con esto, las 12 pantallas del menú están 100% funcionales.**
- ⬜ Pulido de diseño / branding (colores, logo, tipografía) — pendiente, siguiente paso
- ⬜ (Backend) migrar endpoints POS a `require_perm` cuando Android envíe token
- ⬜ (Opcional) editar `marca.tolerancia_bajo/alto` desde la UI (hoy solo por API)

## ✅ FASE 7 — Tolerancia de fábrica por marca (COMPLETADA)
- ✅ `marca.tolerancia_bajo` / `tolerancia_alto` (asimétrica, por empresa) — migración `c3d4e5f6a7b8`
- ✅ `producto.tolerancia_unidad` como override simétrico
- ✅ `analizar_tolerancia` asimétrica; `/auditoria/ajuste` hereda de la marca
- ✅ Pantalla Ventas (historial + cancelar) · `COMO_EJECUTAR.md`

## ✅ FASE 8 — Cierre de pantallas pendientes: Descuentos y Sucursales (COMPLETADA)
- ✅ Pantalla Descuentos (alta/baja de reglas por catálogo/cliente/marca/producto)
- ✅ Pantalla Sucursales (crear/editar; solo SuperAdmin)
- ✅ **Verificado end-to-end contra la BD real `negocio`** (no una de prueba):
  creación de producto, surtido de inventario, regla de descuento, y una venta
  real donde el descuento se aplicó automáticamente (confirma que POS,
  Descuentos e Inventario funcionan juntos correctamente).
- ✅ Reconciliada la BD real con Alembic: existía el esquema completo (aplicado
  manualmente en algún momento) pero sin tabla `alembic_version` y sin el índice
  GIN de `producto.atributos_extra`. Se creó el índice faltante y se hizo
  `alembic stamp head` para que futuras migraciones funcionen correctamente.
## ✅ FASE 9 — Auditoría (frontend) + fix de campos faltantes en Productos (COMPLETADA)
- ✅ Pantalla Auditoría: lista filtrable (tipo/ubicación/atributos JSONB) con
  captura de físico por producto, selector de tipo (o automático), y registro
  contra `POST /auditoria/ajuste`; muestra el resultado (tolerancia bajo/alto,
  dentro/fuera, tipo aplicado) y un historial de "Ajustes recientes".
- ✅ Se detectó y corrigió un hueco real: el formulario de Productos enviaba
  `ubicacion_fisica` y `tolerancia_unidad` en el payload pero **no tenía los
  campos en la UI** para capturarlos — nadie podía asignar la ubicación física
  necesaria para el barrido de auditoría. Se agregaron ambos campos al modal.
- ✅ **Verificado end-to-end con datos reales**: se creó una marca con
  tolerancia asimétrica (bajo 0.3 / alto 0.1 por pieza), se asignó a un
  producto real vía la UI, y se probaron los 3 escenarios de tolerancia en el
  navegador contra la BD real: faltante dentro de tolerancia → *Variación de
  fábrica*; faltante fuera → *Merma operativa*; sobrante fuera → *Error de
  sistema*. Los tres calcularon el límite correcto en cada paso.
- ✅ `StubPage.tsx` eliminado (ya no queda ninguna pantalla "de adorno").

**Con esto, las 12 pantallas del menú están operativas y verificadas de punta
a punta contra la base de datos real.** Lo único pendiente es el pulido visual.

## ✅ FASE 10 — Descuentos robustos, domicilio, clientes por sucursal, marcas, filtros jerárquicos, suspendidos (COMPLETADA)
- ✅ Motor de descuentos: prioridad por especificidad correcta (antes dependía
  de un `ORDER BY` frágil) + validación anti-conflicto (marca vs. producto de
  esa marca, mismo cliente/sucursal) + edición de reglas (antes solo alta/baja)
- ✅ `regla_descuento.sucursal_id` — reglas de cliente heredan la sucursal del
  cliente automáticamente; reglas de marca pueden acotarse a una sucursal
- ✅ Venta a domicilio (`venta.tipo_entrega`): sin descuentos automáticos
- ✅ Descuento manual del checkout: monto fijo → **porcentaje** del total
- ✅ `cliente.sucursal_id` obligatorio — los clientes ya no son globales
- ✅ Pantalla **Marcas** (CRUD, faltaba por completo)
- ✅ Filtro jerárquico marca→especie (`GET /productos/filtros`) en Productos
- ✅ Vista de productos **Suspendidos** + botón **Reactivar**
- ✅ Precio a granel: referencia de división exacta visible junto al campo
- ✅ RBAC cerrado en `clientes`, `descuentos` y escritura de `marcas` (antes abiertos)
- ✅ Fix de un bug real de UI: el ticket del POS mostraba precio de catálogo en
  las líneas pero el total ya traía el descuento — ahora usa el detalle real
  de la venta guardada

## ✅ FASE 11 — Importación desde Excel / XML / PDF (COMPLETADA, 2 rondas)
- ✅ Módulo aparte `/importacion` (Excel de catálogo, factura XML/CFDI, y PDF
  de lista de precios de distribuidor), con vista previa editable línea por
  línea antes de tocar el catálogo real (nada se crea automático — decisión
  `pendiente/crear/vincular/ignorar` por línea, elegida por el dueño).
- ✅ Parser de Excel con dos modos por hoja: "bloques de categoría" (detectado
  por estilo bold/tamaño de fuente, no por texto) y "tabla con encabezados"
  (`Nombre/Kg/Precio` o `Producto/Presentación/Precio de lista/Código`,
  búsqueda de encabezado en toda la hoja, no solo las primeras filas) —
  verificado contra 6 archivos reales del dueño.
- ✅ Parser de CFDI 4.0: costo unitario real ya con descuento aplicado,
  código SAT y código de proveedor por línea.
- ✅ Parser de PDF (`pdfplumber`): tablas de listas de precio de distribuidor
  con encabezado partido en varias filas — el precio siempre se trata como
  costo (pasa por margen), nunca como venta directa.
- ✅ Emparejamiento por nombre (fuzzy) contra el catálogo existente, siempre
  como sugerencia — la decisión final es manual.
- ✅ Margen de venta por marca (`marca.margen_default`) con excepción por
  producto (`producto.margen_override`); costo de compra guardado en
  `producto.costo`, visible solo con el permiso `productos.ver_costo`; se
  recalcula solo al asignar/cambiar la marca de una línea.
- ✅ Confirmación: crea productos (suspendidos y sin precio si no había uno
  real, para no dejarlos vendibles a $0), vincula productos existentes
  (actualiza costo, y precio si se pide explícitamente), y opcionalmente
  genera el ingreso de inventario correspondiente (stock + bitácora) — el
  Excel de "pedidos" también puede traer cantidad, no solo el XML.
- ✅ Botones masivos en la vista previa: asignar marca a todas las líneas,
  aceptar sugerencias, marcar vinculados para actualizar precio, ignorar
  pendientes.
- ✅ Verificado end-to-end contra la BD real con 6 archivos del dueño
  (Agromas, Api-Aba, Winners, CFDI, Excel de pedidos, PDF Tlaxcala/API-ABA)
  — detalle completo en `CHANGELOG.md` (2 entradas).
- ✅ Editar `producto.sku`/código de proveedor automáticamente desde
  `NoIdentificacion` del CFDI (o `Item`/`Código` de PDF/Excel) para mejorar
  matches futuros por código en vez de solo nombre — implementado en Fase
  12b, ver abajo.
- ✅ **Reimpresión de ticket** (4ª ronda, no era parte del alcance original de
  Fase 11 pero surgió al pedir verificación completa del sistema): botón
  "Reimprimir ticket" en el detalle de una venta en **Ventas**, usando el
  mismo componente `TicketModal` que POS. Ver ADR-018 en `MEMORIA.md` y la
  entrada "Fase 11d" en `CHANGELOG.md`.
- ✅ **Barrido de verificación de las 14 pantallas del menú** contra la BD
  real, incluido el cambio de sucursal activa en cada una — todo funcional.

---

## ✅ FASE 12 — 6 mejoras propuestas tras el barrido de verificación (COMPLETADA)
El dueño pidió una lista de ideas de mejora (analiza todo, propón, sobran
créditos) y luego implementar las primeras 6 de las 9 propuestas de una vez.
- ✅ **Advertencia de precio menor en importación**: si el precio sugerido de
  una línea vinculada queda por debajo del precio actual del producto, la
  vista previa lo marca con un aviso ámbar. `GET /importacion/lotes/{id}`
  ahora incluye `precio_actual_producto` por línea (join con `producto`, no
  se guarda en BD).
- ✅ **Marca "REIMPRESIÓN" en el ticket**: visible solo cuando se reimprime
  desde Ventas, nunca en el ticket original de POS.
- ✅ **Filtro de Ventas por cliente y vendedor**: `GET /ventas/` acepta
  `cliente_id`/`usuario_id`; el selector de vendedor se arma con los nombres
  ya presentes en el listado cargado (ver ADR-019), sin depender del
  endpoint de usuarios (restringido a superadmin).
- ✅ **Exportar a Excel** (Ventas, Inventario, Auditoría): tres endpoints
  nuevos usando `openpyxl` (`app/services/export_service.py`) + botón
  "Exportar Excel" en cada pantalla. PDF quedó fuera a propósito (requeriría
  una dependencia nueva de generación de PDF, no pedida explícitamente).
- ✅ **Historial de costo/precio por producto**: nueva tabla
  `producto_historial_precio` (migración `f6a7b8c9d0e1`), se escribe desde
  edición manual de Productos y desde `confirmar_lote` al vincular/actualizar
  un producto. Botón de historial en Productos (mismo permiso que ver costo).
  Ver ADR-020.
- ✅ **Pruebas automatizadas ampliadas**: `tests/test_fase10_11_unit.py` (28
  pruebas nuevas, sin BD) cubre matching/normalización/margen de importación,
  parseo de CFDI, y especificidad de reglas de descuento — antes Fase 10 y
  Fase 11 solo tenían verificación manual. Total de la suite: 37 pruebas.
- ⬜ (No implementadas en esta ronda, quedaron como #7-9 de la lista original
  de 9 propuestas): alertas proactivas de stock crítico, paridad de la app
  Android con la web, limpieza de datos de prueba en la BD real.

---

## ✅ FASE 12b — sku automático desde código de proveedor (COMPLETADA)
El dueño pidió seguir mejorando el sistema sin especificar qué ("mejora algo
o propón algo"). Se cerró el pendiente ya documentado de Fase 11.
- ✅ `producto.sku` se rellena automáticamente al confirmar una importación
  con el código de proveedor de la línea (`NoIdentificacion` del CFDI,
  `Item` del PDF, `Código` del Excel) — tanto al crear un producto nuevo como
  al vincular uno existente que todavía no tenga sku. Nunca pisa un sku ya
  capturado, y nunca genera un `IntegrityError` por duplicado (se verifica
  disponibilidad antes de asignar). Ver ADR-021 en `MEMORIA.md`.
- ✅ Verificado con un script directo contra la API (3 escenarios: crear con
  código libre, crear con código duplicado, vincular a producto sin sku) —
  los 3 productos sintéticos de prueba se suspendieron al terminar.

---

## ✅ FASE 12c — Reporte imprimible de Ventas + investigación Android (COMPLETADA)
El dueño pidió continuar con "lo más corto" de los pendientes sin especificar
cuál. Se investigó Android (rápido, sin cambios de código) y se implementó
el pendiente que sí se podía completar y verificar del todo esta sesión.
- ✅ **Investigación de paridad Android** (sin implementación): confirmado
  que la app Android **no tiene** reimpresión de ticket (`VentaActivity.kt`
  solo muestra un Toast tras cobrar) ni selector de sucursal activa
  (`ID_SUCURSAL_SESION` se fija una sola vez al login). No se tocó código —
  este entorno no puede compilar/probar la app Android, así que editarla a
  ciegas no era responsable. Detalle en `CHANGELOG.md`.
- ✅ **Reporte imprimible/PDF de Ventas**: botón "Imprimir / PDF" que arma un
  reporte (encabezado + tabla filtrada + total) y usa `window.print()` — el
  usuario elige papel o "Guardar como PDF" desde el navegador. Se generalizó
  el mecanismo `@media print` que ya aislaba el ticket a una clase
  `.printable` reutilizable, sin agregar ninguna dependencia nueva de
  generación de PDF. Ver ADR-022 en `MEMORIA.md`.
- ⬜ (No implementado, el patrón ya existe si se pide) extender el mismo
  reporte imprimible a Inventario y Auditoría.

---

## ✅ FASE 13 — Configuración del negocio + surtido por lista auditable (COMPLETADA)
Dos pedidos concretos del dueño más un reanálisis general del sistema.
- ✅ **Configuración del negocio** (`/configuracion`): nombre, dirección,
  teléfono, RFC — usados en el ticket y en el reporte imprimible de Ventas
  en vez del texto fijo "PUNTO PELUDO". Nuevo permiso
  `configuracion.gestionar` (solo superadmin por defecto).
- ✅ **Surtir mercancía por lista, auditable**: el modal ahora acepta varias
  líneas (producto + cantidad) en una sola operación, con proveedor/nota
  opcionales. Nuevo `POST /ingreso-inventario/lote` (transacción atómica) +
  nuevo botón **"Historial de ingresos"** con drill-down a cada lote — antes
  no había forma de saber qué productos se recibieron juntos en una misma
  entrega. El endpoint de un solo producto (usado por la app Android)
  **no se tocó**. Ver ADR-023 en `MEMORIA.md`.
- ✅ **Reanálisis general del sistema** — 4 hallazgos propuestos, ninguno
  implementado a propósito (son propuestas para que el dueño decida):
  1. ⚠️ **Seguridad**: no existe `.env` real en `PP_API/` — el backend corre
     con el `SECRET_KEY` de ejemplo hardcodeado. Arreglo de 2 minutos, pero
     invalida las sesiones activas al aplicarlo.
  2. El puerto de Postgres en Docker se expone a toda la red local, no solo
     a `localhost` — con la contraseña débil del contenedor.
  3. **3 reportes completos y funcionales en el backend
     (`app/routers/informes.py`) sin ninguna pantalla en la web que los
     use** — ventas, surtidos y cortes de caja por rango de fecha, con
     nombres de cliente/vendedor ya resueltos. El permiso `reportes.ver` en
     el catálogo no protege nada hoy (huérfano).
  4. El reporte de surtidos agrupa por "mismo minuto + mismo usuario" para
     aproximar qué se recibió junto — con `ingreso_inventario_lote` ya
     existiendo, podría usar el lote real en vez de adivinar por reloj.

---

## ✅ FASE 14 — POS con filtros/granel visibles + módulo Listas (COMPLETADA)
Feedback denso del dueño tras usar el Punto de Venta.
- ✅ **Filtros en POS**: marca (siempre) + especie/animal + categoría
  (solo se muestran si hay opciones para la marca elegida — mismo endpoint
  que ya usaba Productos). Cubre el caso que pidió el dueño de "marca y
  animal, o tipo en algunos casos (maíz, collares)".
- ✅ **Búsqueda acotada al filtro activo**: consecuencia de mover el
  filtrado de marca/especie/categoría al servidor — la búsqueda de texto ya
  opera sobre el resultado filtrado, no sobre todo el catálogo.
- ✅ **Venta a granel visible desde la tarjeta**: antes solo se podía activar
  con un botón chico DESPUÉS de agregar al carrito. Ahora, si el producto
  admite granel, la tarjeta muestra "Pieza $X" / "Granel $Y/unidad" como dos
  botones directos.
- ✅ **Tarjetas de producto más grandes** — menos apretadas, texto más
  legible.
- ✅ **Catálogo real corregido**: se encontraron 2 lotes de importación
  reales del dueño (Api-Aba 219 líneas, Agromas "pedidos" 94 líneas)
  atascados en revisión con la marca mal puesta o sin marca — se corrigió
  la marca de ambos (el margen se recalculó solo). **No se confirmó nada**,
  siguen esperando que el dueño los revise en Importar catálogo. Se
  confirmó que Agromas ya tiene 26 productos reales en el catálogo (el
  dueño ya había confirmado esa parte por su cuenta). Ver ADR-024.
- ✅ **Módulo Listas** (`/listas`): precios actuales del catálogo agrupados
  por marca, con botón "Exportar Excel" y "Imprimir / PDF" (reutiliza
  patrones de Fase 12/12c). Se agrupa solo por marca porque
  `categoria`/`subcategoria` siguen vacíos en la BD real — no tenía caso
  construir un agrupamiento más fino sin datos que lo llenen. Ver ADR-025.

---

## ✅ FASE 15 — Datos de catálogo (especies/categorías) + filtros limpios + seguridad + Reportes (VERIFICADA 2026-07-16)
Esta fase se había implementado por un malentendido de instrucción (el dueño
solo había pedido escribir el plan) y la sesión se cortó antes de verificar
nada. Una sesión de retoma **verificó todo end-to-end** sin reescribir código:
37 pytest + `smoke_e2e.py` en verde, y cada pantalla probada en el navegador
contra la BD real. Detalle en `CHANGELOG.md` ("Fase 15 VERIFICADA") y
`PLAN_FASE15.md §-1`.
- ✅ **2.1** `.env` real con `SECRET_KEY` generado — **verificado**: el backend
  arranca limpio y el login (Admin/admin123) funciona. (Al levantarlo se
  detectó que faltaba instalar `openpyxl`/`pdfplumber` en el `.venv`; ya
  instalados.)
- ✅ **2.2** Permisos `productos.ver_costo`/`catalogo.importar` en Gerente —
  confirmados en la BD real.
- ✅ **2.3** Catálogo de 9 especies sembrado (Cerdo, Pollo, Pavo, Ganado de
  engorda, Ganado lechero, Ave de postura, Gallo, Ovino, Conejo) — confirmado
  (10 filas con "Perro").
- ✅ **2.4** 7 categorías simples (Suprema, Óptima, Súper Yema, CP, Porcimas,
  Regio, Más Lechón) — confirmadas.
- ✅ **2.5** 22/26 productos Agromas clasificados; 4 sin clasificar a propósito
  (se ven con el botón "Sin especie"). El modal de edición guarda
  especie/categoría — **verificado** (persiste en BD y en la tabla).
- ✅ **2.6** `confirmar_lote()` resuelve `categoria_sugerida` al importar —
  código en su sitio; no se confirmó un lote real (sigue siendo decisión del
  dueño confirmar los 2 lotes pendientes).
- ✅ **2.7** Filtros de Productos y POS reescritos (sin "Tipo" ni atributos
  JSONB; cascada Marca → Categoría → Subcategoría → Especie). **Verificado**:
  la cascada acota opciones y productos; la subcategoría se oculta porque aún
  no hay ninguna en BD (diseño correcto).
- ✅ **2.8** Pantalla **Reportes** (`/reportes`, 3 pestañas) — **verificada**
  con datos reales; `reporte-surtidos` agrupa por `lote_id` real vs "ingreso
  suelto".

Fuera de alcance de esta fase (confirmado explícitamente por el dueño):
alertas por correo, paridad con la app Android, limpieza de datos de prueba
de la BD real, exposición de Postgres a la red local.

Pendiente opcional para el dueño: clasificar los 4 productos Agromas ambiguos;
confirmar (o cancelar) los 2 lotes de importación en `revision`.

---

## ✅ FASE 16 — Módulo Listas gráfico (COMPLETADA 2026-07-17)
Plan completo en [`PLAN_FASE16.md`](PLAN_FASE16.md), decisiones de §6
confirmadas con el dueño en el chat antes de escribir código. Detalle técnico
completo en `CHANGELOG.md` ("Fase 16") y `MEMORIA.md` (ADR-026, ADR-027).
- ✅ Parser de plantilla (`lista_plantilla_service.py`): clasifica encabezado
  vs producto por formato de celda (negrita + relleno de color de marca),
  nivel derivado del tinte, dos paneles independientes por hoja.
- ✅ Resolver de vínculos por nombre normalizado con contexto de encabezados
  (nunca adivina entre productos de otra especie/línea) — 15/26 productos
  reales de Agromas vinculados automático, 4 más a mano vía el CRUD (19/26
  total; los 7 restantes son duplicados exactos o el mismo caso ambiguo que
  Fase 15 ya había dejado sin clasificar).
- ✅ Nueva tabla `lista_plantilla_fila` + CRUD completo (`/listas/*`) —
  **estructura editable desde la web** (decisión §6.6, no estaba en el
  análisis original del plan).
- ✅ Export Excel fiel al estilo de marca (regenerado desde los datos
  vigentes, no copiado del archivo original — ver ADR-027) e Imprimir/PDF.
- ✅ `ListasPage.tsx` rediseñada: vista gráfica de dos paneles con color de
  marca cuando hay plantilla (pestañas para Api-Aba: Hoja1/Hoja2/Vimifos),
  tabla plana de respaldo para marcas sin plantilla.
- ✅ 11 pruebas unitarias nuevas (`test_fase16_unit.py`, sin BD) — suite
  completa 48 pytest en verde. Verificado en el navegador contra la BD real:
  vista gráfica de Agromas/Api-Aba, edición inline, agregar/eliminar fila.

**Decisión de alcance no explícitamente pedida**: los 26 productos Agromas ya
confirmados se **vincularon, no se renombraron** (ver ADR-026) — pendiente de
que el dueño confirme si prefiere renombrarlos al nombre corto de la
plantilla. El lote de importación "Formato de pedidos" (94 líneas) tampoco
se tocó — sigue siendo su decisión confirmarlo desde `/importacion`.

---

## 🐞 Bugs conocidos
Todos los bugs listados en fases previas fueron resueltos (ver MEMORIA.md §6).
Sin bugs abiertos conocidos al 2026-07-16.

✅ **Resuelto en Fase 15** (antes pendiente manual): los permisos
`productos.ver_costo`/`catalogo.importar` para Gerente ya están guardados en
la BD real (confirmado).

✅ **Resuelto en Fase 15** (hallazgo de seguridad de Fase 13): ya existe un
`.env` real en `PP_API/` con un `SECRET_KEY` generado (64 chars), no el valor
de ejemplo. Verificado que el backend arranca y el login funciona con él.
`.env` está en `.gitignore` — no se versiona.

⚠️ Sigue pendiente (fuera del alcance de Fase 15, hallazgo de Fase 13): el
puerto de Postgres en `docker-compose.yml` se expone a toda la red local
(`"5433:5432"`). Cambiar a `"127.0.0.1:5433:5432"` si preocupa.
