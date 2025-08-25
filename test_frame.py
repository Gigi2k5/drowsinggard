import requests
import json
import base64
import time

# URL de base du backend
BASE_URL = "http://localhost:5000"

def test_save_frame():
    """Test de l'endpoint /save_frame"""
    
    # Créer d'abord une session
    session_data = {
        "start_time": "2025-08-25T18:00:00.000Z",
        "end_time": "2025-08-25T18:01:00.000Z",
        "duration": 60,  # 1 minute
        "awake_count": 36,  # 60% du temps
        "drowsy_count": 18,  # 30% du temps
        "alert_count": 2,  # 2 alertes
        "avg_confidence": 75.0
    }
    
    try:
        print("🧪 Test de création de session...")
        response = requests.post(
            f"{BASE_URL}/save_session",
            json=session_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            print(f"❌ Erreur création session: {response.status_code}")
            return None
            
        session_result = response.json()
        if not session_result.get("success"):
            print(f"❌ Erreur création session: {session_result.get('error')}")
            return None
            
        print("✅ Session créée avec succès")
        
        # Récupérer l'ID de la session créée
        sessions_response = requests.get(f"{BASE_URL}/get_sessions?limit=1")
        if sessions_response.status_code == 200:
            sessions_data = sessions_response.json()
            if sessions_data.get("success") and sessions_data.get("sessions"):
                session_id = sessions_data["sessions"][0]["id"]
                print(f"📋 Session ID récupéré: {session_id}")
                return session_id
        
        print("❌ Impossible de récupérer l'ID de session")
        return None
        
    except Exception as e:
        print(f"❌ Erreur création session: {e}")
        return None

def test_save_frame_endpoint(session_id):
    """Test de l'endpoint /save_frame"""
    
    # Créer une image de test (base64)
    test_image = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k="
    
    frame_data = {
        "session_id": session_id,
        "frame_data": test_image,
        "timestamp": time.time(),
        "prediction": "awake",
        "confidence": 85.5,
        "frame_number": 1
    }
    
    try:
        print(f"\n🧪 Test de sauvegarde de frame pour la session {session_id}...")
        print(f"📤 Données envoyées: {json.dumps({**frame_data, 'frame_data': '[BASE64_IMAGE]'}, indent=2)}")
        
        response = requests.post(
            f"{BASE_URL}/save_frame",
            json= frame_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"📥 Réponse reçue: {response.status_code}")
        print(f"📋 Contenu: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ Frame sauvegardée avec succès!")
                return True
            else:
                print(f"❌ Erreur: {result.get('error', 'Erreur inconnue')}")
                return False
        else:
            print(f"❌ Erreur HTTP: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return False

def test_get_session_frames(session_id):
    """Test de l'endpoint /get_session_frames"""
    
    try:
        print(f"\n🧪 Test de récupération des frames pour la session {session_id}...")
        
        response = requests.get(f"{BASE_URL}/get_session_frames/{session_id}")
        
        print(f"📥 Réponse reçue: {response.status_code}")
        print(f"📋 Contenu: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                frames = result.get("frames", [])
                print(f"✅ {len(frames)} frames récupérées")
                for i, frame in enumerate(frames):
                    print(f"   - Frame {i+1}: {frame['prediction']} ({frame['confidence']}%)")
                return True
            else:
                print(f"❌ Erreur: {result.get('error', 'Erreur inconnue')}")
                return False
        else:
            print(f"❌ Erreur HTTP: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Test des endpoints de frames")
    print("=" * 50)
    
    # Test de création de session
    session_id = test_save_frame()
    
    if session_id:
        # Test de sauvegarde de frame
        if test_save_frame_endpoint(session_id):
            # Test de récupération des frames
            test_get_session_frames(session_id)
    
    print("\n🏁 Test terminé")
