#!/usr/bin/env python3
"""
Script para probar que la navegación funciona correctamente en todas las páginas
"""

import requests
import time

def test_navbar_pages():
    """Probar que todas las páginas tienen navegación con notificaciones"""
    pages = [
        ("Dashboard", "/negocio/dashboard"),
        ("Inventario", "/negocio/inventario"),
        ("Ventas", "/negocio/ventas"),
        ("Usuarios", "/negocio/usuarios"),
        ("Reportes", "/negocio/reportes"),
        ("Notificaciones", "/negocio/notificaciones")
    ]

    print("🧪 Probando navegación en todas las páginas...")

    for page_name, url in pages:
        try:
            response = requests.get(f"http://127.0.0.1:8000{url}", allow_redirects=False)
            if response.status_code == 200:
                content = response.text
                # Verificar que tenga el enlace a notificaciones
                if 'href="/negocio/notificaciones"' in content:
                    print(f"✅ {page_name}: Navegación completa")
                else:
                    print(f"❌ {page_name}: Falta enlace a notificaciones")
            else:
                print(f"⚠️ {page_name}: Código {response.status_code}")
        except Exception as e:
            print(f"❌ {page_name}: Error - {e}")

    print("\n🔗 Verificando logout...")
    try:
        # Probar que logout funciona (debe redirigir)
        response = requests.post("http://127.0.0.1:8000/logout", allow_redirects=False)
        if response.status_code == 302 and response.headers.get('location') == '/login':
            print("✅ Logout funciona correctamente")
        else:
            print(f"❌ Logout falló: {response.status_code}")
    except Exception as e:
        print(f"❌ Error en logout: {e}")

if __name__ == "__main__":
    print("⏳ Esperando que el servidor esté listo...")
    time.sleep(2)

    test_navbar_pages()
    print("✅ Prueba completada")
