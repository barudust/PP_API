"""
Smoke test end-to-end (reemplaza al viejo si.py).

Ejercita el flujo completo contra una API corriendo, incluyendo las novedades de
Fase 2/3: RBAC, atributos JSONB, filtros dinámicos, ajuste tipificado con
tolerancia de fábrica, y KPIs del dashboard.

Requisitos:
    1) API corriendo en BASE_URL con la BD migrada (alembic upgrade head)
    2) SuperAdmin creado:  python crear_superadmin.py

Uso:
    python tests/smoke_e2e.py
"""
import sys
import requests

# La consola de Windows usa cp1252 por defecto y truena con emojis.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE_URL = "http://127.0.0.1:8000"
SUPERADMIN_USER = "Admin"
SUPERADMIN_PASS = "admin123"

_fallos = []


def check(nombre, condicion, detalle=""):
    estado = "✅" if condicion else "❌"
    print(f"   {estado} {nombre}" + (f"  ({detalle})" if detalle else ""))
    if not condicion:
        _fallos.append(nombre)


def login():
    r = requests.post(
        f"{BASE_URL}/token",
        data={"username": SUPERADMIN_USER, "password": SUPERADMIN_PASS},
    )
    r.raise_for_status()
    data = r.json()
    return {"Authorization": f"Bearer {data['access_token']}"}, data["usuario_id"], data["sucursal_id"]


def post(path, json=None, data=None, headers=None, esperar_ok=True):
    r = requests.post(f"{BASE_URL}{path}", json=json, data=data, headers=headers)
    if esperar_ok and r.status_code >= 400:
        print(f"      ⚠️ POST {path} -> {r.status_code}: {r.text[:200]}")
    return r


def get(path, headers=None):
    return requests.get(f"{BASE_URL}{path}", headers=headers)


