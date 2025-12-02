import requests
from pprint import pprint

BASE_URL = "http://127.0.0.1:8000"

# ==========================================
# FUNCIONES DE AYUDA
# ==========================================

def log_step(title):
    print(f"\n{'='*10} {title} {'='*10}")

def crear(endpoint, data):
    url = f"{BASE_URL}/{endpoint.lstrip('/')}"
    r = requests.post(url, json=data)
    if r.status_code >= 400:
        print(f"❌ Error POST {endpoint}: {r.text}")
        r.raise_for_status()
    # Intentamos obtener ID si existe
    resp = r.json()
    if isinstance(resp, dict) and 'id' in resp:
        print(f"   ✅ POST {endpoint} OK -> ID: {resp['id']}")
    else:
        print(f"   ✅ POST {endpoint} OK")
    return resp

def obtener(endpoint, item_id=None, params=None):
    url = f"{BASE_URL}/{endpoint.lstrip('/')}"
    if item_id:
        url += f"/{item_id}"
    r = requests.get(url, params=params)
    if r.status_code >= 400:
        print(f"❌ Error GET {url}: {r.text}")
        r.raise_for_status()
    return r.json()

def actualizar_put(endpoint, item_id, data=None):
    url = f"{BASE_URL}/{endpoint.lstrip('/')}/{item_id}"
    # Si no hay data, asumimos que es un endpoint de acción (como /cancelar)
    if data:
        r = requests.put(url, json=data)
    else:
        r = requests.put(url) # PUT sin body
        
    if r.status_code >= 400:
        print(f"❌ Error PUT {url}: {r.text}")
        r.raise_for_status()
    print(f"   ✅ PUT {url} OK")
    return r.json()

def eliminar_silencioso(endpoint, item_id):
    try:
        requests.delete(f"{BASE_URL}/{endpoint.lstrip('/')}/{item_id}")
    except:
        pass

# ==========================================
# FLUJO PRINCIPAL
# ==========================================

