#!/usr/bin/env python3
"""Script de test pour vérifier l'authentification"""

import requests
import json

def test_auth():
    """Tester l'authentification"""
    base_url = 'http://localhost:5000'
    
    print("🔍 Test de l'authentification...")
    
    # Test 1: Route de santé
    try:
        response = requests.get(f'{base_url}/health')
        print(f"✅ /health: {response.status_code}")
        if response.status_code == 200:
            print(f"   Réponse: {response.json()}")
    except Exception as e:
        print(f"❌ /health: {e}")
    
    # Test 2: Connexion admin
    try:
        login_data = {
            'username': 'admin',
            'password': 'admin123'
        }
        response = requests.post(
            f'{base_url}/auth/login',
            json=login_data,
            headers={'Content-Type': 'application/json'}
        )
        print(f"✅ /auth/login (admin): {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Token: {data.get('token', 'N/A')[:20]}...")
            print(f"   User: {data.get('user', {}).get('username', 'N/A')}")
        else:
            print(f"   Erreur: {response.text}")
    except Exception as e:
        print(f"❌ /auth/login: {e}")
    
    # Test 3: Connexion user
    try:
        login_data = {
            'username': 'user',
            'password': 'user123'
        }
        response = requests.post(
            f'{base_url}/auth/login',
            json=login_data,
            headers={'Content-Type': 'application/json'}
        )
        print(f"✅ /auth/login (user): {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Token: {data.get('token', 'N/A')[:20]}...")
            print(f"   User: {data.get('user', {}).get('username', 'N/A')}")
        else:
            print(f"   Erreur: {response.text}")
    except Exception as e:
        print(f"❌ /auth/login: {e}")

if __name__ == "__main__":
    test_auth()
