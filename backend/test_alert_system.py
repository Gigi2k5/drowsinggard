"""
Script de diagnostic pour tester la détection de somnolence
"""
import base64
import requests
import json

API_URL = "http://localhost:5000"

def test_prediction():
    """Tester une prédiction avec une image de test"""
    print("=" * 60)
    print("🧪 TEST DE DÉTECTION DE SOMNOLENCE")
    print("=" * 60)
    print()
    
    # Créer une petite image de test (1x1 pixel noir en base64)
    test_image = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCwAA//2Q=="
    
    print("📊 Configuration actuelle:")
    print(f"  Threshold: 0.65 (65%)")
    print(f"  Buffer size: 7 frames")
    print(f"  Alert debounce: 3 secondes (6 frames consécutives)")
    print()
    
    print("🔍 Simulation de détection...")
    
    # Test avec différents seuils pour voir le comportement
    test_cases = [
        {"threshold": 0.5, "buffer_size": 5, "name": "Sensible (50%, buffer 5)"},
        {"threshold": 0.65, "buffer_size": 7, "name": "Normal (65%, buffer 7)"},
        {"threshold": 0.75, "buffer_size": 7, "name": "Strict (75%, buffer 7)"},
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Test: {test_case['name']}")
        
        try:
            response = requests.post(
                f"{API_URL}/predict",
                json={
                    "image": test_image,
                    "threshold": test_case["threshold"],
                    "buffer_size": test_case["buffer_size"]
                },
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Prédiction: {result.get('prediction', 'N/A')}")
                print(f"   📊 Confiance: {result.get('confidence', 0)}%")
                print(f"   📊 Confiance brute: {result.get('raw_confidence', 0)}%")
                print(f"   ⚡ Latence: {result.get('latency_ms', 0)}ms")
                
                # Déterminer si une alerte serait déclenchée
                if result.get('prediction') == 'drowsy':
                    print(f"   ⚠️ ALERTE: Somnolence détectée !")
                    print(f"   💡 Note: L'alerte ne se déclenchera qu'après 6 frames consécutives")
                else:
                    print(f"   ✅ État: Éveillé")
            else:
                print(f"   ❌ Erreur HTTP {response.status_code}: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Impossible de se connecter à {API_URL}")
            print(f"   💡 Assurez-vous que le serveur backend est démarré")
            break
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
    
    print()
    print("=" * 60)
    print("📋 RÉSUMÉ DU SYSTÈME D'ALERTE")
    print("=" * 60)
    print()
    print("Le système utilise un système à 3 niveaux:")
    print()
    print("1️⃣ NIVEAU 1 - Prédiction IA (Backend)")
    print("   - Le modèle analyse chaque frame")
    print("   - Retourne une confiance brute (0-100%)")
    print("   - Applique un buffer de lissage (7 dernières frames)")
    print("   - Compare au seuil (65% par défaut)")
    print()
    print("2️⃣ NIVEAU 2 - Debounce (Frontend)")
    print("   - Compte les frames 'drowsy' consécutives")
    print("   - Nécessite 3 secondes = 6 frames consécutives")
    print("   - Évite les alertes sporadiques")
    print()
    print("3️⃣ NIVEAU 3 - Alerte Audio/Visuelle")
    print("   - Son d'alerte (si activé dans paramètres)")
    print("   - Compteur d'alertes incrémenté")
    print("   - Enregistré dans l'historique")
    print()
    print("💡 POUR TESTER:")
    print("   1. Démarrez une surveillance")
    print("   2. Fermez les yeux pendant 3+ secondes")
    print("   3. Regardez les logs console (F12)")
    print("   4. Vérifiez le compteur d'alertes")
    print()

if __name__ == '__main__':
    test_prediction()
