# MEMORIA DEL PROYECTO — PP_API (ERP + POS Multi-Sucursal)

> Documento vivo. Registra decisiones arquitectónicas, convenciones de código,
> dependencias y estado del sistema. **Leer esto antes de tocar cualquier lógica.**

Última actualización: **2026-07-08**

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

Todo verificado end-to-end contra Postgres real con `tests/smoke_e2e.py`
(**22 checks en verde**: RBAC, JSONB, ventas híbridas, tolerancia de fábrica,
dashboard, cancelación exacta, bloqueo de sobreventa ACID, bitácora completa) +
`pytest` (7 unitarias de tolerancia y RBAC).
