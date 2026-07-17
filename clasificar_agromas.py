"""Clasifica por especie/categoría los productos reales de Agromas ya
confirmados en el catálogo (Fase 15, §2.4/§2.5 de PLAN_FASE15.md).

Clasificación automática por palabra clave en el nombre, SIN pedir
confirmación línea por línea (decisión ya tomada con el dueño). Los
productos ambiguos se dejan sin especie/categoría a propósito, para que el
dueño los revise después.

Idempotente: vuelve a aplicar el mismo mapeo si se corre de nuevo (no
duplica categorías, usa PATCH sobre el producto).

Uso: con la API corriendo en http://127.0.0.1:8000 y sesión de SuperAdmin
disponible, `python clasificar_agromas.py`.
"""
import sys
import requests

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE_URL = "http://127.0.0.1:8000"
SUPERADMIN_USER = "Admin"
SUPERADMIN_PASS = "admin123"

MARCA_AGROMAS_ID = 3

# nombre exacto del producto -> (especie, categoria|None)
# Los 3 nombres ambiguos (AGROMIX MIGAJA CC, ESPUELA DE ORO MP,
# INVENCIBLE 26 INICIO) no aparecen aquí a propósito: quedan sin
# especie/categoría para revisión posterior del dueño.
CLASIFICACION = {
    "CERDO SUPREMA CRECIMIENTO 25KG": ("Cerdo", "Suprema"),
    "PAVO INICIO 25 KG": ("Pavo", None),
    "CERDO OPTIMA CRECIMIENTO 25 kg": ("Cerdo", "Óptima"),
    "CERDO SUPREMA LACTANCIA 25 kg": ("Cerdo", "Suprema"),
    "BOVIMAS LECHERO SUPREMA 20 25 kg": ("Ganado lechero", "Suprema"),
    "PONEDORA SUPER YEMA 25 kg": ("Ave de postura", "Súper Yema"),
    "POLLO INICIO 25 kg": ("Pollo", None),
    "POLLAS DESARROLLO 25 kg": ("Pollo", None),
    "POLLO ENGORDA CP -5KGS": ("Pollo", "CP"),
    "POLLO ENGORDA CP 25 kg": ("Pollo", "CP"),
    "CERDO SUPREMA FINALIZADOR R-10 ppm": ("Cerdo", "Suprema"),
    "PORCIMAS 25 kg": ("Cerdo", "Porcimas"),
    "BOVIMAS ENGORDA OPTIMA 15 MP 25 kg": ("Ganado de engorda", "Óptima"),
    "CERDO SUPREMA INICIO 25 kg": ("Cerdo", "Suprema"),
    "GALLO REGIO 25 kg": ("Gallo", "Regio"),
    "MAS LECHON PRE-INICIADOR 3": ("Cerdo", "Más Lechón"),
    "MAS LECHON PRE-INICIADOR 1": ("Cerdo", "Más Lechón"),
    "POLLO INICIO - 5 KGS": ("Pollo", None),
}


def login():
    r = requests.post(
        f"{BASE_URL}/token",
        data={"username": SUPERADMIN_USER, "password": SUPERADMIN_PASS},
    )
    r.raise_for_status()
    token = r.json()["access_token"]
    print("🔑 Sesión iniciada como SuperAdmin.")
    return {"Authorization": f"Bearer {token}"}


def obtener_o_crear_categoria(nombre, cache, headers):
    if nombre in cache:
        return cache[nombre]
    existentes = requests.get(f"{BASE_URL}/categorias/").json()
    for c in existentes:
        if c["nombre"] == nombre:
            cache[nombre] = c["id"]
            return c["id"]
    r = requests.post(f"{BASE_URL}/categorias/", json={"nombre": nombre}, headers=headers)
    r.raise_for_status()
    cid = r.json()["id"]
    cache[nombre] = cid
    print(f"✅ Categoría creada: {nombre} (ID: {cid})")
    return cid


def main():
    headers = login()
    especies = {e["nombre"]: e["id"] for e in requests.get(f"{BASE_URL}/especies/").json()}
    cache_categorias = {}

    productos = requests.get(f"{BASE_URL}/productos/?marca_id={MARCA_AGROMAS_ID}").json()
    print(f"📦 {len(productos)} productos de Agromas encontrados.")

    clasificados, ambiguos = 0, 0
    for p in productos:
        nombre = p["nombre"]
        if nombre not in CLASIFICACION:
            print(f"⚠️ Sin clasificar (ambiguo, revisión del dueño): {nombre} (ID: {p['id']})")
            ambiguos += 1
            continue

        especie_nombre, categoria_nombre = CLASIFICACION[nombre]
        especie_id = especies.get(especie_nombre)
        if especie_id is None:
            print(f"❌ Especie '{especie_nombre}' no existe — corre sembrar_especies.py primero.")
            continue

        payload = {"especie_id": especie_id}
        if categoria_nombre:
            payload["categoria_id"] = obtener_o_crear_categoria(categoria_nombre, cache_categorias, headers)

        r = requests.patch(f"{BASE_URL}/productos/{p['id']}/", json=payload, headers=headers)
        r.raise_for_status()
        cat_txt = f", categoría {categoria_nombre}" if categoria_nombre else ""
        print(f"✅ {nombre} (ID: {p['id']}) → especie {especie_nombre}{cat_txt}")
        clasificados += 1

    print(f"\nResumen: {clasificados} clasificados, {ambiguos} dejados para revisión del dueño.")


if __name__ == "__main__":
    main()
