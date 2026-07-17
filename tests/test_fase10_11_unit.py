"""
Pruebas unitarias (sin BD) de la lógica pura de Fase 10 (descuentos, vía
`_especificidad_regla` de ventas.py) y Fase 11 (importación de catálogo).

Antes de esta ronda, ambas fases solo se habían verificado a mano en el
navegador — sin red de pruebas automatizada que avisara si algo se rompía.
Esto cubre las funciones puras (sin `await database...`); el resto (parseo de
Excel/PDF con estilos reales, `confirmar_lote`, `resolver_margen`) requiere la
BD real y sigue verificándose manualmente, como documenta EMPEZAR_AQUI.md.

Ejecutar:  pytest -q
"""
from app.routers.ventas import _especificidad_regla
from app.services.importacion_service import (
    _clave_dedup,
    _normalizar,
    _score,
    buscar_match,
    _resolver_marca_por_nombre,
    _precio_sugerido,
    _clasificar_columna_pdf,
    parsear_xml_cfdi,
)


# --- Fase 10: especificidad de reglas de descuento (producto > marca > cliente) ---

def test_especificidad_regla_general_es_cero():
    assert _especificidad_regla({"producto_id": None, "marca_id": None, "cliente_id": None}) == 0


def test_especificidad_regla_producto_gana_sobre_marca_y_cliente():
    solo_producto = _especificidad_regla({"producto_id": 1, "marca_id": None, "cliente_id": None})
    marca_y_cliente = _especificidad_regla({"producto_id": None, "marca_id": 1, "cliente_id": 1})
    assert solo_producto > marca_y_cliente


def test_especificidad_regla_marca_gana_sobre_cliente():
    solo_marca = _especificidad_regla({"producto_id": None, "marca_id": 1, "cliente_id": None})
    solo_cliente = _especificidad_regla({"producto_id": None, "marca_id": None, "cliente_id": 1})
    assert solo_marca > solo_cliente


def test_especificidad_regla_mas_especifica_es_la_combinada():
    todo = _especificidad_regla({"producto_id": 1, "marca_id": 1, "cliente_id": 1})
    solo_producto = _especificidad_regla({"producto_id": 1, "marca_id": None, "cliente_id": None})
    assert todo > solo_producto


# --- Fase 11: normalización de nombres (dedup vs. fuzzy match) ---

def test_clave_dedup_distingue_presentaciones_por_peso():
    # Mismo producto, dos tamaños de bulto -> NO deben colapsar en un duplicado.
    assert _clave_dedup("Hound Adulto 10 kg") != _clave_dedup("Hound Adulto 4 kg")


def test_clave_dedup_quita_acentos_y_normaliza_espacios():
    assert _clave_dedup("  Alimento   Canino Premium  ") == "alimento canino premium"
    assert _clave_dedup("Ración Perro") == "racion perro"


def test_normalizar_quita_sufijo_de_peso_para_comparar_por_similitud():
    # A diferencia de _clave_dedup, _normalizar SÍ debe igualar dos pesos
    # distintos del mismo nombre (para que el fuzzy match no se confunda).
    assert _normalizar("Croquetas Salmón 20 kg") == _normalizar("Croquetas Salmón 4 kg")


def test_score_texto_identico_es_100():
    assert _score("Gamas Cerdo Inicio 40kg", "Gamas Cerdo Inicio 40kg") == 100.0


def test_score_ignora_diferencia_de_peso():
    # Incluso con pesos distintos, el score debe ser alto (el sufijo se quita).
    assert _score("Gamas Cerdo Inicio 40kg", "Gamas Cerdo Inicio 25kg") == 100.0


# --- Fase 11: buscar_match (sugerencia de producto existente) ---

def _candidatos():
    return [
        {"id": 1, "nombre": "MAS CARNE 12% ESENCIAL 25 kg"},
        {"id": 2, "nombre": "BORREGO ESENCIAL 25 kg"},
        {"id": 3, "nombre": "Croquetas Prueba 20kg"},
    ]


def test_buscar_match_encuentra_el_correcto():
    match_id, score = buscar_match("MAS CARNE 12% ESENCIAL 25 KG", _candidatos())
    assert match_id == 1
    assert score is not None and score >= 90


def test_buscar_match_nombre_distinto_de_peso_igual_no_confunde_candidatos():
    match_id, score = buscar_match("BORREGO ESENCIAL 25 kg", _candidatos())
    assert match_id == 2


def test_buscar_match_sin_candidato_similar_devuelve_none():
    match_id, score = buscar_match("Shampoo Antipulgas 500ml", _candidatos())
    assert match_id is None


