from sqlalchemy import Table, Column, Integer, Text, Numeric, MetaData, ForeignKey, DateTime, Boolean
from sqlalchemy.sql import func

metadata = MetaData()

# ==========================================
# 1. ATRIBUTOS (Catálogos Simples)
# ==========================================

categoria = Table(
    "categoria",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("nombre", Text, nullable=False, unique=True)
)

subcategoria = Table(
    "subcategoria",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("nombre", Text, nullable=False),
    Column("categoria_id", Integer, ForeignKey("categoria.id", ondelete="CASCADE")),
)

marca = Table(
    "marca",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("nombre", Text, nullable=False, unique=True)
)

especie = Table(
    "especie",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("nombre", Text, nullable=False, unique=True)
)

etapa = Table(
    "etapa",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("nombre", Text, nullable=False, unique=True)
)

linea = Table(
    "linea",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("nombre", Text, nullable=False, unique=True)
)

linea_marca = Table(
    "linea_marca",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("linea_id", Integer, ForeignKey("linea.id", ondelete="CASCADE")),
    Column("marca_id", Integer, ForeignKey("marca.id", ondelete="CASCADE")),
    Column("nombre_publico", Text, nullable=False),
)

# ==========================================
# 2. UBICACIONES Y USUARIOS
# ==========================================

sucursal = Table(
    "sucursal",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("nombre", Text, nullable=False, unique=True),
    Column("direccion", Text, nullable=True),
)

usuario = Table(
    "usuario",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("nombre", Text, nullable=False),
    Column("contrasena_hash", Text, nullable=False),
    Column("rol", Text, nullable=False),
    Column("sucursal_id", Integer, ForeignKey("sucursal.id", ondelete="CASCADE"))
)

cliente = Table(
    "cliente",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("nombre", Text, nullable=False),
    Column("telefono", Text),
    Column("direccion", Text),
    Column("notas", Text) # "Amigo del dueño", "Cliente Frecuente", etc.
)

# ==========================================
# 3. PRODUCTO (El Núcleo)
# ==========================================

producto = Table(
    "producto",
    metadata,
    Column("id", Integer, primary_key=True),
    
    # Identificación
    Column("nombre", Text, nullable=False),
    Column("tipo_producto", Text, nullable=False, server_default="Alimento"), 

    Column("sku", Text, unique=True, nullable=True), 
    Column("codigo_barras", Text, nullable=True),
    Column("descripcion", Text, nullable=True),
    
    # Clasificación (Para tus filtros dinámicos)
    
    # Filtros (Nullables para flexibilidad)
    Column("marca_id", Integer, ForeignKey("marca.id")),
    Column("categoria_id", Integer, ForeignKey("categoria.id")),
    Column("subcategoria_id", Integer, ForeignKey("subcategoria.id")),
    Column("especie_id", Integer, ForeignKey("especie.id")),
    Column("etapa_id", Integer, ForeignKey("etapa.id")),
    Column("linea_id", Integer, ForeignKey("linea.id")),
    
    # Lógica de Peso y Venta
    Column("unidad_medida", Text, nullable=False, server_default='pza'), # 'Bulto', 'Bote', 'Pieza'
    Column("contenido_neto", Numeric(10, 3), nullable=False, server_default='1.0'), # Cuánto trae el empaque (ej. 25.000)
    Column("se_vende_a_granel", Boolean, nullable=False, server_default='false'), # ¿Se puede romper el empaque?

    # Precios Diferenciados
    Column("precio_base", Numeric(10, 2), nullable=False),   # Precio del paquete cerrado (Bulto/Pieza)
    Column("precio_granel", Numeric(10, 2), nullable=True),  # Precio por unidad suelta (Kilo/Tableta)
    
    Column("activo", Boolean, default=True) # Soft Delete
)

# ==========================================
# 4. INVENTARIO Y MOVIMIENTOS
# ==========================================

inventario = Table(
    "inventario",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("producto_id", Integer, ForeignKey("producto.id", ondelete="CASCADE")),
    Column("sucursal_id", Integer, ForeignKey("sucursal.id", ondelete="CASCADE")),
    
    # Cantidad siempre en la unidad más pequeña (Kilos o Piezas sueltas)
    # Numeric(12, 3) permite hasta 999 millones y 3 decimales (gramos)
    Column("cantidad", Numeric(12, 3), nullable=False, default=0), 
    
    Column("fecha_actualizacion", DateTime(timezone=True), server_default=func.now(), nullable=False)
)

