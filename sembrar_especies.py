"""Siembra el catálogo base de especies (Fase 15, §2.3 de PLAN_FASE15.md).

Idempotente: no duplica una especie que ya exista (compara por nombre).
Uso: con la API corriendo en http://127.0.0.1:8000, `python sembrar_especies.py`.
"""
import sys
import requests

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE_URL = "http://127.0.0.1:8000"

ESPECIES = [
    "Cerdo",
    "Pollo",
    "Pavo",
    "Ganado de engorda",
    "Ganado lechero",
    "Ave de postura",
    "Gallo",
    "Ovino",
    "Conejo",
]


def main():
    existentes = {e["nombre"]: e["id"] for e in requests.get(f"{BASE_URL}/especies/").json()}

    for nombre in ESPECIES:
        if nombre in existentes:
            print(f"⚠️ Ya existe: {nombre} (ID: {existentes[nombre]})")
            continue
        r = requests.post(f"{BASE_URL}/especies/", json={"nombre": nombre})
        r.raise_for_status()
        print(f"✅ CREAR OK: {nombre} (ID: {r.json()['id']})")


if __name__ == "__main__":
    main()
