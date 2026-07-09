# Cómo ejecutar Punto Peludo

Guía para levantar todo el sistema. Son 3 piezas:

| Pieza | Carpeta | Qué es |
|-------|---------|--------|
| **Backend** (API) | `PP_API/` | FastAPI + PostgreSQL. El cerebro. |
| **Web** | `../punto-peludo-web/` | Panel de administración + punto de venta (React). |
| **Android** | `../PuntoPeludo/` | App móvil del cajero (opcional). |

Todo vive bajo `Documents/Negocio/Punt o de venta/`.

---

## Requisitos
- **Docker Desktop** (para la base de datos PostgreSQL)
- **Python 3.11+** (backend)
- **Node.js 18+** y **npm** (web)

---

## 1) Base de datos

Desde `PP_API/`:
```bash
docker compose up -d
```
Levanta PostgreSQL 15 en `localhost:5433` (usuario `postgres`, contraseña `1234`,
base `negocio`). Los datos persisten aunque apagues la PC.

---

## 2) Backend (API)

Desde `PP_API/`:
```bash
# Entorno virtual (solo la primera vez)
python -m venv venv
#   Windows PowerShell:  .\venv\Scripts\Activate.ps1
#   Git Bash / Linux:    source venv/Scripts/activate
pip install -r requirements.txt

# Migraciones (crea/actualiza las tablas)
alembic upgrade head

# Crear el primer SuperAdmin (necesario por el control de permisos)
python crear_superadmin.py            # usuario: Admin  ·  contraseña: admin123

# Correr la API
uvicorn app.main:app --reload
```
La API queda en **http://127.0.0.1:8000** · documentación interactiva en **/docs**.

Config opcional en `.env` (copiar de `.env.example`): `DATABASE_URL`, `SECRET_KEY`,
`CORS_ORIGINS`, `SUCURSAL_DEFAULT`, `PERMITIR_STOCK_NEGATIVO`.

(Opcional) Datos de prueba, con la API corriendo: `python llenar_datos.py`

---

## 3) Web (panel + punto de venta)

Desde `../punto-peludo-web/`:
```bash
npm install               # solo la primera vez
npm run dev               # http://localhost:5173
```
Abre **http://localhost:5173** y entra con `Admin` / `admin123`.

- La URL de la API se configura en `punto-peludo-web/.env` → `VITE_API_URL`.
- El origen `http://localhost:5173` ya está permitido en el CORS del backend.
- Según los **permisos** del usuario, verá el POS, la administración o todo.

Para compilar a producción: `npm run build` (genera `dist/`), `npm run preview` para
previsualizar.

---

## Orden rápido (resumen)

```bash
# terminal 1  (base de datos + API)
cd PP_API
docker compose up -d
alembic upgrade head
python crear_superadmin.py     # solo la 1ª vez
uvicorn app.main:app --reload

# terminal 2  (web)
cd ../punto-peludo-web
npm run dev
```

---

## Pruebas
- Backend: `pytest -q` (unitarias) · `python tests/smoke_e2e.py` (e2e, con la API arriba).
- Web: `npm run build` (chequeo de tipos + compilación).

## Problemas comunes
- **La web no carga datos / error de red**: revisa que la API esté en el puerto 8000
  y que `VITE_API_URL` apunte ahí.
- **CORS**: agrega el origen de tu web a `CORS_ORIGINS` en el `.env` del backend.
- **401 al entrar**: crea el usuario con `python crear_superadmin.py`.
- **Docker no arranca**: abre Docker Desktop y espera a que el engine esté listo.
- **`uvicorn: command not found`**: activa el `venv` antes.
