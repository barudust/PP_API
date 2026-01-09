# main.py

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

# --- ¡Nuevas importaciones! ---
from database import database 
from routers import productos, categorias, atributos, inventario, sucursales, usuarios, clientes, ventas, auth, corte, descuentos, auditoria, informes
# ... (tu lifespan se queda igual) ...
@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    yield
    await database.disconnect()



# En main.py cambia la línea donde creas la app:

app = FastAPI(lifespan=lifespan, redirect_slashes=False) # <--- Agrega esto
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    print("----- ERROR 422 DETECTADO -----")
    for error in errors:
        # Esto te dirá: qué campo falta, qué tipo se esperaba y qué mandaste
        print(f"Campo: {error.get('loc')}")
        print(f"Mensaje: {error.get('msg')}")
        print(f"Tipo de error: {error.get('type')}")
    print("-------------------------------")
    return JSONResponse(
        status_code=422,
        content={"detail": errors},
    )

# ... (tu middleware se queda igual) ...
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ¡AQUÍ CONECTAS TUS DEPARTAMENTOS! ---
print("Incluyendo routers...")
app.include_router(auth.router)
app.include_router(productos.router)
app.include_router(categorias.router)
app.include_router(atributos.router)
app.include_router(inventario.router)
app.include_router(sucursales.router)
app.include_router(usuarios.router) # <-- AÑADIDO
app.include_router(clientes.router) # <-- AGREGAR
app.include_router(ventas.router)
app.include_router(corte.router)
app.include_router(descuentos.router)
app.include_router(auditoria.router)
app.include_router(informes.router)
print("Routers incluidos. Iniciando app.")