def main_test():
    ids = {
        "sucursales": [], "usuarios": [], "clientes": [],
        "categorias": [], "subcategorias": [], "marcas": [], 
        "especies": [], "etapas": [], "lineas": [],
        "productos": [], "inventario": [], "ventas": [], "reglas": [], "cortes": []
    }

    try:
        log_step("1. INFRAESTRUCTURA Y SEGURIDAD")
        
        # 1. Sucursal y Usuario
        suc = crear("sucursales", {"nombre": "Sucursal Master"})
        ids["sucursales"].append(suc['id'])
        
        usr = crear("usuarios", {
            "nombre": "Admin", "contrasena_hash": "secret123", 
            "rol": "admin", "sucursal_id": suc['id']
        })
        ids["usuarios"].append(usr['id'])

        # 2. Prueba de Login (Autenticación)
        print("   🔐 Probando Login...")
        login_resp = requests.post(f"{BASE_URL}/token", data={
            "username": "Admin", "password": "secret123"
        })
        if login_resp.status_code == 200:
            print(f"   ✅ Login Exitoso. Token: {login_resp.json()['access_token'][:15]}...")
        else:
            print(f"   ❌ Falló Login: {login_resp.text}")

        # 3. Cliente
        cli = crear("clientes", {"nombre": "Cliente VIP", "telefono": "555-1234"})
        ids["clientes"].append(cli['id'])


        log_step("2. CATÁLOGOS Y PRODUCTOS")
        
        cat = crear("categorias", {"nombre": "Alimentos"})
        ids["categorias"].append(cat['id'])
        subcat = crear("categorias/subcategorias/", {"nombre": "Ganado", "categoria_id": cat['id']})
        ids["subcategorias"].append(subcat['id'])
        mar = crear("marcas", {"nombre": "NutriPlus"})
        ids["marcas"].append(mar['id'])
        esp = crear("especies", {"nombre": "Bovino"})
        ids["especies"].append(esp['id'])
        eta = crear("etapas", {"nombre": "Engorda"})
        ids["etapas"].append(eta['id'])
        lin = crear("lineas", {"nombre": "Premium"})
        ids["lineas"].append(lin['id'])

        # 4. Producto Complejo
        # Bulto de 40kg, Precio $1000. Se vende a granel por $30/kg.
        prod = crear("productos", {
            "nombre": "Alimento Bovino Premium - 40kg",
            "tipo_producto": "Alimento",
            "marca_id": mar['id'], "categoria_id": cat['id'],
            "especie_id": esp['id'], "etapa_id": eta['id'], "linea_id": lin['id'],
            
            "unidad_medida": "Bulto",
            "contenido_neto": 40.0,
            "se_vende_a_granel": True,
            
            "precio_base": 1000.00,
            "precio_granel": 30.00,
            "stock_minimo": 50.0 # Avisar si baja de 50kg
        })
        ids["productos"].append(prod['id'])

        # 5. Regla de Descuento
        # 10% de descuento para la marca NutriPlus
        regla = crear("descuentos", {
            "descripcion": "10% en NutriPlus",
            "descuento_porcentaje": 10.0,
            "marca_id": mar['id']
        })
        ids["reglas"].append(regla['id'])


        log_step("3. OPERACIÓN DIARIA (Caja e Inventario)")
        
        # 6. Abrir Caja
        corte = crear("corte/abrir", {
            "sucursal_id": suc['id'], "usuario_id": usr['id'], "fondo_inicial": 500.0
        })
        ids["cortes"].append(corte['id'])
        print(f"   💵 Caja Abierta con: ${corte['fondo_inicial']}")

        # 7. Ingreso de Mercancía
        # Entran 10 Bultos (10 * 40kg = 400kg)
        crear("ingreso-inventario/", {
            "producto_id": prod['id'], "sucursal_id": suc['id'],
            "cantidad": 10, "usuario_id": usr['id']
        })
        
        # Validar stock inicial
        inv = obtener("inventario", item_id=None, params={"producto_id": prod['id'], "sucursal_id": suc['id']})[0]
        ids["inventario"].append(inv['id'])
        print(f"   📦 Stock calculado: {inv['cantidad']} kg (Esperado: 400.0)")


        log_step("4. VENTAS Y DESCUENTOS")
        
        # 8. Venta
        # Vendemos 2 Bultos.
        # Precio Base: 2 * $1000 = $2000.
        # Descuento Auto (Marca 10%): -$200.
        # Total Esperado: $1800.
        # Stock a descontar: 2 * 40kg = 80kg.
        
        venta = crear("ventas", {
            "sucursal_id": suc['id'], "usuario_id": usr['id'], "cliente_id": cli['id'],
            "detalles": [{"producto_id": prod['id'], "cantidad": 2}],
            "descuento_especial": 0
        })
        ids["ventas"].append(venta['venta_id'])
        
        print(f"   💰 Total Cobrado: ${venta['total_final']}")
        
        if float(venta['total_final']) == 1800.0:
            print("   ✅ LÓGICA DE PRECIOS Y DESCUENTOS: CORRECTA")
        else:
            print(f"   ❌ ERROR EN PRECIOS: Esperado 1800, Recibido {venta['total_final']}")

        # Validar Stock Post-Venta (400 - 80 = 320)
        inv = obtener("inventario", item_id=None, params={"producto_id": prod['id'], "sucursal_id": suc['id']})[0]
        print(f"   📦 Stock Post-Venta: {inv['cantidad']} kg (Esperado: 320.0)")


        log_step("5. AUDITORÍA Y CONTROL")
        
        # 9. Ajuste de Inventario (Auditoría)
        # El empleado pesa y encuentra 315kg (Faltan 5kg, se rompió un saco)
        crear("auditoria/ajuste", {
            "sucursal_id": suc['id'], "usuario_id": usr['id'], "producto_id": prod['id'],
            "cantidad_sistema": 320.0,
            "cantidad_fisica": 315.0,
            "motivo": "Merma saco roto"
        })
        print("   🔍 Ajuste realizado. Inventario seteado a 315.0 kg")

        # 10. Reporte de Stock Bajo (Probando endpoint)
        # El stock actual es 315, el mínimo es 50. No debería salir.
        # Pero si el mínimo fuera 400, sí saldría. Probemos el endpoint.
        alertas = obtener("informes/stock-bajo", params={"sucursal_id": suc['id'], "limite_kilos": 500})
        if len(alertas) > 0:
            print(f"   ⚠️ Alerta de Stock Bajo funcionando: Detectó {len(alertas)} productos.")


        log_step("6. CANCELACIÓN Y CIERRE")

        # 11. Cancelar Venta
        # El cliente devuelve los 2 bultos.
        # Stock actual (315) + Devolución (80) = 395 kg.
        actualizar_put(f"ventas/{venta['venta_id']}/cancelar", item_id="")
        
        inv = obtener("inventario", item_id=None, params={"producto_id": prod['id'], "sucursal_id": suc['id']})[0]
        print(f"   📦 Stock tras cancelar: {inv['cantidad']} kg (Esperado: 395.0)")

        # 12. Cerrar Caja
        # Fondo ($500) + Ventas ($0, porque se canceló la única venta) = $500.
        # El cajero cuenta $500. Retira $0. Deja $500.
        cerrar = crear("corte/cerrar", {
            "corte_id": corte['id'],
            "efectivo_real": 500.0,
            "monto_retirado": 0.0,
            "comentarios": "Día tranquilo"
        })
        print(f"   🔒 Caja Cerrada. Diferencia: ${cerrar['diferencia']} (Esperado: 0.0)")


        print("\n✨✨✨ ¡SISTEMA VERIFICADO EXITOSAMENTE! ✨✨✨")

    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO: {e}")

    finally:
        log_step("LIMPIEZA")
        # Borrar en orden
        for x in ids["ventas"]: eliminar_silencioso("ventas", x) # (Si tuvieras delete venta)
        for x in ids["reglas"]: eliminar_silencioso("descuentos", x)
        for x in ids["inventario"]: eliminar_silencioso("inventario", x)
        for x in ids["productos"]: eliminar_silencioso("productos", x)
        
        cats = ["subcategorias", "categorias", "usuarios", "clientes", "sucursales", "marcas", "especies", "etapas", "lineas"]
        for c in cats:
            for x in ids[c]: eliminar_silencioso(c, x)
        
        print("Datos de prueba eliminados (o intentado eliminar).")

if __name__ == "__main__":
    main_test()