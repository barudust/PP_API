import sys
import requests

# La consola de Windows usa cp1252 por defecto y truena con emojis.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE_URL = "http://127.0.0.1:8000"

# Credenciales del SuperAdmin creado con `python crear_superadmin.py`
SUPERADMIN_USER = "Admin"
SUPERADMIN_PASS = "admin123"


def login():
    """Inicia sesión y devuelve los headers con el token Bearer."""
    try:
        r = requests.post(
            f"{BASE_URL}/token",
            data={"username": SUPERADMIN_USER, "password": SUPERADMIN_PASS},
        )
        r.raise_for_status()
        token = r.json()["access_token"]
        print("🔑 Sesión iniciada como SuperAdmin.")
        return {"Authorization": f"Bearer {token}"}
    except Exception as e:
        print(f"❌ No se pudo iniciar sesión: {e}")
        print("   Primero corre:  python crear_superadmin.py")
        return None


def crear(endpoint, data, headers=None):
    # Aseguramos que el endpoint termine en '/' para evitar el 307 Redirect
    endpoint_limpio = endpoint.strip("/") + "/"
    url = f"{BASE_URL}/{endpoint_limpio}"

    try:
        r = requests.post(url, json=data, headers=headers)
        r.raise_for_status()
        resp = r.json()

        nombre = data.get('nombre', 'Item')
        if isinstance(resp, dict) and 'id' in resp:
            print(f"✅ CREAR OK: {nombre} (ID: {resp['id']})")
            return resp['id']
        else:
            print(f"✅ CREAR OK: {nombre}")
            return resp
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 409 or "already exists" in e.response.text:
            print(f"⚠️ Ya existe: {data.get('nombre')}")
        else:
            print(f"❌ Error en {url}: {e}")
        return None
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return None


def obtener_primera_sucursal(headers):
    """El bootstrap ya creó una sucursal; la reutilizamos."""
    try:
        r = requests.get(f"{BASE_URL}/sucursales/", headers=headers)
        r.raise_for_status()
        data = r.json()
        if data:
            return data[0]["id"]
    except Exception:
        pass
    return None


def main():
    print("\n🌱 POBLANDO BASE DE DATOS (CATÁLOGOS DINÁMICOS) 🌱\n")

    headers = login()
    if not headers:
        return

    # 1. INFRAESTRUCTURA (la sucursal y el SuperAdmin ya existen por el bootstrap)
    suc_id = obtener_primera_sucursal(headers)
    if not suc_id:
        suc_id = crear("sucursales", {"nombre": "Sucursal Centro"}, headers)
    if not suc_id:
        suc_id = 1

    # Usuario vendedor de ejemplo (creación protegida → requiere token)
    usr_id = crear("usuarios", {
        "nombre": "Cajero1", "contrasena_hash": "cajero123",
        "rol": "vendedor", "sucursal_id": suc_id
    }, headers)
    if not usr_id:
        usr_id = 1

    # 2. CLIENTES (abierto)
    crear("clientes", {"nombre": "Público General", "telefono": "000"})
    crear("clientes", {"nombre": "Juan Ganadero", "telefono": "555-1111"})

    # 3. CATÁLOGOS (abierto)
    cat_alim = crear("categorias", {"nombre": "Alimentos"})
    crear("categorias", {"nombre": "Accesorios"})
    cat_mp = crear("categorias", {"nombre": "Materia Prima"})
    crear("categorias", {"nombre": "Farmacia"})

    cat_alim = cat_alim if cat_alim else 1
    cat_mp = cat_mp if cat_mp else 3

    # Subcategorías
    sub_granos = crear("categorias/subcategorias", {"nombre": "Granos", "categoria_id": cat_mp})
    crear("categorias/subcategorias", {"nombre": "Perro", "categoria_id": cat_alim})

    # Marcas
    mar_gamas = crear("marcas", {"nombre": "Gamas"})
    crear("marcas", {"nombre": "Nupec"})
    crear("marcas", {"nombre": "Bayer"})
    mar_gamas = mar_gamas if mar_gamas else 1

    # Tipos de Producto
    crear("tipos-producto", {"nombre": "Alimento"})
    crear("tipos-producto", {"nombre": "Accesorio"})
    crear("tipos-producto", {"nombre": "Farmacia"})
    crear("tipos-producto", {"nombre": "Higiene"})

    # Especies
    esp_cerdo = crear("especies", {"nombre": "Cerdo"})
    crear("especies", {"nombre": "Perro"})
    crear("especies", {"nombre": "Gato"})
    crear("especies", {"nombre": "Ave"})
    esp_cerdo = esp_cerdo if esp_cerdo else 1

    # Etapas
    eta_inicio = crear("etapas", {"nombre": "Inicio"})
    crear("etapas", {"nombre": "Adulto"})
    crear("etapas", {"nombre": "Cachorro"})
    crear("etapas", {"nombre": "Senior"})
    eta_inicio = eta_inicio if eta_inicio else 1

    # 4. PRODUCTOS (creación protegida → requiere token gerente+)
    sub_granos = sub_granos if sub_granos else 1

    prod1 = crear("productos", {
        "nombre": "Gamas Cerdo Inicio - 40kg",
        "tipo_producto": "Alimento",
        "marca_id": mar_gamas,
        "categoria_id": cat_alim,
        "especie_id": esp_cerdo,
        "etapa_id": eta_inicio,
        "unidad_medida": "Bulto",
        "contenido_neto": 40.0,
        "se_vende_a_granel": True,
        "precio_base": 850.00,
        "precio_granel": 25.00,
        "stock_minimo": 200.0
    }, headers)

    prod2 = crear("productos", {
        "nombre": "Maíz Quebrado",
        "tipo_producto": "Materia Prima",
        "categoria_id": cat_mp,
        "subcategoria_id": sub_granos,
        "unidad_medida": "Saco",
        "contenido_neto": 40.0,
        "se_vende_a_granel": True,
        "precio_base": 380.00,
        "precio_granel": 11.00,
        "stock_minimo": 100.0
    }, headers)

    # 5. INVENTARIO (abierto)
    if prod1 and prod2:
        crear("ingreso-inventario", {"producto_id": prod1, "sucursal_id": suc_id, "cantidad": 10, "usuario_id": usr_id})
        crear("ingreso-inventario", {"producto_id": prod2, "sucursal_id": suc_id, "cantidad": 50, "usuario_id": usr_id})

        try:
            crear("corte/abrir", {"sucursal_id": suc_id, "usuario_id": usr_id, "fondo_inicial": 1000})
        except Exception:
            print("⚠️ La caja ya estaba abierta")

    print("\n✨ Datos cargados correctamente. ✨")


if __name__ == "__main__":
    main()