# --- Fase 11: resolución de marca por nombre (hint de hoja/proveedor) ---

def _marcas():
    return [
        {"id": 1, "nombre": "Agromas"},
        {"id": 2, "nombre": "Api-Aba"},
        {"id": 3, "nombre": "PetFood MX"},
    ]


def test_resolver_marca_exacta():
    assert _resolver_marca_por_nombre("Agromas", _marcas()) == 1


def test_resolver_marca_por_similitud_alta():
    # El hint de hoja/proveedor puede venir con variaciones menores.
    assert _resolver_marca_por_nombre("AGROMAS", _marcas()) == 1


def test_resolver_marca_sin_hint_es_none():
    assert _resolver_marca_por_nombre(None, _marcas()) is None


def test_resolver_marca_sin_similitud_suficiente_es_none():
    assert _resolver_marca_por_nombre("Proveedor Totalmente Distinto SA", _marcas()) is None


# --- Fase 11: cálculo de precio sugerido (costo + margen) ---

def test_precio_sugerido_aplica_margen_porcentual():
    assert _precio_sugerido(costo=100, margen=20) == 120.0


def test_precio_sugerido_admite_margen_negativo():
    assert _precio_sugerido(costo=100, margen=-10) == 90.0


def test_precio_sugerido_sin_costo_o_sin_margen_es_none():
    assert _precio_sugerido(costo=None, margen=20) is None
    assert _precio_sugerido(costo=100, margen=None) is None


# --- Fase 11: clasificación de columnas de PDF (encabezados partidos) ---

def test_clasificar_columna_pdf_descripcion_es_nombre():
    assert _clasificar_columna_pdf("nueva descripcion") == "nombre"


def test_clasificar_columna_pdf_item_es_codigo_proveedor():
    assert _clasificar_columna_pdf("item") == "codigo_proveedor"


def test_clasificar_columna_pdf_tonelada_se_ignora():
    # Precio por tonelada es redundante/derivado — no se usa como columna.
    assert _clasificar_columna_pdf("precio tonelada") is None


def test_clasificar_columna_pdf_saco_con_kg_es_contenido_neto():
    assert _clasificar_columna_pdf("kg x saco") == "contenido_neto"


def test_clasificar_columna_pdf_precio_es_costo():
    assert _clasificar_columna_pdf("precio") == "precio_costo"


def test_clasificar_columna_pdf_desconocida_es_none():
    assert _clasificar_columna_pdf("observaciones") is None


# --- Fase 11: parseo de CFDI (costo real con descuento aplicado) ---

_CFDI_EJEMPLO = """<?xml version="1.0" encoding="UTF-8"?>
<cfdi:Comprobante xmlns:cfdi="http://www.sat.gob.mx/cfd/4">
  <cfdi:Emisor Nombre="PRODUCTOS AGROINDUSTRIALES AZTECA"/>
  <cfdi:Conceptos>
    <cfdi:Concepto Descripcion="MAS CARNE 12% ESENCIAL 25 kg" Cantidad="10"
      ValorUnitario="180" Importe="1800" Descuento="120"
      ClaveProdServ="10101500" NoIdentificacion="COD-1"/>
    <cfdi:Concepto Descripcion="PORCIMAS" Cantidad="5"
      ValorUnitario="200" Importe="1000" Descuento="0"
      ClaveProdServ="10101501" NoIdentificacion="COD-2"/>
  </cfdi:Conceptos>
</cfdi:Comprobante>"""


def test_parsear_xml_cfdi_extrae_proveedor_y_lineas():
    resultado = parsear_xml_cfdi(_CFDI_EJEMPLO.encode("utf-8"))
    assert resultado["proveedor"] == "PRODUCTOS AGROINDUSTRIALES AZTECA"
    assert len(resultado["lineas"]) == 2


def test_parsear_xml_cfdi_costo_unitario_resta_el_descuento():
    # (Importe - Descuento) / Cantidad = (1800 - 120) / 10 = 168.0
    resultado = parsear_xml_cfdi(_CFDI_EJEMPLO.encode("utf-8"))
    linea = resultado["lineas"][0]
    assert linea["nombre_original"] == "MAS CARNE 12% ESENCIAL 25 kg"
    assert linea["cantidad"] == 10.0
    assert linea["precio_costo"] == 168.0
    assert linea["codigo_sat"] == "10101500"
    assert linea["codigo_proveedor"] == "COD-1"


def test_parsear_xml_cfdi_sin_descuento_usa_el_importe_completo():
    resultado = parsear_xml_cfdi(_CFDI_EJEMPLO.encode("utf-8"))
    linea = resultado["lineas"][1]
    assert linea["precio_costo"] == 200.0
