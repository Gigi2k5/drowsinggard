"""
Script pour corriger toutes les frames dont session_id contient un timestamp au lieu d'un ID
"""
import sqlite3
from datetime import datetime

DB_PATH = 'sessions.db'

def fix_all_frames():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("=" * 60)
    print("🔧 CORRECTION DES session_id INCORRECTS")
    print("=" * 60)
    print()
    
    # 1. Récupérer toutes les sessions avec leur client_session_id
    cursor.execute("""
        SELECT id, client_session_id, start_time, end_time
        FROM sessions
        WHERE client_session_id IS NOT NULL
        ORDER BY id
    """)
    sessions = cursor.fetchall()
    
    print(f"📊 {len(sessions)} sessions trouvées avec client_session_id")
    print()
    
    total_fixed = 0
    
    for session in sessions:
        session_id, client_sid, start_time, end_time = session
        
        # Vérifier si client_session_id ressemble à un timestamp (uniquement des chiffres)
        if client_sid and client_sid.isdigit():
            # C'est un timestamp - chercher les frames qui ont ce timestamp comme session_id
            cursor.execute("""
                SELECT COUNT(*)
                FROM session_frames
                WHERE session_id = ?
            """, (int(client_sid),))
            
            count_wrong = cursor.fetchone()[0]
            
            if count_wrong > 0:
                print(f"🔧 Session {session_id} (client_session_id={client_sid}):")
                print(f"   {count_wrong} frames avec session_id={client_sid} (devrait être {session_id})")
                
                # Corriger
                cursor.execute("""
                    UPDATE session_frames
                    SET session_id = ?
                    WHERE session_id = ?
                """, (session_id, int(client_sid)))
                
                print(f"   ✅ Corrigées")
                total_fixed += count_wrong
                print()
    
    conn.commit()
    
    print("=" * 60)
    print(f"✅ TOTAL: {total_fixed} frames corrigées")
    print("=" * 60)
    print()
    
    # Vérification finale
    print("📊 Vérification finale:")
    
    # Frames orphelines
    cursor.execute("""
        SELECT COUNT(*)
        FROM session_frames
        WHERE session_id IS NULL OR session_id = 0
    """)
    orphan_count = cursor.fetchone()[0]
    print(f"  Frames orphelines (session_id NULL ou 0): {orphan_count}")
    
    # Frames avec session_id > 1000 (probablement des timestamps)
    cursor.execute("""
        SELECT COUNT(*)
        FROM session_frames
        WHERE session_id > 1000
    """)
    suspicious_count = cursor.fetchone()[0]
    print(f"  Frames avec session_id > 1000 (suspicious): {suspicious_count}")
    
    # Distribution par session
    cursor.execute("""
        SELECT session_id, COUNT(*) as count
        FROM session_frames
        WHERE session_id IS NOT NULL
        GROUP BY session_id
        ORDER BY session_id
    """)
    distribution = cursor.fetchall()
    print(f"\n📈 Distribution des frames par session:")
    for sid, count in distribution[:20]:
        print(f"  Session {sid}: {count} frames")
    
    conn.close()

if __name__ == '__main__':
    print("⚠️  Ce script va corriger les session_id incorrects dans la table session_frames")
    print()
    response = input("Continuer ? (oui/non): ")
    
    if response.lower() in ['oui', 'o', 'yes', 'y']:
        fix_all_frames()
    else:
        print("❌ Opération annulée")
