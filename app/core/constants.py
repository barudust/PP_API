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

# --- Tipo de entrega de una venta ---
ENTREGA_TIENDA = "tienda"
ENTREGA_DOMICILIO = "domicilio"
TIPOS_ENTREGA = {ENTREGA_TIENDA, ENTREGA_DOMICILIO}

# --- Listas gráficas (Fase 16) — plantillas Excel replicadas por marca ---
# Nombre de archivo dentro de app/assets/plantillas/ (carpeta no versionada,
# ver PLAN_FASE16.md §6.7) y color de acento de marca (tema de Office del
# .xlsx original) usado para pintar encabezados y exportar fiel al original.
LISTA_PLANTILLA_MARCAS = {
    "Agromas": {"archivo": "Lista Agromas.xlsx", "color": "#ED7D31"},
    "Api-Aba": {"archivo": "Lista Api-Aba.xlsx", "color": "#70AD47"},
}

# --- Importación de catálogo (Fase 11) ---
IMPORT_TIPO_EXCEL = "excel_catalogo"
IMPORT_TIPO_XML = "xml_factura"
IMPORT_TIPO_PDF = "pdf_lista_precios"
IMPORT_TIPOS = {IMPORT_TIPO_EXCEL, IMPORT_TIPO_XML, IMPORT_TIPO_PDF}

IMPORT_ESTADO_REVISION = "revision"
IMPORT_ESTADO_CONFIRMADO = "confirmado"
IMPORT_ESTADO_CANCELADO = "cancelado"
IMPORT_ESTADOS = {IMPORT_ESTADO_REVISION, IMPORT_ESTADO_CONFIRMADO, IMPORT_ESTADO_CANCELADO}

IMPORT_DECISION_PENDIENTE = "pendiente"
IMPORT_DECISION_CREAR = "crear"
IMPORT_DECISION_VINCULAR = "vincular"
IMPORT_DECISION_IGNORAR = "ignorar"
IMPORT_DECISIONES = {
    IMPORT_DECISION_PENDIENTE,
    IMPORT_DECISION_CREAR,
    IMPORT_DECISION_VINCULAR,
    IMPORT_DECISION_IGNORAR,
}

# ==========================================================================
# PERMISOS (RBAC por permisos, asignables a roles)
# ==========================================================================
# Catálogo maestro: (codigo, nombre, grupo). Se sincroniza a la BD al arrancar.
PERMISOS = [
    ("pos.vender",          "Registrar ventas",              "Punto de venta"),
    ("pos.caja",            "Abrir y cerrar caja",           "Punto de venta"),
    ("productos.ver",       "Ver productos",                 "Catálogo"),
    ("productos.gestionar", "Crear y editar productos",      "Catálogo"),
    ("productos.ver_costo", "Ver costo y margen de productos","Catálogo"),
    ("catalogo.importar",   "Importar catálogo (Excel/XML)", "Catálogo"),
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
    ("configuracion.gestionar", "Editar datos del negocio",  "Dirección"),
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
    "productos.ver_costo", "catalogo.importar",
}

PERMISOS_POR_ROL_DEFAULT = {
    ROL_VENDEDOR: _VENDEDOR,
    ROL_GERENTE: _GERENTE,
    ROL_SUPERADMIN: set(TODOS_LOS_PERMISOS),
}

# Orden de presentación de roles en la UI de gestión
ROLES_VALIDOS_LISTA = [ROL_SUPERADMIN, ROL_GERENTE, ROL_VENDEDOR]
