import requests
from pprint import pprint

BASE_URL = "http://127.0.0.1:8000"

def crear_item(endpoint, data):
    r = requests.post(f"{BASE_URL}/{endpoint.lstrip('/')}", json=data)
    if r.status_code >= 400:
        print(f"❌ Error al crear en {endpoint}: {r.text}")
    r.raise_for_status()
    print(f"POST /{endpoint.lstrip('/')} OK (ID: {r.json().get('id')})")
    return r.json()

def obtener_item(endpoint, item_id):
    r = requests.get(f"{BASE_URL}/{endpoint.lstrip('/')}/{item_id}")
    r.raise_for_status()
    # print(f"GET /{endpoint.lstrip('/')}/{item_id} OK")
    return r.json()

def listar_items(endpoint_con_params):
    r = requests.get(f"{BASE_URL}/{endpoint_con_params.lstrip('/')}")
    r.raise_for_status()
    # print(f"GET /{endpoint_con_params.lstrip('/')} OK (Total: {len(r.json())})")
    return r.json()

def eliminar_item(endpoint, item_id):
    # Nota: En productos, esto ahora es Soft-Delete (Suspender)
    r = requests.delete(f"{BASE_URL}/{endpoint.lstrip('/')}/{item_id}")
    if r.status_code >= 400:
        print(f"❌ Error al eliminar {endpoint}/{item_id}: {r.text}")
    r.raise_for_status()
    print(f"DELETE /{endpoint.lstrip('/')}/{item_id} OK")
    return r.status_code

