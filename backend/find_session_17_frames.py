"""
Script pour trouver les frames de la session 17
"""
import sqlite3

DB_PATH = 'sessions.db'

def find_frames_session_17():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("🔍 Recherche des frames pour la session 17")
    print()
    
    # 1. Détails de la session 17
    cursor.execute("SELECT * FROM sessions WHERE id = 17")
    session = cursor.fetchone()
    cursor.execute("PRAGMA table_info(sessions)")
    columns = [col[1] for col in cursor.fetchall()]
    
    session_data = dict(zip(columns, session))
    print("📋 Session 17:")
    print(f"  ID: {session_data['id']}")
    print(f"  User ID: {session_data['user_id']}")
    print(f"  Start: {session_data['start_time']}")
    print(f"  End: {session_data['end_time']}")
    print(f"  Duration: {session_data['duration']}s")
    print(f"  Awake: {session_data['awake_count']}")
    print(f"  Drowsy: {session_data['drowsy_count']}")
    print(f"  client_session_id: {session_data['client_session_id']}")
    print()
    
    # 2. Chercher des frames dans la plage de temps
    start_time = session_data['start_time']
    end_time = session_data['end_time']
    
    print(f"🔍 Recherche de frames entre {start_time} et {end_time}")
    
    # Convertir les timestamps ISO en epoch
    from datetime import datetime
    start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
    end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
    start_epoch = start_dt.timestamp()
    end_epoch = end_dt.timestamp()
    
    print(f"  Epoch: {start_epoch} - {end_epoch}")
    print()
    
    # Chercher toutes les frames dans cette plage
    cursor.execute("""
        SELECT id, session_id, client_session_id, timestamp, prediction, confidence, frame_number
        FROM session_frames 
        WHERE timestamp BETWEEN ? AND ?
        ORDER BY timestamp
    """, (start_epoch, end_epoch))
    
    frames_in_timerange = cursor.fetchall()
    print(f"📊 Frames trouvées dans la plage de temps: {len(frames_in_timerange)}")
    
    if frames_in_timerange:
        print("\n📋 Détails des frames:")
        for frame in frames_in_timerange[:10]:
            print(f"  Frame {frame[0]}:")
            print(f"    session_id: {frame[1]}")
            print(f"    client_session_id: {frame[2]}")
            print(f"    timestamp: {frame[3]} ({datetime.fromtimestamp(frame[3])})")
            print(f"    prediction: {frame[4]}")
            print(f"    frame_number: {frame[6]}")
            print()
        
        # Vérifier les client_session_id uniques
        unique_client_ids = set(f[2] for f in frames_in_timerange if f[2])
        print(f"🔍 client_session_id uniques dans cette plage: {len(unique_client_ids)}")
        for cid in unique_client_ids:
            count = sum(1 for f in frames_in_timerange if f[2] == cid)
            print(f"  {cid}: {count} frames")
        print()
        
        # Proposition de correction
        if len(unique_client_ids) == 1:
            correct_client_id = list(unique_client_ids)[0]
            print(f"💡 Suggestion: Mapper les frames avec client_session_id={correct_client_id} vers session_id=17")
            
            response = input("\n❓ Voulez-vous effectuer ce mappage ? (oui/non): ")
            if response.lower() in ['oui', 'o', 'yes', 'y']:
                cursor.execute("""
                    UPDATE session_frames
                    SET session_id = 17
                    WHERE client_session_id = ?
                """, (correct_client_id,))
                conn.commit()
                
                # Vérifier
                cursor.execute("SELECT COUNT(*) FROM session_frames WHERE session_id = 17")
                count = cursor.fetchone()[0]
                print(f"✅ {count} frames maintenant liées à la session 17")
    else:
        print("❌ Aucune frame trouvée dans cette plage de temps")
        print()
        print("🔍 Recherche de frames avec le client_session_id exact:")
        cursor.execute("""
            SELECT id, session_id, client_session_id, timestamp, prediction, frame_number
            FROM session_frames
            WHERE client_session_id = ?
        """, (session_data['client_session_id'],))
        frames = cursor.fetchall()
        print(f"  Trouvées: {len(frames)}")
    
    conn.close()

if __name__ == '__main__':
    find_frames_session_17()
