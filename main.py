# main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# --- ¡Nuevas importaciones! ---
from database import database 
from routers import productos, categorias, atributos, inventario, sucursales, usuarios, clientes, ventas, auth, corte, descuentos, auditoria, informes
# ... (tu lifespan se queda igual) ...
@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    yield
    await database.disconnect()

app = FastAPI(lifespan=lifespan)

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