# CHANGELOG — PP_API

> Registro de qué se modificó en cada iteración y por qué.
> Formato: [Fecha] — Fase — resumen; luego archivos tocados.

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
