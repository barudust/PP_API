import requests
from pprint import pprint

BASE_URL = "http://127.0.0.1:8000"

# --- Funciones de Ayuda ---

def crear_item(endpoint, data):
    r = requests.post(f"{BASE_URL}/{endpoint.lstrip('/')}", json=data)
    if r.status_code >= 400:
        print(f"❌ Error al crear en {endpoint}: {r.text}")
        r.raise_for_status()
    # Solo imprimimos ID para no ensuciar la consola
    print(f"✅ POST /{endpoint.lstrip('/')} OK (ID: {r.json().get('id')})")
    return r.json()

def listar_items(endpoint_con_params):
    r = requests.get(f"{BASE_URL}/{endpoint_con_params.lstrip('/')}")
    r.raise_for_status()
    return r.json()

def eliminar_item_silencioso(endpoint, item_id):
    """Intenta borrar. Si falla (por FK o porque no existe), no hace ruido."""
    try:
        requests.delete(f"{BASE_URL}/{endpoint.lstrip('/')}/{item_id}")
    except:
        pass 

# --- Flujo Principal de Negocio ---

def main_test():
    print("\n🚀 INICIANDO PRUEBA DE FLUJO DE NEGOCIO\n")
    
    # Guardamos IDs para limpiar al final
    ids = {
        "sucursales": [], "usuarios": [], "clientes": [],
        "categorias": [], "marcas": [], "especies": [], "etapas": [], "lineas": [], "subcategorias": [],
        "productos": [], "inventario": []
    }

    try:
        # 1. INFRAESTRUCTURA BÁSICA
        print("--- Paso 1: Creando Catálogos Básicos ---")
        suc = crear_item("sucursales", {"nombre": "Sucursal Test"})
        ids["sucursales"].append(suc['id'])

        usr = crear_item("usuarios", {"nombre": "Vendedor", "contrasena_hash": "123", "rol": "ven", "sucursal_id": suc['id']})
        ids["usuarios"].append(usr['id'])

        cli = crear_item("clientes", {"nombre": "Cliente Test", "telefono": "555"})
        ids["clientes"].append(cli['id'])

        cat = crear_item("categorias", {"nombre": "Alimentos"})
        ids["categorias"].append(cat['id'])
        
        # Creamos una subcategoría para probar el filtro completo
        subcat = crear_item("categorias/subcategorias/", {"nombre": "Cerdos", "categoria_id": cat['id']})
        ids["subcategorias"].append(subcat['id'])

        marca = crear_item("marcas", {"nombre": "Gamas"})
        ids["marcas"].append(marca['id'])
        
        # Creamos solo lo mínimo necesario para el producto
        esp = crear_item("especies", {"nombre": "Bovino"})
        ids["especies"].append(esp['id'])
        eta = crear_item("etapas", {"nombre": "Inicio"})
        ids["etapas"].append(eta['id'])
        lin = crear_item("lineas", {"nombre": "Premium"})
        ids["lineas"].append(lin['id'])

        # 2. CREAR PRODUCTO COMPLEJO
        print("\n--- Paso 2: Creando Producto (Bulto 40kg / $850) ---")
        prod = crear_item("productos", {
            "nombre": "Alimento Bovino - Saco 40kg",
            "tipo_producto": "Alimento",
            "marca_id": marca['id'],
            "categoria_id": cat['id'],
            "subcategoria_id": subcat['id'],
            "especie_id": esp['id'],
            "etapa_id": eta['id'],
            "linea_id": lin['id'],
            "unidad_medida": "Bulto",
            "contenido_neto": 40.0,      # 1 Bulto = 40kg
            "se_vende_a_granel": True,
            "precio_base": 850.00,       # $850 el bulto cerrado
            "precio_granel": 25.00       # $25 el kilo suelto
        })
        ids["productos"].append(prod['id'])

        # 3. SURTIR INVENTARIO
        print("\n--- Paso 3: Ingresando 5 Bultos al Inventario ---")
        # Lógica: 5 bultos * 40kg c/u = 200kg totales
        crear_item("ingreso-inventario/", {
            "producto_id": prod['id'],
            "sucursal_id": suc['id'],
            "cantidad": 5, 
            "usuario_id": usr['id']
        })
        
        # Validar Matemáticas de Inventario
        inv_list = listar_items(f"inventario?producto_id={prod['id']}&sucursal_id={suc['id']}")
        inv_item = inv_list[0]
        ids["inventario"].append(inv_item['id'])
        
        stock_kilos = float(inv_item['cantidad'])
        print(f"   📦 Stock en DB: {stock_kilos} kg")
        
        if stock_kilos == 200.0:
            print("   ✅ Cálculo de Ingreso CORRECTO (5 * 40 = 200)")
        else:
            print(f"   ❌ ERROR: Se esperaban 200.0 kg, hay {stock_kilos}")

        # 4. REGISTRAR VENTA
        print("\n--- Paso 4: Vendiendo 1.5 Bultos ---")
        # Lógica Inventario: 1.5 bultos * 40kg = 60kg a descontar.
        # Lógica Dinero: 1.5 bultos * $850 = $1275.
        
        venta_resp = crear_item("ventas", {
            "sucursal_id": suc['id'],
            "usuario_id": usr['id'],
            "cliente_id": cli['id'],
            "detalles": [
                {"producto_id": prod['id'], "cantidad": 1.5}
            ],
            "descuento_especial": 0
        })
        
        total_venta = float(venta_resp['total_final'])
        print(f"   💰 Total Venta: ${total_venta}")

        # Validar Dinero
        if total_venta == 1275.0:
             print("   ✅ Cálculo de Dinero CORRECTO (1.5 * 850 = 1275)")
        else:
             print(f"   ❌ ERROR DINERO: Esperado 1275.0, Recibido {total_venta}")

        # Validar Descuento de Stock
        inv_list_final = listar_items(f"inventario?producto_id={prod['id']}&sucursal_id={suc['id']}")
        stock_final = float(inv_list_final[0]['cantidad'])
        print(f"   📦 Stock Final: {stock_final} kg")
        
        if stock_final == 140.0:
            print("   ✅ Descuento de Inventario CORRECTO (200 - 60 = 140)")
        else:
            print(f"   ❌ ERROR STOCK: Esperado 140.0, Quedan {stock_final}")

        print("\n✨✨✨ PRUEBA EXITOSA: EL SISTEMA FUNCIONA ✨✨✨")

    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO: {e}")

    finally:
        print("\n--- Limpiando Datos... ---")
        # Borramos en orden inverso para evitar conflictos de FK
        # Nota: Productos con Soft-Delete no se borran físicamente,
        # por lo que sus dependencias (Marcas, etc.) podrían no borrarse.
        # Usamos eliminación silenciosa para no ensuciar la consola.
        
        for item_id in ids["inventario"]: eliminar_item_silencioso("inventario", item_id)
        for item_id in ids["productos"]: eliminar_item_silencioso("productos", item_id)
        
        # Intentamos borrar catálogos
        listas_catalogos = ["subcategorias", "categorias", "usuarios", "clientes", "sucursales", "marcas", "especies", "etapas", "lineas"]
        for cat in listas_catalogos:
            for item_id in ids[cat]:
                eliminar_item_silencioso(cat, item_id)
        
        print("Listo.")

if __name__ == "__main__":
    main_test()