# PP_API — ERP + POS Multi-Sucursal

API REST (FastAPI + PostgreSQL) para un negocio de alimento animal, accesorios y
farmacia veterinaria. Un solo backend sirve a la **app Android** (POS del cajero)
y a la **web de administración** (SuperAdmin / Gerente).

> Documentación viva del proyecto: [MEMORIA.md](MEMORIA.md) ·
> [ROADMAP.md](ROADMAP.md) · [CHANGELOG.md](CHANGELOG.md)

## Stack
FastAPI · `databases` (async) + SQLAlchemy **Core** · asyncpg · PostgreSQL 15 ·
Alembic · JWT (python-jose) + bcrypt. Config por `.env` (sin dependencias extra).

## Puesta en marcha

```bash
# 1. Base de datos (Docker) — expone Postgres en localhost:5433
docker compose up -d

# 2. Entorno e instalación
python -m venv venv
#   Windows:  .\venv\Scripts\Activate.ps1
#   Linux/Mac: source venv/bin/activate
pip install -r requirements.txt

# 3. Configuración (opcional; hay defaults de desarrollo)
cp .env.example .env        # y edita SECRET_KEY, CORS_ORIGINS, etc.

# 4. Migraciones
alembic upgrade head

# 5. Crear el SuperAdmin inicial (bootstrap requerido por el RBAC)
python crear_superadmin.py          # Admin / admin123 por defecto

# 6. Correr la API
uvicorn app.main:app --reload       # docs interactivas en http://127.0.0.1:8000/docs
```

Datos de prueba opcionales (con la API corriendo): `python llenar_datos.py`

## Pruebas

```bash
pip install -r requirements-dev.txt

# Unitarias (lógica pura, sin BD)
pytest -q

# End-to-end (requiere API corriendo + SuperAdmin creado)
python tests/smoke_e2e.py
```

## Estructura

```
app/
  main.py            # App FastAPI + CORS + routers
  core/              # config, database, security, dependencies (RBAC), constants
  models/            # Tablas SQLAlchemy Core, por dominio
  schemas/           # Modelos Pydantic, por dominio
  routers/           # Endpoints por dominio (incl. dashboard, auditoria)
  services/          # Lógica de negocio reutilizable (inventario, auditoría)
alembic/             # Migraciones (usan la URL de .env)
tests/               # Unitarias (pytest) + smoke e2e
crear_superadmin.py  # Bootstrap del primer SuperAdmin
llenar_datos.py      # Seed vía API
```

## Roles (RBAC)
- **vendedor** — POS de su sucursal (ventas, su caja, lectura de inventario).
- **gerente** — su sucursal: ajustes/auditoría, reportes, supervisión de cortes.
- **superadmin** — acceso total: catálogo global, sucursales, dashboard, KPIs.

## Notas de negocio
- El inventario se guarda **siempre en la unidad mínima** (kg/ml/pza). Los bultos
  se convierten con `producto.contenido_neto`.
- Venta híbrida: paquete cerrado (`precio_base`) o granel (`precio_granel`).
- Ventas y cortes corren en **transacciones atómicas** (ACID).
- Atributos por tipo de producto en `producto.atributos_extra` (JSONB) → filtros
  dinámicos en el frontend.
