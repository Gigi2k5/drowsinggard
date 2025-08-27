<template>
  <div class="admin-panel">
    <div class="admin-header">
      <h1>Panel d'Administration</h1>
      <p>Gestion des utilisateurs et surveillance des sessions</p>
    </div>
    
    <!-- Liste des utilisateurs -->
    <div class="users-section">
      <div class="section-header">
        <h2>Utilisateurs</h2>
        <button @click="refreshUsers" class="btn-refresh" :disabled="loading">
          <i class="fas fa-sync-alt"></i>
          Actualiser
        </button>
      </div>
      
      <div v-if="loading" class="loading">
        <div class="spinner"></div>
        <p>Chargement des utilisateurs...</p>
      </div>
      
      <div v-else-if="users.length === 0" class="no-users">
        <i class="fas fa-users-slash"></i>
        <p>Aucun utilisateur trouvé</p>
      </div>
      
      <div v-else class="users-grid">
        <div 
          v-for="user in users" 
          :key="user.id" 
          class="user-card"
          :class="{ 'user-admin': user.role === 'admin' }"
        >
          <div class="user-header">
            <div class="user-info">
              <h3>{{ user.username }}</h3>
              <span class="user-role" :class="`role-${user.role}`">
                {{ user.role === 'admin' ? 'Administrateur' : 'Utilisateur' }}
              </span>
            </div>
            <div class="user-actions">
              <button 
                @click="viewUserSessions(user)" 
                class="btn-view-sessions"
                title="Voir les sessions"
              >
                <i class="fas fa-video"></i>
              </button>
              <button 
                v-if="user.role !== 'admin' || user.id !== 1"
                @click="deleteUser(user)" 
                class="btn-delete-user"
                title="Supprimer l'utilisateur"
              >
                <i class="fas fa-trash-alt"></i>
              </button>
            </div>
          </div>
          
          <div class="user-details">
            <div class="detail-item">
              <span class="label">Email:</span>
              <span>{{ user.email }}</span>
            </div>
            <div class="detail-item">
              <span class="label">Créé le:</span>
              <span>{{ formatDate(user.created_at) }}</span>
            </div>
            <div class="detail-item">
              <span class="label">Dernière connexion:</span>
              <span>{{ formatDate(user.last_login) || 'Jamais' }}</span>
            </div>
            <div class="detail-item">
              <span class="label">Statut:</span>
              <span :class="`status-${user.is_active ? 'active' : 'inactive'}`">
                {{ user.is_active ? 'Actif' : 'Inactif' }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Sessions d'un utilisateur (Modal) -->
    <div v-if="selectedUser" class="modal-overlay" @click="closeUserSessions">
      <div class="modal-content sessions-modal" @click.stop>
        <div class="modal-header">
          <h3>Sessions de {{ selectedUser.username }}</h3>
          <button @click="closeUserSessions" class="btn-close">
            <i class="fas fa-times"></i>
          </button>
        </div>

        <div class="modal-body">
          <div v-if="userSessionsLoading" class="loading">
            <div class="spinner"></div>
            <p>Chargement des sessions...</p>
          </div>
          
          <div v-else-if="userSessions.length === 0" class="no-sessions">
            <i class="fas fa-video-slash"></i>
            <p>Aucune session trouvée pour cet utilisateur</p>
          </div>
          
          <div v-else class="sessions-grid">
            <div 
              v-for="session in userSessions" 
              :key="session.id" 
              class="session-card"
              :class="getSessionStatusClass(session)"
            >
              <div class="session-header">
                <div class="session-info">
                  <h4>Session #{{ session.id }}</h4>
                  <span class="session-date">{{ formatDate(session.created_at) }}</span>
                </div>
                <div class="session-status">
                  <span :class="`status-${getSessionStatus(session)}`">
                    {{ getSessionStatusText(session) }}
                  </span>
                </div>
              </div>
              
              <div class="session-stats">
                <div class="stat-item">
                  <span class="stat-label">Durée:</span>
                  <span class="stat-value">{{ formatDuration(session.duration) }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">Éveillé:</span>
                  <span class="stat-value">{{ session.awake_count }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">Somnolent:</span>
                  <span class="stat-value">{{ session.drowsy_count }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">Alertes:</span>
                  <span class="stat-value">{{ session.alert_count }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">Confiance:</span>
                  <span class="stat-value">{{ Math.round(session.avg_confidence) }}%</span>
                </div>
              </div>
              
              <div class="session-actions">
                <button @click="viewSessionVideo(session)" class="btn-view-video">
                  <i class="fas fa-video"></i>
                  Voir la vidéo
                </button>
                <button @click="exportSessionData(session)" class="btn-export-data">
                  <i class="fas fa-download"></i>
                  Exporter
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Modal de visionnage vidéo -->
    <div v-if="selectedVideoSession" class="modal-overlay" @click="closeVideoModal">
      <div class="modal-content video-modal" @click.stop>
        <div class="modal-header">
          <h3>Visionnage de la Session #{{ selectedVideoSession.id }}</h3>
          <button @click="closeVideoModal" class="btn-close">
            <i class="fas fa-times"></i>
          </button>
        </div>
        
        <div class="modal-body">
          <div v-if="videoLoading" class="video-loading">
            <div class="spinner"></div>
            <p>Chargement de la vidéo...</p>
          </div>
          
          <div v-else-if="videoError" class="video-error">
            <i class="fas fa-exclamation-triangle"></i>
            <h4>Erreur de chargement</h4>
            <p>{{ videoError }}</p>
          </div>
          
          <div v-else-if="sessionFrames.length > 0" class="video-player">
            <div class="video-controls">
              <button @click="playVideo" :disabled="isPlaying" class="btn-control">
                <i class="fas fa-play"></i>
                Lecture
              </button>
              <button @click="pauseVideo" :disabled="!isPlaying" class="btn-control">
                <i class="fas fa-pause"></i>
                Pause
              </button>
              <button @click="stopVideo" class="btn-control">
                <i class="fas fa-stop"></i>
                Stop
              </button>
              <div class="progress-container">
                <input 
                  type="range" 
                  v-model="currentFrameIndex" 
                  :min="0" 
                  :max="sessionFrames.length - 1" 
                  class="progress-bar"
                  @input="seekToFrame"
                />
                <span class="progress-text">
                  Frame {{ currentFrameIndex + 1 }} / {{ sessionFrames.length }}
                </span>
              </div>
            </div>
            
            <div class="video-display">
              <img 
                :src="currentFrameImage" 
                :alt="`Frame ${currentFrameIndex + 1}`"
                class="frame-image"
              />
              <div class="frame-info">
                <div class="info-item">
                  <span class="label">Prédiction :</span>
                  <span :class="`prediction-${currentFrame.prediction}`">
                    {{ currentFrame.prediction }}
                  </span>
                </div>
                <div class="info-item">
                  <span class="label">Confiance :</span>
                  <span>{{ Math.round(currentFrame.confidence) }}%</span>
                </div>
                <div class="info-item">
                  <span class="label">Timestamp :</span>
                  <span>{{ formatTimestamp(currentFrame.timestamp) }}</span>
                </div>
              </div>
            </div>
          </div>
          
          <div v-else class="no-frames">
            <i class="fas fa-video-slash"></i>
            <h4>Aucune frame disponible</h4>
            <p>Cette session ne contient pas de frames vidéo enregistrées.</p>
          </div>
        </div>
        
        <div class="modal-footer">
          <button @click="exportSessionVideo" class="btn-export-video" :disabled="sessionFrames.length === 0 || exportingVideo">
            <i class="fas fa-download"></i>
            {{ exportingVideo ? 'Export en cours...' : 'Exporter la vidéo' }}
          </button>
          <button @click="closeVideoModal" class="btn-secondary">Fermer</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { api } from '../services/api'

export default {
  name: 'AdminPanel',
  setup() {
    const users = ref([])
    const loading = ref(false)
    const selectedUser = ref(null)
    const userSessions = ref([])
    const userSessionsLoading = ref(false)
    
    // État de la vidéo
    const selectedVideoSession = ref(null)
    const sessionFrames = ref([])
    const videoLoading = ref(false)
    const videoError = ref(null)
    const isPlaying = ref(false)
    const currentFrameIndex = ref(0)
    const playInterval = ref(null)
    const exportingVideo = ref(false)
    
    // Computed properties pour la vidéo
    const currentFrame = computed(() => {
      if (sessionFrames.value.length === 0) return null
      return sessionFrames.value[currentFrameIndex.value] || sessionFrames.value[0]
    })
    
    const currentFrameImage = computed(() => {
      if (!currentFrame.value) return ''
      return currentFrame.value.frame_data
    })
    
    // Méthodes
    async function loadUsers() {
      loading.value = true
      try {
        const response = await api.request('/admin/users')
        // Masquer les comptes admin de la liste
        users.value = (response.users || []).filter(u => u.role !== 'admin')
      } catch (error) {
        console.error('Erreur chargement utilisateurs:', error)
        users.value = []
      } finally {
        loading.value = false
      }
    }
    
    async function refreshUsers() {
      await loadUsers()
    }
    
    async function viewUserSessions(user) {
      selectedUser.value = user
      userSessionsLoading.value = true
      userSessions.value = []
      
      try {
        const response = await api.request(`/admin/users/${user.id}/sessions`)
        userSessions.value = response.sessions || []
      } catch (error) {
        console.error('Erreur chargement sessions utilisateur:', error)
        userSessions.value = []
      } finally {
        userSessionsLoading.value = false
      }
    }
    
    function closeUserSessions() {
      selectedUser.value = null
      userSessions.value = []
    }
    
    async function deleteUser(user) {
      if (!confirm(`Êtes-vous sûr de vouloir supprimer l'utilisateur ${user.username} ?`)) {
        return
      }
      
      try {
        await api.request(`/admin/users/${user.id}`, { method: 'DELETE' })
        await loadUsers()
        
        if (selectedUser.value && selectedUser.value.id === user.id) {
          closeUserSessions()
        }
      } catch (error) {
        console.error('Erreur suppression utilisateur:', error)
        alert('Erreur lors de la suppression de l\'utilisateur')
      }
    }
    
    // Méthodes pour la vidéo
    async function viewSessionVideo(session) {
      selectedVideoSession.value = session
      videoLoading.value = true
      videoError.value = null
      sessionFrames.value = []
      currentFrameIndex.value = 0
      
      try {
        const response = await api.request(`/get_session_frames/${session.id}`)
        if (response.success) {
          sessionFrames.value = response.frames || []
        } else {
          videoError.value = response.error || 'Erreur lors du chargement des frames'
        }
      } catch (error) {
        console.error('❌ Erreur chargement frames:', error)
        videoError.value = 'Impossible de charger les frames de la session'
      } finally {
        videoLoading.value = false
      }
    }
    
    function closeVideoModal() {
      stopVideo()
      selectedVideoSession.value = null
      sessionFrames.value = []
      videoError.value = null
      currentFrameIndex.value = 0
    }
    
    function playVideo() {
      if (sessionFrames.value.length === 0) return
      
      isPlaying.value = true
      playInterval.value = setInterval(() => {
        if (currentFrameIndex.value < sessionFrames.value.length - 1) {
          currentFrameIndex.value++
        } else {
          stopVideo()
        }
      }, 100)
    }
    
    function pauseVideo() {
      isPlaying.value = false
      if (playInterval.value) {
        clearInterval(playInterval.value)
        playInterval.value = null
      }
    }
    
    function stopVideo() {
      isPlaying.value = false
      if (playInterval.value) {
        clearInterval(playInterval.value)
        playInterval.value = null
      }
      currentFrameIndex.value = 0
    }
    
    function seekToFrame() {
      // La fonction est automatiquement appelée par v-model sur le slider
    }
    
    async function exportSessionVideo() {
      try {
        if (!selectedVideoSession.value || sessionFrames.value.length === 0) {
          alert('Aucune frame à exporter pour cette session')
          return
        }
        exportingVideo.value = true
        const fps = 10
        const frameDuration = Math.round(1000 / fps)
        
        // Charger la première image pour initialiser le canvas
        const firstImg = new Image()
        firstImg.src = sessionFrames.value[0].frame_data
        await new Promise((resolve, reject) => {
          firstImg.onload = resolve
          firstImg.onerror = reject
        })
        const width = firstImg.naturalWidth || 640
        const height = firstImg.naturalHeight || 480
        
        const canvas = document.createElement('canvas')
        canvas.width = width
        canvas.height = height
        const ctx = canvas.getContext('2d')
        
        const stream = canvas.captureStream(fps)
        const mimeType = MediaRecorder.isTypeSupported('video/webm;codecs=vp9') ? 'video/webm;codecs=vp9' : 'video/webm'
        const recorder = new MediaRecorder(stream, { mimeType })
        const chunks = []
        recorder.ondataavailable = e => { if (e.data && e.data.size > 0) chunks.push(e.data) }
        const stopped = new Promise(resolve => { recorder.onstop = resolve })
        recorder.start()
        
        // Dessiner les frames à la cadence voulue
        for (let i = 0; i < sessionFrames.value.length; i++) {
          const img = new Image()
          img.src = sessionFrames.value[i].frame_data
          await new Promise((resolve, reject) => {
            img.onload = resolve
            img.onerror = reject
          })
          ctx.drawImage(img, 0, 0, width, height)
          await new Promise(resolve => setTimeout(resolve, frameDuration))
        }
        
        recorder.stop()
        await stopped
        
        const blob = new Blob(chunks, { type: 'video/webm' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `session_${selectedVideoSession.value.id}.webm`
        document.body.appendChild(a)
        a.click()
        setTimeout(() => {
          URL.revokeObjectURL(url)
          document.body.removeChild(a)
        }, 0)
      } catch (err) {
        console.error('❌ Erreur export vidéo:', err)
        alert("Erreur lors de l'export de la vidéo. Consultez la console.")
      } finally {
        exportingVideo.value = false
      }
    }
    
    function exportSessionData(session) {
      const csvContent = [
        ['ID', 'Date création', 'Début', 'Fin', 'Durée (s)', 'Éveillé', 'Somnolent', 'Alertes', 'Confiance moyenne'],
        [
          session.id,
          session.created_at,
          session.start_time,
          session.end_time,
          session.duration,
          session.awake_count,
          session.drowsy_count,
          session.alert_count,
          session.avg_confidence
        ]
      ].map(row => row.map(cell => `"${cell || ''}"`).join(',')).join('\n')
      
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `session_${session.id}_${selectedUser.value.username}.csv`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    }
    
    // Fonctions utilitaires
    function formatDate(dateString) {
      if (!dateString) return 'N/A'
      const date = new Date(dateString)
      return date.toLocaleDateString('fr-FR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    }
    
    function formatDuration(seconds) {
      if (!seconds) return '00:00'
      const hours = Math.floor(seconds / 3600)
      const minutes = Math.floor((seconds % 3600) / 60)
      const secs = seconds % 60
      
      if (hours > 0) {
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
      }
      return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    }
    
    function getSessionStatus(session) {
      if (session.end_time && session.start_time) {
        return 'completed'
      }
      return 'interrupted'
    }
    
    function getSessionStatusClass(session) {
      const status = getSessionStatus(session)
      return `status-${status}`
    }
    
    function getSessionStatusText(session) {
      const status = getSessionStatus(session)
      switch (status) {
        case 'completed': return 'Terminée'
        case 'interrupted': return 'Interrompue'
        default: return 'Inconnu'
      }
    }
    
    function formatTimestamp(timestamp) {
      if (!timestamp) return 'N/A'
      const date = new Date(timestamp * 1000)
      return date.toLocaleTimeString('fr-FR', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
    }
    
    // Lifecycle
    onMounted(() => {
      loadUsers()
    })
    
    return {
      users,
      loading,
      selectedUser,
      userSessions,
      userSessionsLoading,
      selectedVideoSession,
      sessionFrames,
      videoLoading,
      videoError,
      isPlaying,
      currentFrameIndex,
      exportingVideo,
      currentFrame,
      currentFrameImage,
      loadUsers,
      refreshUsers,
      viewUserSessions,
      closeUserSessions,
      deleteUser,
      viewSessionVideo,
      closeVideoModal,
      playVideo,
      pauseVideo,
      stopVideo,
      seekToFrame,
      exportSessionVideo,
      exportSessionData,
      formatDate,
      formatDuration,
      getSessionStatus,
      getSessionStatusClass,
      getSessionStatusText,
      formatTimestamp
    }
  }
}
</script>

<style scoped>
.admin-panel {
  padding: 2rem 0;
}

.admin-header {
  text-align: center;
  margin-bottom: 3rem;
}

.admin-header h1 {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  background: linear-gradient(135deg, #ffffff, #e5e7eb);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.admin-header p {
  font-size: 1.125rem;
  color: #9ca3af;
}

/* Section utilisateurs */
.users-section {
  background: linear-gradient(135deg, #1a1f2e, #252a3a);
  border-radius: 16px;
  padding: 2rem;
  border: 1px solid #374151;
  margin-bottom: 2rem;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.section-header h2 {
  color: #ffffff;
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
}

.btn-refresh {
  background: linear-gradient(135deg, #4f9eff, #60a5fa);
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.btn-refresh:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(79, 158, 255, 0.3);
}

.btn-refresh:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.loading, .no-users, .no-sessions {
  text-align: center;
  padding: 3rem;
  color: #9ca3af;
}

.spinner {
  border: 3px solid #374151;
  border-top: 3px solid #4f9eff;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.users-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 1.5rem;
}

.user-card {
  background: linear-gradient(135deg, #0f1419, #1a1f2e);
  border-radius: 12px;
  padding: 1.5rem;
  border: 1px solid #374151;
  transition: all 0.3s ease;
}

.user-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
}

.user-card.user-admin {
  border-left: 4px solid #f59e0b;
}

.user-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.user-info h3 {
  color: #ffffff;
  margin: 0 0 0.5rem 0;
  font-size: 1.25rem;
}

.user-role {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.role-admin {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
}

.role-user {
  background: rgba(79, 158, 255, 0.1);
  color: #4f9eff;
}

.user-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-view-sessions, .btn-delete-user {
  background: none;
  border: 1px solid #374151;
  color: #9ca3af;
  padding: 0.5rem;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-view-sessions:hover {
  border-color: #4f9eff;
  color: #4f9eff;
}

.btn-delete-user:hover {
  border-color: #ef4444;
  color: #ef4444;
}

.user-details {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.detail-item .label {
  color: #9ca3af;
  font-size: 0.875rem;
}

.detail-item span:last-child {
  color: #d1d5db;
  font-size: 0.875rem;
}

.status-active {
  color: #4ade80;
}

.status-inactive {
  color: #ef4444;
}

/* Section sessions utilisateur */
.user-sessions-section {
  background: linear-gradient(135deg, #1a1f2e, #252a3a);
  border-radius: 16px;
  padding: 2rem;
  border: 1px solid #374151;
  margin-bottom: 2rem;
}

.btn-close-sessions {
  background: linear-gradient(135deg, #6b7280, #9ca3af);
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.btn-close-sessions:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(107, 114, 128, 0.3);
}

.sessions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 1.25rem;
}

.session-card {
  background: linear-gradient(135deg, #0f1419, #1a1f2e);
  border-radius: 12px;
  padding: 1.5rem;
  border: 1px solid #374151;
  transition: all 0.3s ease;
}

.session-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
}

.session-card.status-completed {
  border-left: 4px solid #4ade80;
}

.session-card.status-interrupted {
  border-left: 4px solid #f59e0b;
}

.session-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.session-info h4 {
  color: #ffffff;
  margin: 0 0 0.5rem 0;
  font-size: 1.125rem;
}

.session-date {
  color: #9ca3af;
  font-size: 0.875rem;
}

.session-status {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.status-completed {
  background: rgba(74, 222, 128, 0.1);
  color: #4ade80;
}

.status-interrupted {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
}

.session-stats {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-label {
  color: #9ca3af;
  font-size: 0.875rem;
}

.stat-value {
  color: #d1d5db;
  font-weight: 600;
  font-size: 0.875rem;
}

.session-actions {
  display: flex;
  gap: 0.75rem;
}

.btn-view-video, .btn-export-data {
  flex: 1;
  background: linear-gradient(135deg, #4f9eff, #60a5fa);
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.btn-view-video:hover, .btn-export-data:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(79, 158, 255, 0.3);
}

/* Modal vidéo */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: linear-gradient(135deg, #1a1f2e, #252a3a);
  border-radius: 16px;
  border: 1px solid #374151;
  width: 90%;
  max-width: 900px;
  max-height: 90vh;
  overflow-y: auto;
}

.sessions-modal { max-width: 1100px; width: 95%; }

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #374151;
}

.modal-header h3 {
  margin: 0;
  color: #ffffff;
  font-size: 1.25rem;
  font-weight: 600;
}

.btn-close {
  background: none;
  border: none;
  color: #9ca3af;
  font-size: 1.25rem;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.btn-close:hover {
  color: #ffffff;
  background: rgba(255, 255, 255, 0.1);
}

.modal-body {
  padding: 1.5rem;
}

.video-loading, .video-error, .no-frames {
  text-align: center;
  padding: 3rem;
  color: #9ca3af;
}

.video-error {
  color: #fca5a5;
}

.video-player {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.video-controls {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.btn-control {
  background: linear-gradient(135deg, #4f9eff, #60a5fa);
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-control:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(79, 158, 255, 0.3);
}

.btn-control:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.progress-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.progress-bar {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: #374151;
  outline: none;
  cursor: pointer;
}

.progress-bar::-webkit-slider-thumb {
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #4f9eff;
  cursor: pointer;
}

.progress-text {
  color: #9ca3af;
  font-size: 0.875rem;
  text-align: center;
}

.video-display {
  display: flex;
  gap: 1.5rem;
  align-items: flex-start;
}

.frame-image {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
  border: 1px solid #374151;
}

.frame-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: rgba(15, 20, 25, 0.5);
  border-radius: 6px;
  border: 1px solid #374151;
}

.info-item .label {
  color: #9ca3af;
  font-size: 0.875rem;
}

.prediction-awake {
  color: #4ade80;
  font-weight: 600;
}

.prediction-drowsy {
  color: #ef4444;
  font-weight: 600;
}

.modal-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-top: 1px solid #374151;
  gap: 1rem;
}

.btn-export-video, .btn-secondary {
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  border: none;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.btn-export-video {
  background: linear-gradient(135deg, #4ade80, #22c55e);
  color: white;
}

.btn-export-video:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(74, 222, 128, 0.3);
}

.btn-export-video:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background: linear-gradient(135deg, #6b7280, #9ca3af);
  color: white;
}

.btn-secondary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(107, 114, 128, 0.3);
}
</style>
