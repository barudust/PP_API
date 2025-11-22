from sqlalchemy import Table, Column, Integer, Text, Numeric, MetaData, ForeignKey, DateTime, Boolean
from sqlalchemy.sql import func

metadata = MetaData()

# === PRODUCTOS Y ATRIBUTOS ===

producto = Table(
    "producto",
    metadata,
    Column("id", Integer, primary_key=True),
    
    # ### NUEVO: Lógica de Negocio ###
    Column("nombre", Text, nullable=False),
    Column("sku", Text, nullable=True), # Para tu código generado (MARCA-ESPECIE...)
    Column("codigo_barras", Text, nullable=True),
    
    # Clasificación
    Column("tipo_producto", Text, nullable=False, server_default="Alimento"), # 'Alimento', 'Accesorio', 'Materia Prima'
    
    # Relaciones (Filtros)
    Column("marca_id", Integer, ForeignKey("marca.id", ondelete="CASCADE")),
    Column("categoria_id", Integer, ForeignKey("categoria.id")),
    Column("subcategoria_id", Integer, ForeignKey("subcategoria.id", ondelete="SET NULL")),
    Column("especie_id", Integer, ForeignKey("especie.id")),
    Column("etapa_id", Integer, ForeignKey("etapa.id")),
    Column("linea_id", Integer, ForeignKey("linea.id")),
    
    # Datos de Venta
    Column("unidad", Text), # Ej: "Bulto 25kg", "Pieza"
    Column("peso_bulto_kg", Integer), # Cuánto pesa el bulto cerrado
    
    # Precios
    Column("precio_unitario", Numeric(10, 2)), # Precio base (o precio por bulto)
    Column("precio_por_kg", Numeric(10, 2)),   # Precio si se vende a granel
    Column("precio_por_bulto", Numeric(10, 2)), # Precio explícito por bulto (opcional, si difiere del unitario)

    # Banderas de Lógica
    Column("se_vende_por_kilo", Boolean, nullable=False, server_default="false"), # Si true, permite fracciones en venta
    Column("activo", Boolean, nullable=False, server_default="true") # Soft-Delete (Suspender en vez de borrar)
)

# --- Tablas de Atributos (Sin cambios mayores) ---
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

# === INVENTARIO Y SUCURSALES ===

sucursal = Table(
    "sucursal",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("nombre", Text, nullable=False, unique=True),
    Column("direccion", Text, nullable=True),
)

inventario = Table(
    "inventario",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("producto_id", Integer, ForeignKey("producto.id", ondelete="CASCADE")),
    Column("sucursal_id", Integer, ForeignKey("sucursal.id", ondelete="CASCADE")),
    
    # ### CAMBIO IMPORTANTE ###
    # Cambiamos Integer a Numeric para soportar Kilos (ej. 24.5 kg)
    Column("cantidad", Numeric(12, 3), nullable=False), 
    
    Column("fecha_actualizacion", DateTime(timezone=True), server_default=func.now(), nullable=False)
)

# === CLIENTES Y DESCUENTOS (NUEVO) ===

cliente = Table(
    "cliente",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("nombre", Text, nullable=False),
    Column("telefono", Text),
    Column("direccion", Text),
    Column("notas", Text) # Para anotar "Amigo del dueño", etc.
)

regla_descuento = Table(
    "regla_descuento",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("descripcion", Text, nullable=False), # Ej: "10% en Marca X"
    Column("descuento_porcentaje", Numeric(5, 2), nullable=False),
    
    # Filtros de la regla (si es NULL, aplica a todos)
    Column("cliente_id", Integer, ForeignKey("cliente.id", ondelete="CASCADE")),
    Column("marca_id", Integer, ForeignKey("marca.id", ondelete="CASCADE")),
    Column("producto_id", Integer, ForeignKey("producto.id", ondelete="CASCADE")),
    
    Column("activo", Boolean, default=True)
)

# === CAJA Y VENTAS ===

usuario = Table(
    "usuario",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("nombre", Text, nullable=False),
    Column("contrasena_hash", Text, nullable=False),
    Column("rol", Text, nullable=False),
    Column("sucursal_id", Integer, ForeignKey("sucursal.id", ondelete="CASCADE"))
)

corte_caja = Table(
    "corte_caja",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("sucursal_id", Integer, ForeignKey("sucursal.id"), nullable=False),
    Column("usuario_id", Integer, ForeignKey("usuario.id"), nullable=False),
    
    Column("fecha_apertura", DateTime(timezone=True), server_default=func.now()),
    Column("fecha_cierre", DateTime(timezone=True), nullable=True),
    
    Column("fondo_inicial", Numeric(10, 2), nullable=False),
    Column("efectivo_final_real", Numeric(10, 2)),
    Column("varianza", Numeric(10, 2)), # Diferencia (Sobró/Faltó)
    Column("comentarios", Text)
)

venta = Table(
    "venta",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("sucursal_id", Integer, ForeignKey("sucursal.id", ondelete="CASCADE")),
    Column("usuario_id", Integer, ForeignKey("usuario.id", ondelete="CASCADE")),
    
    # ### NUEVO ###
    Column("cliente_id", Integer, ForeignKey("cliente.id", ondelete="SET NULL")), # Null = Público General
    Column("corte_caja_id", Integer, ForeignKey("corte_caja.id")), # Relaciona venta con el turno
    
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
    
    # Cambiado a Numeric para soportar venta de 0.5 kg
    Column("cantidad", Numeric(12, 3), nullable=False), 
    Column("precio_unitario", Numeric(10, 2), nullable=False)
)

ingreso_inventario = Table(
    "ingreso_inventario",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("producto_id", Integer, ForeignKey("producto.id", ondelete="CASCADE")),
    Column("sucursal_id", Integer, ForeignKey("sucursal.id", ondelete="CASCADE")),
    # Cambiado a Numeric
    Column("cantidad", Numeric(12, 3), nullable=False),
    Column("usuario_id", Integer, ForeignKey("usuario.id", ondelete="CASCADE")),
    Column("fecha_actualizacion", DateTime(timezone=True), server_default=func.now(), nullable=False)
)