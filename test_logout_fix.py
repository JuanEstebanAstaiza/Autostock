#!/usr/bin/env python3
"""
Script para probar que el logout funciona correctamente desde la navbar
"""

import requests
import time

def test_logout_endpoint():
    """Probar el endpoint de logout"""
    print("🧪 Probando endpoint de logout...")

    # Primero intentar GET (debería fallar)
    try:
        response = requests.get("http://127.0.0.1:8000/logout", allow_redirects=False)
        print(f"GET /logout: {response.status_code} - {response.reason}")
        if response.status_code == 405:
            print("✅ GET correctamente rechazado (405 Method Not Allowed)")
        else:
            print("⚠️ GET no fue rechazado como esperado")
    except Exception as e:
        print(f"❌ Error en GET /logout: {e}")

    # Ahora probar POST (debería funcionar)
    try:
        response = requests.post("http://127.0.0.1:8000/logout", allow_redirects=False)
        print(f"POST /logout: {response.status_code} - {response.reason}")
        if response.status_code == 302:
            print("✅ POST funciona correctamente (redirección a /login)")
            print(f"   Location: {response.headers.get('location', 'No especificado')}")
        else:
            print("⚠️ POST no funcionó como esperado")
    except Exception as e:
        print(f"❌ Error en POST /logout: {e}")

    print("\n📝 El botón en la navbar ahora usa POST, por lo que debería funcionar correctamente.")
    print("🔗 Para probar manualmente: ve a /negocio/notificaciones y haz clic en 'Cerrar Sesión'")

if __name__ == "__main__":
    # Esperar un poco para que el servidor esté listo
    print("⏳ Esperando que el servidor esté listo...")
    time.sleep(2)

    test_logout_endpoint()
