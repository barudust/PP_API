import requests
from pprint import pprint

BASE_URL = "http://127.0.0.1:8000"

def crear_item(endpoint, data):
    r = requests.post(f"{BASE_URL}/{endpoint.lstrip('/')}", json=data)
    r.raise_for_status()
    print(f"POST /{endpoint.lstrip('/')} OK (ID: {r.json().get('id')})")
    return r.json()

def obtener_item(endpoint, item_id):
    r = requests.get(f"{BASE_URL}/{endpoint.lstrip('/')}/{item_id}")
    r.raise_for_status()
    print(f"GET /{endpoint.lstrip('/')}/{item_id} OK")
    return r.json()

def listar_items(endpoint_con_params):
    r = requests.get(f"{BASE_URL}/{endpoint_con_params.lstrip('/')}")
    r.raise_for_status()
    print(f"GET /{endpoint_con_params.lstrip('/')} OK (Total: {len(r.json())})")
    return r.json()

def eliminar_item(endpoint, item_id):
    r = requests.delete(f"{BASE_URL}/{endpoint.lstrip('/')}/{item_id}")
    r.raise_for_status()
    print(f"DELETE /{endpoint.lstrip('/')}/{item_id} OK")
    return r.status_code

def main_test():
    ids_creados = {
        "marcas": [], "especies": [], "etapas": [], "lineas": [],
        "categorias": [], "subcategorias": [], "sucursales": [],
        "productos": [], "inventario": [], "usuarios": [] # <-- Añadido
    }

    try:
        print("--- 1. Probando Atributos Simples ---")
        
        suc_json = crear_item("sucursales", {"nombre": "Sucursal Prueba"})
        sucursal_id = suc_json['id']
        ids_creados["sucursales"].append(sucursal_id)

        # --- (NUEVO) Crear el Usuario de Prueba ---
        # (Usamos una contraseña falsa, en el futuro será un hash)
        usr_json = crear_item("usuarios", {
            "nombre": "Usuario de Prueba",
            "contrasena_hash": "fakepassword",
            "rol": "admin",
            "sucursal_id": sucursal_id
        })
        usuario_id = usr_json['id']
        ids_creados["usuarios"].append(usuario_id)
        # --- Fin del nuevo bloque ---

        cat_json = crear_item("categorias", {"nombre": "Alimentos"})
        categoria_id = cat_json['id']
        ids_creados["categorias"].append(categoria_id)

        marca_json = crear_item("marcas", {"nombre": "Marca Prueba"})
        marca_id = marca_json['id']
        ids_creados["marcas"].append(marca_id)

        esp_json = crear_item("especies", {"nombre": "Perro Prueba"})
        especie_id = esp_json['id']
        ids_creados["especies"].append(especie_id)

        eta_json = crear_item("etapas", {"nombre": "Adulto Prueba"})
        etapa_id = eta_json['id']
        ids_creados["etapas"].append(etapa_id)

        lin_json = crear_item("lineas", {"nombre": "Premium Prueba"})
        linea_id = lin_json['id']
        ids_creados["lineas"].append(linea_id)

        print("\n--- 2. Probando Atributos Dependientes ---")
        subcat_json = crear_item("categorias/subcategorias/", {
            "nombre": "Croquetas Prueba",
            "categoria_id": categoria_id
        })
        subcategoria_id = subcat_json['id']
        ids_creados["subcategorias"].append(subcategoria_id)

        print("\n--- 3. Probando Producto (Relacional) ---")
        prod_json = crear_item("productos", {
            "nombre": "Producto Súper Premium Prueba",
            "marca_id": marca_id,
            "categoria_id": categoria_id,
            "subcategoria_id": subcategoria_id,
            "especie_id": especie_id,
            "etapa_id": etapa_id,
            "linea_id": linea_id,
            "unidad": "Bulto",
            "peso_bulto_kg": 25,
            "precio_unitario": 1000.0
        })
        producto_id = prod_json['id']
        ids_creados["productos"].append(producto_id)
        
        print("\n--- 4. Probando Lógica de Negocio (Ingreso de Inventario) ---")
        
        print("Probando INSERCIÓN de inventario (10 bultos)...")
        # --- (CORREGIDO) Usamos el 'usuario_id' que acabamos de crear ---
        ingreso1 = crear_item("ingreso-inventario/", {
            "producto_id": producto_id,
            "sucursal_id": sucursal_id,
            "cantidad": 10,
            "usuario_id": usuario_id 
        })
        # (El ID del ingreso no lo guardamos porque no lo borramos directamente)

        # Ahora sí filtramos el inventario
        inventario_lista = listar_items(f"inventario?producto_id={producto_id}&sucursal_id={sucursal_id}")
        assert len(inventario_lista) == 1, "Debería existir 1 solo registro de inventario"
        inventario_item = inventario_lista[0]
        inventario_id = inventario_item['id']
        ids_creados["inventario"].append(inventario_id)
        
        print("Inventario actual:")
        pprint(inventario_item)
        assert inventario_item['cantidad'] == 10

        # PRUEBA DE ACTUALIZACIÓN (UPDATE)
        print("Probando ACTUALIZACIÓN de inventario (5 bultos más)...")
        ingreso2 = crear_item("ingreso-inventario/", {
            "producto_id": producto_id,
            "sucursal_id": sucursal_id,
            "cantidad": 5,
            "usuario_id": usuario_id
        })
        
        inventario_item_actualizado = obtener_item("inventario", inventario_id)
        print("Inventario actualizado:")
        pprint(inventario_item_actualizado)
        assert inventario_item_actualizado['cantidad'] == 15
        
        print("\n✅✅✅ ¡Todas las pruebas de creación y lógica pasaron! ✅✅✅")

    except requests.exceptions.RequestException as e:
        print(f"\n❌❌❌ ¡PRUEBA FALLIDA! ❌❌❌")
        print(f"Error: {e}")
        if e.response is not None:
            print(f"Respuesta del servidor: {e.response.status_code} - {e.response.text}")

    finally:
        print("\n--- 5. Limpiando datos de prueba (DELETE) ---")
        
        # Borramos en orden inverso
        for item_id in ids_creados["inventario"]:
            eliminar_item("inventario", item_id)

        for item_id in ids_creados["productos"]:
            eliminar_item("productos", item_id)

        for item_id in ids_creados["subcategorias"]:
            eliminar_item("categorias/subcategorias", item_id)

        for item_id in ids_creados["categorias"]:
            eliminar_item("categorias", item_id)
            
        # (NUEVO) Borrar el usuario
        for item_id in ids_creados["usuarios"]:
            eliminar_item("usuarios", item_id)
            
        for item_id in ids_creados["sucursales"]:
            eliminar_item("sucursales", item_id)

        for item_id in ids_creados["marcas"]:
            eliminar_item("marcas", item_id)

        for item_id in ids_creados["especies"]:
            eliminar_item("especies", item_id)
            
        for item_id in ids_creados["etapas"]:
            eliminar_item("etapas", item_id)
            
        for item_id in ids_creados["lineas"]:
            eliminar_item("lineas", item_id)
        
        print("\nLimpieza completada.")

if __name__ == "__main__":
    main_test()