# Registro de Compras/Ingresos
ingreso_inventario = Table(
    "ingreso_inventario",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("producto_id", Integer, ForeignKey("producto.id", ondelete="CASCADE")),
    Column("sucursal_id", Integer, ForeignKey("sucursal.id", ondelete="CASCADE")),
    Column("cantidad", Numeric(12, 3), nullable=False), # Numeric para kilos
    Column("usuario_id", Integer, ForeignKey("usuario.id", ondelete="CASCADE")),
    Column("fecha_actualizacion", DateTime(timezone=True), server_default=func.now(), nullable=False)
)

# Auditoría (Cuando pesas los botes para corregir inventario)
ajuste_inventario = Table(
    "ajuste_inventario",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("sucursal_id", Integer, ForeignKey("sucursal.id")),
    Column("usuario_id", Integer, ForeignKey("usuario.id")),
    Column("producto_id", Integer, ForeignKey("producto.id")),
    
    Column("fecha", DateTime(timezone=True), server_default=func.now()),
    
    # La evidencia
    Column("cantidad_sistema", Numeric(12, 3), nullable=False), # Lo que decía el software
    Column("cantidad_fisica", Numeric(12, 3), nullable=False),  # Lo que pesaste real
    Column("diferencia", Numeric(12, 3), nullable=False),       # La resta (Merma/Ganancia)
    Column("motivo", Text) 
)

# El "Chismoso" (Bitácora completa de movimientos)
historial_inventario = Table(
    "historial_inventario",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("fecha", DateTime(timezone=True), server_default=func.now()),
    
    Column("sucursal_id", Integer, ForeignKey("sucursal.id"), nullable=False),
    Column("usuario_id", Integer, ForeignKey("usuario.id"), nullable=False),
    Column("producto_id", Integer, ForeignKey("producto.id"), nullable=False),
    
    Column("tipo_movimiento", Text, nullable=False), # 'VENTA', 'COMPRA', 'AJUSTE', 'CORRECCION'
    
    Column("cantidad_anterior", Numeric(12, 3), nullable=False),
    Column("cantidad_movida", Numeric(12, 3), nullable=False), 
    Column("cantidad_nueva", Numeric(12, 3), nullable=False),
    
    Column("motivo", Text)
)

# ==========================================
# 5. VENTAS Y CAJA
# ==========================================

corte_caja = Table(
    "corte_caja",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("sucursal_id", Integer, ForeignKey("sucursal.id"), nullable=False),
    Column("usuario_id", Integer, ForeignKey("usuario.id"), nullable=False),
    
    Column("fecha_apertura", DateTime(timezone=True), server_default=func.now()),
    Column("fecha_cierre", DateTime(timezone=True), nullable=True),
    
    # Dinero
    Column("fondo_inicial", Numeric(10, 2), nullable=False), # El cambio
    Column("ventas_totales", Numeric(10, 2), default=0),     # Ventas sistema
    Column("efectivo_esperado", Numeric(10, 2)),             # Fondo + Ventas
    Column("efectivo_real", Numeric(10, 2)),                 # Lo contado
    Column("diferencia", Numeric(10, 2)),                    # Sobrante/Faltante
    
    # Retiro
    Column("monto_retirado", Numeric(10, 2), default=0),     # Tu ganancia
    Column("fondo_siguiente", Numeric(10, 2), default=0),    # Para mañana
    
    Column("comentarios", Text)
)

regla_descuento = Table(
    "regla_descuento",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("descripcion", Text, nullable=False), 
    Column("descuento_porcentaje", Numeric(5, 2), nullable=False),
    
    # Filtros de la regla
    Column("cliente_id", Integer, ForeignKey("cliente.id", ondelete="CASCADE")),
    Column("marca_id", Integer, ForeignKey("marca.id", ondelete="CASCADE")),
    Column("producto_id", Integer, ForeignKey("producto.id", ondelete="CASCADE")),
    
    Column("activo", Boolean, default=True)
)

venta = Table(
    "venta",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("sucursal_id", Integer, ForeignKey("sucursal.id", ondelete="CASCADE")),
    Column("usuario_id", Integer, ForeignKey("usuario.id", ondelete="CASCADE")),
    
    Column("cliente_id", Integer, ForeignKey("cliente.id", ondelete="SET NULL")), 
    Column("corte_caja_id", Integer, ForeignKey("corte_caja.id")), 
    
    Column("fecha", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("total", Numeric(10, 2), nullable=False),
    
    # Descuentos manuales
    Column("descuento_especial_monto", Numeric(10, 2), default=0),
    Column("descuento_especial_motivo", Text)
)

venta_detalle = Table(
    "venta_detalle",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("venta_id", Integer, ForeignKey("venta.id", ondelete="CASCADE")),
    Column("producto_id", Integer, ForeignKey("producto.id", ondelete="CASCADE")),
    
    # Numeric para soportar 0.5 kg
    Column("cantidad", Numeric(12, 3), nullable=False), 
    Column("precio_unitario", Numeric(10, 2), nullable=False)
)