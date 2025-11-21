from sqlalchemy import Table, Column, Integer, Text, Numeric, MetaData, ForeignKey, Date, DateTime,  func
from datetime import datetime, timezone
from sqlalchemy import UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy import MetaData
fecha_actualizacion = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
metadata = MetaData()

producto = Table(
    "producto",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("nombre", Text, nullable=False),
    Column("marca_id", Integer, ForeignKey("marca.id", ondelete="CASCADE")),
    Column("categoria_id", Integer, ForeignKey("categoria.id")),
    Column("subcategoria_id", Integer, ForeignKey("subcategoria.id", ondelete="SET NULL")),
    Column("especie_id", Integer, ForeignKey("especie.id")),
    Column("etapa_id", Integer, ForeignKey("etapa.id")),
    Column("linea_id", Integer, ForeignKey("linea.id")),
    Column("unidad", Text),
    Column("peso_bulto_kg", Integer),
    Column("precio_unitario", Numeric(10, 2)),
)


categoria = Table(
    "categoria",
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

marca = Table(
    "marca",
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
    UniqueConstraint("nombre", "categoria_id", name="subcategoria_nombre_categoria_id_key")
)

linea_marca = Table(
    "linea_marca",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("linea_id", Integer, ForeignKey("linea.id", ondelete="CASCADE")),
    Column("marca_id", Integer, ForeignKey("marca.id", ondelete="CASCADE")),
    Column("nombre_publico", Text, nullable=False),
    UniqueConstraint("marca_id", "nombre_publico", name="linea_marca_marca_id_nombre_publico_key")
)


inventario = Table(
    "inventario",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("producto_id", Integer, ForeignKey("producto.id", ondelete="CASCADE")),
    Column("sucursal_id", Integer, ForeignKey("sucursal.id", ondelete="CASCADE")),
    Column("cantidad", Integer, nullable=False),
    Column("fecha_actualizacion", DateTime(timezone=True), server_default=func.now(), nullable=False)
)

sucursal = Table(
    "sucursal",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("nombre", Text, nullable=False, unique=True),
    Column("direccion", Text, nullable=True),
)

ingreso_inventario = Table(
    "ingreso_inventario",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("producto_id", Integer, ForeignKey("producto.id", ondelete="CASCADE")),
    Column("sucursal_id", Integer, ForeignKey("sucursal.id", ondelete="CASCADE")),
    Column("cantidad", Integer, nullable=False),
    Column("usuario_id", Integer, ForeignKey("usuario.id", ondelete="CASCADE")),
    Column("fecha_actualizacion", DateTime(timezone=True), server_default=func.now(), nullable=False)
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


venta = Table(
    "venta",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("sucursal_id", Integer, ForeignKey("sucursal.id", ondelete="CASCADE")),
    Column("usuario_id", Integer, ForeignKey("usuario.id", ondelete="CASCADE")),
    Column("fecha", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("total", Numeric(10, 2), nullable=False)
)


venta_detalle = Table(
    "venta_detalle",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("venta_id", Integer, ForeignKey("venta.id", ondelete="CASCADE")),
    Column("producto_id", Integer, ForeignKey("producto.id", ondelete="CASCADE")),
    Column("cantidad", Integer, nullable=False),
    Column("precio_unitario", Numeric(10, 2), nullable=False)
)

