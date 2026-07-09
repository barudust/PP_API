# ROADMAP — PP_API

> Backlog (⬜) · En progreso (🚧) · Completado (✅). Mover/tachar tareas al avanzar.
> Trabajo por fases; se revisa con el dueño entre fases.

Última actualización: **2026-07-08**

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
- ✅ Diseño base: tipografía Inter (auto-alojada), marca Punto Peludo
- ⬜ Auditoría (plan de conteo móvil + ajuste con tolerancia por marca)
- ⬜ Descuentos · Sucursales
- ⬜ Pulido de diseño / branding (colores, logo, tipografía) — pendiente
- ⬜ (Backend) migrar endpoints POS a `require_perm` cuando Android envíe token

## ✅ FASE 7 — Tolerancia de fábrica por marca (COMPLETADA)
- ✅ `marca.tolerancia_bajo` / `tolerancia_alto` (asimétrica, por empresa) — migración `c3d4e5f6a7b8`
- ✅ `producto.tolerancia_unidad` como override simétrico
- ✅ `analizar_tolerancia` asimétrica; `/auditoria/ajuste` hereda de la marca
- ✅ Pantalla Ventas (historial + cancelar) · `COMO_EJECUTAR.md`

---

## 🐞 Bugs conocidos
Todos los bugs listados en fases previas fueron resueltos (ver MEMORIA.md §6).
Sin bugs abiertos conocidos al 2026-07-08.
