"""
Servicios de auditoría física: tolerancia de fábrica y sugerencia de tipo.

Funciones puras (sin BD) para poder probarlas en aislamiento.
"""
from app.core.constants import VARIACION_FABRICA, MERMA_OPERATIVA, ERROR_SISTEMA


def analizar_tolerancia(
    contenido_neto: float,
    cantidad_sistema: float,
    diferencia: float,
    tolerancia_bajo: float,
    tolerancia_alto: float,
):
    """
    Calcula la tolerancia de variación de fábrica (ASIMÉTRICA) y sugiere el tipo.

    La variación depende de la empresa/marca: algunos empaques llegan con hasta
    `tolerancia_bajo` kg de menos y otros con hasta `tolerancia_alto` kg de más,
    por cada bulto. Los límites totales escalan con el nº de empaques en sistema.

    - Si la diferencia cae en [-límite_bajo, +límite_alto] → VARIACION_FABRICA
      (no se penaliza al empleado).
    - Si falta producto fuera de tolerancia → MERMA_OPERATIVA.
    - Si sobra producto fuera de tolerancia → ERROR_SISTEMA.

    Devuelve: (limite_bajo, limite_alto, dentro_de_tolerancia, tipo_sugerido)
    """
    contenido = float(contenido_neto or 1)
    num_empaques = abs(cantidad_sistema) / contenido if contenido > 0 else 0

    limite_bajo = round(num_empaques * float(tolerancia_bajo or 0), 3)   # puede FALTAR
    limite_alto = round(num_empaques * float(tolerancia_alto or 0), 3)   # puede SOBRAR

    tiene_tolerancia = limite_bajo > 0 or limite_alto > 0
    dentro = tiene_tolerancia and (-limite_bajo <= diferencia <= limite_alto)

    if dentro:
        tipo_sugerido = VARIACION_FABRICA
    elif diferencia < 0:
        tipo_sugerido = MERMA_OPERATIVA
    else:
        tipo_sugerido = ERROR_SISTEMA

    return limite_bajo, limite_alto, dentro, tipo_sugerido
