"""
Pruebas unitarias (sin BD) de la lógica de negocio pura.

Ejecutar:  pytest -q
"""
import asyncio

from app.services.auditoria_service import analizar_tolerancia
from app.core.constants import VARIACION_FABRICA, MERMA_OPERATIVA, ERROR_SISTEMA
from app.core.dependencies import require_roles, ROL_VENDEDOR, ROL_GERENTE, ROL_SUPERADMIN


# --- Tolerancia de fábrica (asimétrica) ---

def test_diferencia_dentro_de_tolerancia_sugiere_variacion_fabrica():
    # 315kg en bultos de 40kg -> 7.875 bultos * 0.25 = 1.969 de tolerancia por lado
    bajo, alto, dentro, tipo = analizar_tolerancia(
        contenido_neto=40, cantidad_sistema=315, diferencia=-0.2,
        tolerancia_bajo=0.25, tolerancia_alto=0.25,
    )
    assert dentro is True
    assert tipo == VARIACION_FABRICA
    assert abs(bajo - 1.969) < 0.001 and abs(alto - 1.969) < 0.001


def test_faltante_fuera_de_tolerancia_es_merma():
    _, _, dentro, tipo = analizar_tolerancia(
        contenido_neto=40, cantidad_sistema=315, diferencia=-10,
        tolerancia_bajo=0.25, tolerancia_alto=0.25,
    )
    assert dentro is False
    assert tipo == MERMA_OPERATIVA


def test_sobrante_fuera_de_tolerancia_es_error_sistema():
    _, _, dentro, tipo = analizar_tolerancia(
        contenido_neto=40, cantidad_sistema=315, diferencia=10,
        tolerancia_bajo=0.25, tolerancia_alto=0.25,
    )
    assert dentro is False
    assert tipo == ERROR_SISTEMA


def test_sin_tolerancia_definida_nunca_esta_dentro():
    bajo, alto, dentro, tipo = analizar_tolerancia(
        contenido_neto=40, cantidad_sistema=315, diferencia=-0.2,
        tolerancia_bajo=0, tolerancia_alto=0,
    )
    assert bajo == 0 and alto == 0
    assert dentro is False
    assert tipo == MERMA_OPERATIVA


def test_tolerancia_asimetrica_por_marca():
    # Empresa cuyos bultos SOLO llegan cortos (bajo=0.5, alto=0).
    # Un faltante pequeño es variación de fábrica...
    _, _, dentro, tipo = analizar_tolerancia(
        contenido_neto=40, cantidad_sistema=200, diferencia=-0.4,
        tolerancia_bajo=0.5, tolerancia_alto=0,
    )
    assert dentro is True and tipo == VARIACION_FABRICA
    # ...pero un sobrante NO (esa marca nunca trae de más) -> error de sistema.
    _, _, dentro2, tipo2 = analizar_tolerancia(
        contenido_neto=40, cantidad_sistema=200, diferencia=0.4,
        tolerancia_bajo=0.5, tolerancia_alto=0,
    )
    assert dentro2 is False and tipo2 == ERROR_SISTEMA


# --- RBAC: require_roles ---

def _run_checker(rol, *roles_permitidos):
    checker = require_roles(*roles_permitidos)
    return asyncio.run(checker(actual={"rol": rol}))


def test_superadmin_pasa_cualquier_restriccion():
    # Aunque el endpoint pida gerente, el superadmin siempre pasa.
    res = _run_checker(ROL_SUPERADMIN, ROL_GERENTE)
    assert res["rol"] == ROL_SUPERADMIN


def test_rol_correcto_pasa():
    res = _run_checker(ROL_GERENTE, ROL_GERENTE)
    assert res["rol"] == ROL_GERENTE


def test_rol_insuficiente_es_403():
    import pytest
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        _run_checker(ROL_VENDEDOR, ROL_GERENTE)
    assert exc.value.status_code == 403
