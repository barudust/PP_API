import requests
import random

BASE_URL = "http://127.0.0.1:8000"

def crear(endpoint, data):
    # CORRECCIÓN: Aseguramos que el endpoint termine en '/' para evitar el 307 Redirect
    endpoint_limpio = endpoint.strip("/") + "/"
    url = f"{BASE_URL}/{endpoint_limpio}"
    
    try:
        r = requests.post(url, json=data)
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
        # Si ya existe, no es error crítico, solo avisamos
        if e.response.status_code == 409 or "already exists" in e.response.text:
             print(f"⚠️ Ya existe: {data.get('nombre')}")
        else:
             print(f"❌ Error en {url}: {e}")
        return None
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return None

def main():
    print("\n🌱 POBLANDO BASE DE DATOS (CATÁLOGOS DINÁMICOS) 🌱\n")

    # 1. INFRAESTRUCTURA
    suc_id = crear("sucursales", {"nombre": "Sucursal Centro"})
    if not suc_id: suc_id = 1 

    usr_id = crear("usuarios", {
        "nombre": "Admin", "contrasena_hash": "admin123", "rol": "admin", "sucursal_id": suc_id
    })
    if not usr_id: usr_id = 1

    # 2. CLIENTES
    crear("clientes", {"nombre": "Público General", "telefono": "000"})
    crear("clientes", {"nombre": "Juan Ganadero", "telefono": "555-1111"})

    # 3. CATÁLOGOS
    cat_alim = crear("categorias", {"nombre": "Alimentos"})
    cat_acc = crear("categorias", {"nombre": "Accesorios"})
    cat_mp = crear("categorias", {"nombre": "Materia Prima"})
    cat_med = crear("categorias", {"nombre": "Farmacia"})

    cat_alim = cat_alim if cat_alim else 1
    cat_mp = cat_mp if cat_mp else 3
    
    # Subcategorías
    sub_granos = crear("categorias/subcategorias", {"nombre": "Granos", "categoria_id": cat_mp})
    sub_perro = crear("categorias/subcategorias", {"nombre": "Perro", "categoria_id": cat_alim})
    
    # Marcas
    mar_gamas = crear("marcas", {"nombre": "Gamas"})
    mar_nupec = crear("marcas", {"nombre": "Nupec"})
    mar_bayer = crear("marcas", {"nombre": "Bayer"})
    mar_gamas = mar_gamas if mar_gamas else 1

    # ==========================================
    # NUEVAS ADICIONES (TIPOS, ESPECIES, ETAPAS)
    # ==========================================
    
    # Tipos de Producto (Nuevo catálogo dinámico)
    tip_alim = crear("tipos-producto", {"nombre": "Alimento"})
    tip_acc = crear("tipos-producto", {"nombre": "Accesorio"})
    tip_farm = crear("tipos-producto", {"nombre": "Farmacia"})
    tip_hig = crear("tipos-producto", {"nombre": "Higiene"})

    # Especies
    esp_cerdo = crear("especies", {"nombre": "Cerdo"})
    esp_perro = crear("especies", {"nombre": "Perro"})
    esp_gato = crear("especies", {"nombre": "Gato"})
    esp_ave = crear("especies", {"nombre": "Ave"})
    esp_cerdo = esp_cerdo if esp_cerdo else 1

    # Etapas
    eta_inicio = crear("etapas", {"nombre": "Inicio"})
    eta_adulto = crear("etapas", {"nombre": "Adulto"})
    eta_cachorro = crear("etapas", {"nombre": "Cachorro"})
    eta_senior = crear("etapas", {"nombre": "Senior"})
    eta_inicio = eta_inicio if eta_inicio else 1

    # 4. PRODUCTOS
    sub_granos = sub_granos if sub_granos else 1
    
    # A. ALIMENTO
    prod1 = crear("productos", {
        "nombre": "Gamas Cerdo Inicio - 40kg",
        "tipo_producto": "Alimento", # Aquí podrías pasar el string o el ID según tu lógica final
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
    })

    # B. MATERIA PRIMA
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
    })

    # 5. INVENTARIO
    if prod1 and prod2:
        crear("ingreso-inventario", {"producto_id": prod1, "sucursal_id": suc_id, "cantidad": 10, "usuario_id": usr_id}) 
        crear("ingreso-inventario", {"producto_id": prod2, "sucursal_id": suc_id, "cantidad": 50, "usuario_id": usr_id})
        
        try:
            crear("corte/abrir", {"sucursal_id": suc_id, "usuario_id": usr_id, "fondo_inicial": 1000})
        except:
            print("⚠️ La caja ya estaba abierta")

    print("\n✨ Datos cargados correctamente. ✨")

if __name__ == "__main__":
    main()