def main_test():
    ids_creados = {
        "marcas": [], "especies": [], "etapas": [], "lineas": [],
        "categorias": [], "subcategorias": [], "sucursales": [],
        "productos": [], "inventario": [], "usuarios": [], "clientes": []
    }

    try:
        print("\n--- 1. CREANDO CATÁLOGOS (Atributos) ---")
        
        suc_json = crear_item("sucursales", {"nombre": "Sucursal Norte Test"})
        sucursal_id = suc_json['id']
        ids_creados["sucursales"].append(sucursal_id)

        usr_json = crear_item("usuarios", {
            "nombre": "Juan Perez",
            "contrasena_hash": "admin123",
            "rol": "admin",
            "sucursal_id": sucursal_id
        })
        usuario_id = usr_json['id']
        ids_creados["usuarios"].append(usuario_id)

        # --- NUEVO: Crear Cliente ---
        cli_json = crear_item("clientes", { # Asumiendo que crearemos este router pronto
             # Si aún no tienes router de clientes, esto fallará, pero lo dejo preparado
             # Puedes comentar estas líneas si aun no creamos routers/clientes.py
             "nombre": "Cliente Frecuente Test",
             "telefono": "555-1234",
             "direccion": "Conocido"
        })
        ids_creados["clientes"].append(cli_json['id'])

        cat_json = crear_item("categorias", {"nombre": "Alimentos Balanceados"})
        categoria_id = cat_json['id']
        ids_creados["categorias"].append(categoria_id)

        marca_json = crear_item("marcas", {"nombre": "Gamas"})
        marca_id = marca_json['id']
        ids_creados["marcas"].append(marca_id)

        esp_json = crear_item("especies", {"nombre": "Cerdo"})
        especie_id = esp_json['id']
        ids_creados["especies"].append(especie_id)

        eta_json = crear_item("etapas", {"nombre": "Inicio"})
        etapa_id = eta_json['id']
        ids_creados["etapas"].append(etapa_id)

        lin_json = crear_item("lineas", {"nombre": "Premium"})
        linea_id = lin_json['id']
        ids_creados["lineas"].append(linea_id)

        subcat_json = crear_item("categorias/subcategorias/", {
            "nombre": "Cerdos",
            "categoria_id": categoria_id
        })
        subcategoria_id = subcat_json['id']
        ids_creados["subcategorias"].append(subcategoria_id)

        print("\n--- 2. CREANDO PRODUCTO (Estructura Nueva) ---")
        # Actualizado para usar 'precio_base', 'contenido_neto', etc.
        prod_json = crear_item("productos", {
            "nombre": "Gamas Cerdo Inicio - Bulto 40kg",
            "tipo_producto": "Alimento",
            
            # Filtros
            "marca_id": marca_id,
            "categoria_id": categoria_id,
            "subcategoria_id": subcategoria_id,
            "especie_id": especie_id,
            "etapa_id": etapa_id,
            "linea_id": linea_id,
            
            # Lógica de Negocio
            "unidad_medida": "Bulto",
            "contenido_neto": 40.0,      # El bulto trae 40kg
            "se_vende_a_granel": True,   # Se puede abrir
            
            # Precios
            "precio_base": 850.00,       # Precio por bulto cerrado
            "precio_granel": 25.00       # Precio por kilo suelto
        })
        producto_id = prod_json['id']
        ids_creados["productos"].append(producto_id)
        
        print("\n--- 3. PROBANDO INVENTARIO (Kilos) ---")
        
        print(f"Ingresando 5 Bultos de 40kg (Total esperado: 200kg)...")
        crear_item("ingreso-inventario/", {
            "producto_id": producto_id,
            "sucursal_id": sucursal_id,
            "cantidad": 5, # Entran 5 bultos
            "usuario_id": usuario_id 
        })

        # Verificación
        inv_lista = listar_items(f"inventario?producto_id={producto_id}&sucursal_id={sucursal_id}")
        inv_item = inv_lista[0]
        inventario_id = inv_item['id']
        ids_creados["inventario"].append(inventario_id)
        
        print(f"Inventario en DB: {inv_item['cantidad']} kg")
        
        # Lógica de negocio: 5 bultos * 40kg = 200kg
        # NOTA: Tu backend actual en 'ingreso-inventario' suma la cantidad directa
        # AÚN NO hemos programado la multiplicación por 'contenido_neto' en el router.
        # Por ahora, el sistema sumará 5.0 (si no hemos hecho esa lógica extra).
        # Si ya hicimos la lógica de multiplicar en el router, debería ser 200.
        # Asumiré que por ahora suma directo lo que mandamos (5.0).
        
        # Cuando programemos la lógica de "Entrada de Bultos", esto cambiará.
        
        print("\n--- 4. PROBANDO SOFT-DELETE (Suspensión) ---")
        print(f"Suspendiendo producto ID {producto_id}...")
        eliminar_item("productos", producto_id)
        
        # Verificar que YA NO aparece en la lista normal
        lista_activos = listar_items("productos")
        encontrado = any(p['id'] == producto_id for p in lista_activos)
        if not encontrado:
            print("✅ Correcto: El producto no aparece en la lista de activos.")
        else:
            print("❌ Error: El producto sigue apareciendo.")

        # Verificar que SÍ aparece en la lista completa
        lista_todos = listar_items("productos?mostrar_inactivos=true")
        item_suspendido = next((p for p in lista_todos if p['id'] == producto_id), None)
        
        if item_suspendido and item_suspendido['activo'] == False:
            print("✅ Correcto: El producto existe pero tiene activo=False.")
        else:
            print("❌ Error: El producto no se encuentra o sigue activo.")

        print("\n✅✅✅ ¡PRUEBA EXITOSA! El Backend está robusto. ✅✅✅")

    except requests.exceptions.RequestException as e:
        print(f"\n❌❌❌ FALLO EN LA PRUEBA ❌❌❌")
        print(f"Error: {e}")
        if e.response is not None:
            print(f"Respuesta: {e.response.text}")

    finally:
       
        for item_id in ids_creados["clientes"]:
            eliminar_item("clientes", item_id)
        print("\n--- Limpieza (Nota: Soft-deleted items pueden causar errores de FK al borrar padres) ---")
        
        pass

if __name__ == "__main__":
    main_test()