def main():
    print("\n🧪 SMOKE TEST E2E\n")

    print("1) Autenticación y RBAC")
    H, uid, suc_id = login()
    check("login superadmin", True)
    # Sin token, /usuarios debe dar 401
    r = get("/usuarios/")
    check("usuarios sin token -> 401", r.status_code == 401, f"got {r.status_code}")
    # Con token, /usuarios debe dar 200
    r = get("/usuarios/", headers=H)
    check("usuarios con token -> 200", r.status_code == 200, f"got {r.status_code}")

    print("2) Catálogo + producto con atributos JSONB")
    marca = post("/marcas/", json={"nombre": "SmokeMarca"}, headers=H).json()
    post("/tipos-producto/", json={"nombre": "Alimento"}, headers=H)
    prod = post("/productos/", json={
        "nombre": "Smoke Bulto 40kg",
        "tipo_producto": "Alimento",
        "marca_id": marca["id"],
        "unidad_medida": "Bulto",
        "contenido_neto": 40.0,
        "se_vende_a_granel": True,
        "tolerancia_unidad": 0.25,
        "ubicacion_fisica": "Pasillo 3",
        "atributos_extra": {"linea": "Premium", "sabor": "Pollo"},
        "precio_base": 1000.00,
        "precio_granel": 30.00,
        "stock_minimo": 50.0,
    }, headers=H).json()
    pid = prod["id"]
    check("producto creado", "id" in prod, f"id={pid}")
    check("atributos_extra persistido como dict",
          isinstance(prod.get("atributos_extra"), dict) and prod["atributos_extra"].get("linea") == "Premium",
          str(prod.get("atributos_extra")))

    # Regla de descuento por marca (10%)
    post("/descuentos/", json={
        "descripcion": "10% SmokeMarca", "descuento_porcentaje": 10.0, "marca_id": marca["id"]
    }, headers=H)

    print("3) Filtros dinámicos JSONB")
    r = get("/productos/?tipo=Alimento&atributos=%7B%22linea%22%3A%22Premium%22%7D", headers=H)
    encontrados = [p for p in r.json() if p["id"] == pid]
    check("filtro por atributos JSONB encuentra el producto", len(encontrados) == 1)
    r = get("/productos/atributos-disponibles?tipo=Alimento", headers=H)
    disp = r.json()
    check("atributos-disponibles lista 'linea'", "linea" in disp and "Premium" in disp["linea"], str(disp))

    print("4) Ingreso de inventario (10 bultos -> 400kg)")
    post("/ingreso-inventario/", json={
        "producto_id": pid, "sucursal_id": suc_id, "cantidad": 10, "usuario_id": uid
    })
    stock = get(f"/inventario?producto_id={pid}&sucursal_id={suc_id}").json()
    check("stock inicial = 400", abs(float(stock[0]["cantidad"]) - 400.0) < 0.01, str(stock[0]["cantidad"]))

    print("5) Caja + ventas híbridas (bulto y granel)")
    post("/corte/abrir", json={"sucursal_id": suc_id, "usuario_id": uid, "fondo_inicial": 500})
    # Venta 2 bultos: 2*1000 -10% = 1800 ; stock 400-80=320
    v1 = post("/ventas/", json={
        "sucursal_id": suc_id, "usuario_id": uid,
        "detalles": [{"producto_id": pid, "cantidad": 2, "es_granel": False}],
    }).json()
    check("total venta bulto = 1800", abs(float(v1["total_final"]) - 1800.0) < 0.01, str(v1.get("total_final")))
    # Venta granel 5kg: 30 -10% = 27 *5 = 135 ; stock 320-5=315
    v2 = post("/ventas/", json={
        "sucursal_id": suc_id, "usuario_id": uid,
        "detalles": [{"producto_id": pid, "cantidad": 5, "es_granel": True}],
    }).json()
    check("total venta granel = 135", abs(float(v2["total_final"]) - 135.0) < 0.01, str(v2.get("total_final")))
    stock = get(f"/inventario?producto_id={pid}&sucursal_id={suc_id}").json()
    check("stock tras ventas = 315", abs(float(stock[0]["cantidad"]) - 315.0) < 0.01, str(stock[0]["cantidad"]))

    print("6) Auditoría: plan de conteo + ajuste tipificado con tolerancia")
    r = get(f"/auditoria/plan-conteo?sucursal_id={suc_id}&tipo_producto=Alimento", headers=H)
    plan = [x for x in r.json() if x["id"] == pid]
    check("plan-conteo incluye el producto con stock 315",
          len(plan) == 1 and abs(float(plan[0]["cantidad_sistema"]) - 315.0) < 0.01)
    # Físico 314.8 -> diff -0.2. tolerancia = (315/40)*0.25 = 1.969 -> dentro -> VARIACION_FABRICA
    aj = post("/auditoria/ajuste", json={
        "sucursal_id": suc_id, "usuario_id": uid, "producto_id": pid,
        "cantidad_fisica": 314.8
    }, headers=H).json()
    check("ajuste dentro de tolerancia de fábrica", aj.get("dentro_de_tolerancia") is True, str(aj.get("tolerancia_calculada")))
    check("tipo sugerido = VARIACION_FABRICA", aj.get("tipo_ajuste") == "VARIACION_FABRICA", str(aj.get("tipo_ajuste")))

    print("7) Dashboard SuperAdmin (KPIs)")
    r = get("/dashboard/resumen", headers=H)
    check("dashboard/resumen requiere superadmin y responde 200", r.status_code == 200)
    resumen = r.json()
    check("ventas_hoy ~ 1935", abs(float(resumen["ventas_hoy"]) - 1935.0) < 0.01, str(resumen["ventas_hoy"]))
    r = get(f"/dashboard/top-productos?sucursal_id={suc_id}", headers=H)
    top = r.json()
    check("top-productos incluye el producto", any(t["producto_id"] == pid for t in top))
    r = get("/dashboard/ventas-por-sucursal", headers=H)
    check("ventas-por-sucursal responde lista", isinstance(r.json(), list))

    print("8) Cancelación exacta (usa cantidad_base guardada)")
    requests.put(f"{BASE_URL}/ventas/{v1['venta_id']}/cancelar")
    stock = get(f"/inventario?producto_id={pid}&sucursal_id={suc_id}").json()
    # 314.8 + 80 (2 bultos) = 394.8
    check("stock tras cancelar bulto = 394.8", abs(float(stock[0]["cantidad"]) - 394.8) < 0.01, str(stock[0]["cantidad"]))

    print("9) Fase 4: bloqueo de sobreventa (ACID) + bitácora")
    r = post("/ventas/", json={
        "sucursal_id": suc_id, "usuario_id": uid,
        "detalles": [{"producto_id": pid, "cantidad": 10000, "es_granel": True}],
    }, esperar_ok=False)
    check("sobreventa bloqueada -> 400", r.status_code == 400, f"got {r.status_code}")
    stock = get(f"/inventario?producto_id={pid}&sucursal_id={suc_id}").json()
    check("stock intacto tras sobreventa fallida (394.8)", abs(float(stock[0]["cantidad"]) - 394.8) < 0.01, str(stock[0]["cantidad"]))
    hist = get(f"/auditoria/historial?producto_id={pid}", headers=H).json()
    tipos = {h["tipo_movimiento"] for h in hist}
    check("bitácora registró COMPRA y VENTA", "COMPRA" in tipos and "VENTA" in tipos, str(tipos))

    print("\n" + ("=" * 40))
    if _fallos:
        print(f"❌ FALLARON {len(_fallos)} checks: {_fallos}")
        sys.exit(1)
    print("✨ TODOS LOS CHECKS PASARON ✨")


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("❌ No hay conexión con la API. ¿Corriste 'uvicorn main:app'?")
        sys.exit(2)
