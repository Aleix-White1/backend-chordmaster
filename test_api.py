#!/usr/bin/env python3
"""
Script de prueba para la API de registro con refresh tokens
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_api():
    print("🚀 Probando la API de ChordMaster con Refresh Tokens...")
    
    # 1. Probar endpoint raíz
    print("\n1. Probando endpoint raíz...")
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Respuesta: {response.json()}")
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # 2. Intentar crear las tablas
    print("\n2. Creando tablas en la base de datos...")
    try:
        response = requests.post(f"{BASE_URL}/api/auth/create-tables")
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Respuesta: {response.json()}")
    except Exception as e:
        print(f"⚠️  Error al crear tablas (probablemente ya existen): {e}")
    
    # 3. Probar registro de usuario
    print("\n3. Probando registro de usuario...")
    user_data = {
        "name": "Usuario de Prueba",
        "email": "test@chordmaster.com",
        "password": "password123"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            headers={"Content-Type": "application/json"},
            json=user_data
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            register_data = response.json()
            print(f"✅ Usuario registrado: {register_data['name']} ({register_data['email']})")
            print(f"✅ Access Token: {register_data['access_token'][:50]}...")
            print(f"✅ Refresh Token: {register_data['refresh_token'][:50]}...")
            global refresh_token_from_register
            refresh_token_from_register = register_data['refresh_token']
        else:
            print(f"⚠️  Respuesta: {response.json()}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # 4. Probar login
    print("\n4. Probando login...")
    login_data = {
        "email": "test@chordmaster.com",
        "password": "password123"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            headers={"Content-Type": "application/json"},
            json=login_data
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            token_data = response.json()
            print("✅ Login exitoso!")
            print(f"✅ Access Token: {token_data['access_token'][:50]}...")
            print(f"✅ Refresh Token: {token_data['refresh_token'][:50]}...")
            
            # 5. Probar refresh token
            print("\n5. Probando refresh token...")
            refresh_data = {
                "refresh_token": token_data['refresh_token']
            }
            
            try:
                response = requests.post(
                    f"{BASE_URL}/api/auth/refresh",
                    headers={"Content-Type": "application/json"},
                    json=refresh_data
                )
                print(f"Status: {response.status_code}")
                if response.status_code == 200:
                    new_token_data = response.json()
                    print("✅ Refresh exitoso!")
                    print(f"✅ Nuevo Access Token: {new_token_data['access_token'][:50]}...")
                else:
                    print(f"⚠️  Respuesta: {response.json()}")
            except Exception as e:
                print(f"❌ Error: {e}")
            
            # 6. Probar logout
            print("\n6. Probando logout...")
            try:
                response = requests.post(
                    f"{BASE_URL}/api/auth/logout",
                    headers={"Content-Type": "application/json"},
                    json=refresh_data
                )
                print(f"Status: {response.status_code}")
                if response.status_code == 200:
                    logout_data = response.json()
                    print(f"✅ Logout exitoso: {logout_data['message']}")
                else:
                    print(f"⚠️  Respuesta: {response.json()}")
            except Exception as e:
                print(f"❌ Error: {e}")
                
        else:
            print(f"⚠️  Respuesta: {response.json()}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # 7. Probar logout en todos los dispositivos (usando token del registro)
    print("\n7. Probando logout en todos los dispositivos...")
    try:
        logout_all_data = {
            "refresh_token": refresh_token_from_register
        }
        response = requests.post(
            f"{BASE_URL}/api/auth/logout-all",
            headers={"Content-Type": "application/json"},
            json=logout_all_data
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            logout_all_response = response.json()
            print(f"✅ Logout de todos los dispositivos: {logout_all_response['message']}")
        else:
            print(f"⚠️  Respuesta: {response.json()}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_api()
