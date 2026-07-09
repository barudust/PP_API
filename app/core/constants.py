# constants.py
"""Constantes de dominio compartidas."""

# --- Tipos de ajuste de inventario (auditoría física) ---
MERMA_OPERATIVA = "MERMA_OPERATIVA"      # Se tiró/dañó producto en la operación
VARIACION_FABRICA = "VARIACION_FABRICA"  # Los bultos traían de más/menos (±g)
ERROR_SISTEMA = "ERROR_SISTEMA"          # Captura errónea / descuadre de sistema
CADUCIDAD = "CADUCIDAD"                   # Producto caducado retirado

TIPOS_AJUSTE = {
    MERMA_OPERATIVA,
    VARIACION_FABRICA,
    ERROR_SISTEMA,
    CADUCIDAD,
}

# --- Tipos de movimiento en el historial ---
MOV_VENTA = "VENTA"
MOV_COMPRA = "COMPRA"
MOV_AJUSTE = "AJUSTE_AUDITORIA"
MOV_CANCELACION = "CANCELACION_VENTA"

# ==========================================================================
# PERMISOS (RBAC por permisos, asignables a roles)
# ==========================================================================
# Catálogo maestro: (codigo, nombre, grupo). Se sincroniza a la BD al arrancar.
PERMISOS = [
    ("pos.vender",          "Registrar ventas",              "Punto de venta"),
    ("pos.caja",            "Abrir y cerrar caja",           "Punto de venta"),
    ("productos.ver",       "Ver productos",                 "Catálogo"),
    ("productos.gestionar", "Crear y editar productos",      "Catálogo"),
    ("inventario.ver",      "Ver inventario",                "Inventario"),
    ("inventario.surtir",   "Surtir / ingresar mercancía",   "Inventario"),
    ("auditoria.contar",    "Hacer conteo físico",           "Auditoría"),
    ("auditoria.ajustar",   "Registrar ajustes",             "Auditoría"),
    ("ventas.ver",          "Ver ventas",                    "Ventas"),
    ("ventas.cancelar",     "Cancelar ventas",               "Ventas"),
    ("clientes.ver",        "Ver clientes",                  "Clientes"),
    ("clientes.gestionar",  "Crear y editar clientes",       "Clientes"),
    ("descuentos.gestionar","Gestionar descuentos",          "Ventas"),
    ("reportes.ver",        "Ver reportes",                  "Reportes"),
    ("dashboard.ver",       "Ver dashboard global",          "Dirección"),
    ("sucursales.gestionar","Gestionar sucursales",          "Dirección"),
    ("usuarios.gestionar",  "Gestionar usuarios",            "Dirección"),
    ("roles.gestionar",     "Gestionar roles y permisos",    "Dirección"),
]

TODOS_LOS_PERMISOS = [p[0] for p in PERMISOS]

# Roles canónicos (mismos strings que usa `usuario.rol`)
ROL_VENDEDOR = "vendedor"
ROL_GERENTE = "gerente"
ROL_SUPERADMIN = "superadmin"

# Permisos por defecto de cada rol (superadmin obtiene TODOS de forma implícita).
_VENDEDOR = {
    "pos.vender", "pos.caja",
    "productos.ver", "inventario.ver",
    "clientes.ver", "clientes.gestionar",
}
_GERENTE = _VENDEDOR | {
    "inventario.surtir",
    "auditoria.contar", "auditoria.ajustar",
    "ventas.ver", "ventas.cancelar",
    "productos.gestionar", "descuentos.gestionar",
    "reportes.ver", "dashboard.ver",
}

PERMISOS_POR_ROL_DEFAULT = {
    ROL_VENDEDOR: _VENDEDOR,
    ROL_GERENTE: _GERENTE,
    ROL_SUPERADMIN: set(TODOS_LOS_PERMISOS),
}

# Orden de presentación de roles en la UI de gestión
ROLES_VALIDOS_LISTA = [ROL_SUPERADMIN, ROL_GERENTE, ROL_VENDEDOR]
