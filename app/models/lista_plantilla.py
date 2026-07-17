"""Estructura editable de las plantillas gráficas de Listas (Fase 16) —
reproduce el layout de dos paneles de Lista Agromas.xlsx / Lista Api-Aba.xlsx
como filas ordenadas, ver PLAN_FASE16.md §4.1/§4.2."""
from sqlalchemy import Table, Column, Integer, Text, ForeignKey, CheckConstraint

from .base import metadata

lista_plantilla_fila = Table(
    "lista_plantilla_fila",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("marca_id", Integer, ForeignKey("marca.id", ondelete="CASCADE"), nullable=False),
    # Nombre de la hoja de origen ('Hoja1', 'Hoja2', 'Vimifos'...) — una marca
    # con una sola lista usa siempre el mismo valor (ej. 'Hoja1').
    Column("hoja", Text, nullable=False, server_default="Hoja1"),
    Column("panel", Text, nullable=False),  # 'izq' | 'der'
    Column("orden", Integer, nullable=False),  # posición dentro de marca+hoja+panel
    Column("tipo", Text, nullable=False),  # 'encabezado' | 'producto'
    # Solo para 'encabezado': profundidad del esquema (1 = más importante).
    # El color de fondo al renderizar se deriva de este número (tinte
    # creciente del color de marca), no hay un catálogo fijo de "sección"/
    # "línea" — soporta la profundidad que traiga cada plantilla.
    Column("nivel", Integer, nullable=True),
    # Para 'encabezado': el texto del encabezado. Para 'producto': el nombre
    # tal como aparece en la plantilla (se conserva aunque haya vínculo, para
    # poder re-resolver el match si el producto cambia de nombre).
    Column("texto", Text, nullable=False),
    # Vínculo resuelto a un producto real del catálogo — NULL = celda de
    # precio vacía (no hay match o el producto no tiene precio).
    Column("producto_id", Integer, ForeignKey("producto.id", ondelete="SET NULL"), nullable=True),
    CheckConstraint("panel IN ('izq','der')", name="ck_lista_plantilla_fila_panel"),
    CheckConstraint("tipo IN ('encabezado','producto')", name="ck_lista_plantilla_fila_tipo"),
)
