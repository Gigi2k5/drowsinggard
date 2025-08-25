import requests
import json
import time

# URL de base du backend
BASE_URL = "http://localhost:5000"

def test_save_session():
    """Test de l'endpoint /save_session"""
    
    # Données de test pour une session
    session_data = {
        "start_time": "2025-08-25T18:00:00.000Z",
        "end_time": "2025-08-25T18:05:00.000Z",
        "duration": 300,  # 5 minutes
        "awake_count": 180,  # 60% du temps
        "drowsy_count": 90,  # 30% du temps
        "alert_count": 5,  # 5 alertes
        "avg_confidence": 78.5
    }
    
    try:
        print("🧪 Test de sauvegarde de session...")
        print(f"📤 Données envoyées: {json.dumps(session_data, indent=2)}")
        
        # Appel à l'endpoint /save_session
        response = requests.post(
            f"{BASE_URL}/save_session",
            json=session_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"📥 Réponse reçue: {response.status_code}")
        print(f"📋 Contenu: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ Session sauvegardée avec succès!")
                return True
            else:
                print(f"❌ Erreur: {result.get('error', 'Erreur inconnue')}")
                return False
        else:
            print(f"❌ Erreur HTTP: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Impossible de se connecter au backend. Assurez-vous qu'il est démarré sur http://localhost:5000")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return False

def test_get_sessions():
    """Test de l'endpoint /get_sessions"""
    
    try:
        print("\n🧪 Test de récupération des sessions...")
        
        # Appel à l'endpoint /get_sessions
        response = requests.get(f"{BASE_URL}/get_sessions?limit=10")
        
        print(f"📥 Réponse reçue: {response.status_code}")
        print(f"📋 Contenu: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                sessions = result.get("sessions", [])
                print(f"✅ {len(sessions)} sessions récupérées")
                for session in sessions:
                    print(f"   - Session #{session['id']}: {session['duration']}s, {session['alert_count']} alertes")
                return True
            else:
                print(f"❌ Erreur: {result.get('error', 'Erreur inconnue')}")
                return False
        else:
            print(f"❌ Erreur HTTP: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Impossible de se connecter au backend")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Test des endpoints de session")
    print("=" * 50)
    
    # Test de sauvegarde
    if test_save_session():
        print("\n" + "=" * 50)
        # Test de récupération
        test_get_sessions()
    
    print("\n🏁 Test terminé")
