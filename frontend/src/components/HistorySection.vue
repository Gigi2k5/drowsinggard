<template>
  <div class="history-section">
    <!-- En-tête de la section -->
    <header class="history-header">
      <h1>Historique des Sessions</h1>
      <p>Consultez et gérez vos sessions de surveillance</p>
    </header>

    <!-- Filtres et contrôles -->
    <div class="history-controls">
      <div class="filters-row">
        <div class="filter-group">
          <label for="dateFilter">Période :</label>
          <select id="dateFilter" v-model="dateFilter" @change="loadSessions">
            <option value="1">Dernières 24h</option>
            <option value="7">7 derniers jours</option>
            <option value="30">30 derniers jours</option>
            <option value="90">3 derniers mois</option>
            <option value="all">Tout l'historique</option>
          </select>
        </div>

        <div class="filter-group">
          <label for="statusFilter">Statut :</label>
          <select id="statusFilter" v-model="statusFilter" @change="loadSessions">
            <option value="all">Tous les statuts</option>
            <option value="completed">Terminées</option>
            <option value="interrupted">Interrompues</option>
          </select>
        </div>

        <div class="filter-group">
          <label for="limitFilter">Affichage :</label>
          <select id="limitFilter" v-model="limitFilter" @change="loadSessions">
            <option value="20">20 sessions</option>
            <option value="50">50 sessions</option>
            <option value="100">100 sessions</option>
          </select>
        </div>
      </div>

      <div class="actions-row">
        <button @click="loadSessions" class="btn-refresh" :disabled="loading">
          <i class="fas fa-sync-alt" :class="{ 'fa-spin': loading }"></i>
          Actualiser
        </button>
        
        <button @click="exportHistory" class="btn-export" :disabled="sessions.length === 0">
          <i class="fas fa-download"></i>
          Exporter
        </button>
        
        <button @click="clearAllSessions" class="btn-clear" :disabled="sessions.length === 0">
          <i class="fas fa-trash-alt"></i>
          Tout effacer
        </button>
      </div>
    </div>

    <!-- Statistiques globales -->
    <div class="stats-overview" v-if="sessions.length > 0">
      <div class="stat-item">
        <div class="stat-number">{{ totalSessions }}</div>
        <div class="stat-label">Sessions totales</div>
      </div>
      <div class="stat-item">
        <div class="stat-number">{{ totalDuration }}</div>
        <div class="stat-label">Temps total</div>
      </div>
      <div class="stat-item">
        <div class="stat-number">{{ totalAlerts }}</div>
        <div class="stat-label">Alertes totales</div>
      </div>
      <div class="stat-item">
        <div class="stat-number">{{ avgConfidence }}%</div>
        <div class="stat-label">Confiance moyenne</div>
      </div>
    </div>

    <!-- Liste des sessions -->
    <div class="sessions-container">
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>Chargement de l'historique...</p>
      </div>

      <div v-else-if="sessions.length === 0" class="empty-state">
        <i class="fas fa-history"></i>
        <h3>Aucune session enregistrée</h3>
        <p>Commencez une session de surveillance pour voir apparaître l'historique</p>
      </div>

      <div v-else class="sessions-grid">
        <div 
          v-for="session in filteredSessions" 
          :key="session.id" 
          class="session-card"
          :class="getSessionStatusClass(session)"
        >
          <!-- En-tête de la session -->
          <div class="session-header">
            <div class="session-info">
              <div class="session-date">
                <i class="fas fa-calendar-alt"></i>
                {{ formatDate(session.created_at) }}
              </div>
              <div class="session-time">
                <i class="fas fa-clock"></i>
                {{ formatTime(session.created_at) }}
              </div>
            </div>
            <div class="session-status" :class="getSessionStatusClass(session)">
              {{ getSessionStatusText(session) }}
            </div>
          </div>

          <!-- Détails de la session -->
          <div class="session-details">
            <div class="detail-row">
              <span>Début :</span>
              <span>{{ formatDateTime(session.start_time) }}</span>
            </div>
            <div class="detail-row">
              <span>Fin :</span>
              <span>{{ formatDateTime(session.end_time) }}</span>
            </div>
            <div class="detail-row">
              <span>Durée :</span>
              <span class="duration">{{ formatDuration(session.duration) }}</span>
            </div>
          </div>

          <!-- Statistiques de détection -->
          <div class="detection-stats">
            <div class="stat-row">
              <div class="stat-item-detection">
                <div class="stat-icon awake">
                  <i class="fas fa-eye"></i>
                </div>
                <div class="stat-content">
                  <div class="stat-value">{{ session.awake_count }}</div>
                  <div class="stat-label">Éveillé</div>
                </div>
              </div>
              
              <div class="stat-item-detection">
                <div class="stat-icon drowsy">
                  <i class="fas fa-eye-slash"></i>
                </div>
                <div class="stat-content">
                  <div class="stat-value">{{ session.drowsy_count }}</div>
                  <div class="stat-label">Somnolent</div>
                </div>
              </div>
              
              <div class="stat-item-detection">
                <div class="stat-icon alert">
                  <i class="fas fa-exclamation-triangle"></i>
                </div>
                <div class="stat-content">
                  <div class="stat-value">{{ session.alert_count }}</div>
                  <div class="stat-label">Alertes</div>
                </div>
              </div>
            </div>
            
            <div class="confidence-bar">
              <div class="confidence-label">Confiance moyenne</div>
              <div class="confidence-progress">
                <div 
                  class="confidence-fill" 
                  :style="{ width: `${session.avg_confidence}%` }"
                  :class="getConfidenceClass(session.avg_confidence)"
                ></div>
              </div>
              <div class="confidence-value">{{ Math.round(session.avg_confidence) }}%</div>
            </div>
          </div>

          <!-- Actions -->
          <div class="session-actions">
            <button @click="viewSessionDetails(session)" class="btn-action btn-view">
              <i class="fas fa-eye"></i>
              Détails
            </button>
            
            <button @click="viewSessionVideo(session)" class="btn-action btn-video">
              <i class="fas fa-play"></i>
              Vidéo
            </button>
            
            <button @click="deleteSession(session.id)" class="btn-action btn-delete">
              <i class="fas fa-trash-alt"></i>
              Supprimer
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Pagination -->
    <div class="pagination" v-if="sessions.length > 0">
      <button 
        @click="previousPage" 
        :disabled="currentPage === 1"
        class="btn-page"
      >
        <i class="fas fa-chevron-left"></i>
        Précédent
      </button>
      
      <span class="page-info">
        Page {{ currentPage }} sur {{ totalPages }}
      </span>
      
      <button 
        @click="nextPage" 
        :disabled="currentPage >= totalPages"
        class="btn-page"
      >
        Suivant
        <i class="fas fa-chevron-right"></i>
      </button>
    </div>

    <!-- Modal de détails de session -->
    <div v-if="selectedSession" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>Détails de la Session</h3>
          <button @click="closeModal" class="btn-close">
            <i class="fas fa-times"></i>
          </button>
        </div>
        
        <div class="modal-body">
          <div class="session-detail-grid">
            <div class="detail-section">
              <h4>Informations générales</h4>
              <div class="detail-item">
                <span class="label">ID Session :</span>
                <span class="value">#{{ selectedSession.id }}</span>
              </div>
              <div class="detail-item">
                <span class="label">Créée le :</span>
                <span class="value">{{ formatDateTime(selectedSession.created_at) }}</span>
              </div>
              <div class="detail-item">
                <span class="label">Début :</span>
                <span class="value">{{ formatDateTime(selectedSession.start_time) }}</span>
              </div>
              <div class="detail-item">
                <span class="label">Fin :</span>
                <span class="value">{{ formatDateTime(selectedSession.end_time) }}</span>
              </div>
              <div class="detail-item">
                <span class="label">Durée totale :</span>
                <span class="value duration">{{ formatDuration(selectedSession.duration) }}</span>
              </div>
            </div>
            
            <div class="detail-section">
              <h4>Statistiques de détection</h4>
              <div class="detail-item">
                <span class="label">Frames éveillé :</span>
                <span class="value awake">{{ selectedSession.awake_count }}</span>
              </div>
              <div class="detail-item">
                <span class="label">Frames somnolent :</span>
                <span class="value drowsy">{{ selectedSession.drowsy_count }}</span>
              </div>
              <div class="detail-item">
                <span class="label">Alertes détectées :</span>
                <span class="value alert">{{ selectedSession.alert_count }}</span>
              </div>
              <div class="detail-item">
                <span class="label">Confiance moyenne :</span>
                <span class="value">{{ Math.round(selectedSession.avg_confidence) }}%</span>
              </div>
            </div>
          </div>
          
          <div class="session-summary">
            <h4>Résumé de la session</h4>
            <div class="summary-content">
              <p>
                Cette session de surveillance a duré <strong>{{ formatDuration(selectedSession.duration) }}</strong> 
                et a détecté <strong>{{ selectedSession.alert_count }} alerte(s)</strong> 
                avec une confiance moyenne de <strong>{{ Math.round(selectedSession.avg_confidence) }}%</strong>.
              </p>
              <p>
                Le système a analysé <strong>{{ selectedSession.awake_count + selectedSession.drowsy_count }} frames</strong> 
                au total, avec <strong>{{ selectedSession.awake_count }} frames éveillées</strong> 
                et <strong>{{ selectedSession.drowsy_count }} frames somnolentes</strong>.
              </p>
            </div>
          </div>
        </div>
        
        <div class="modal-footer">
          <button @click="closeModal" class="btn-secondary">Fermer</button>
          <button @click="deleteSession(selectedSession.id)" class="btn-danger">
            <i class="fas fa-trash-alt"></i>
            Supprimer cette session
          </button>
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
                 @load="onImageLoad"
                 @error="onImageError"
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
          <button 
            v-if="canExport"
            @click="exportSessionVideo" 
            class="btn-export-video" 
            :disabled="sessionFrames.length === 0 || exportingVideo"
          >
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
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { api } from '../services/api'

export default {
  name: 'HistorySection',
  props: {
    userRole: {
      type: String,
      default: 'user'
    }
  },
  setup(props) {
    // État des données
    const sessions = ref([])
    const loading = ref(false)
    const selectedSession = ref(null)
    
    // État de la vidéo
    const selectedVideoSession = ref(null)
    const sessionFrames = ref([])
    const videoLoading = ref(false)
    const videoError = ref(null)
    const isPlaying = ref(false)
    const currentFrameIndex = ref(0)
    const playInterval = ref(null)
    const exportingVideo = ref(false)
    
    // Filtres
    const dateFilter = ref('7')
    const statusFilter = ref('all')
    const limitFilter = ref('20')
    
    // Pagination
    const currentPage = ref(1)
    const itemsPerPage = 10
    
    // Computed properties
    const filteredSessions = computed(() => {
      let filtered = sessions.value
      
      // Filtre par statut
      if (statusFilter.value !== 'all') {
        filtered = filtered.filter(s => getSessionStatus(s) === statusFilter.value)
      }
      
      // Pagination
      const start = (currentPage.value - 1) * itemsPerPage
      const end = start + itemsPerPage
      return filtered.slice(start, end)
    })
    
    const totalSessions = computed(() => sessions.value.length)
    const totalPages = computed(() => Math.ceil(sessions.value.length / itemsPerPage))
    
    const totalDuration = computed(() => {
      const total = sessions.value.reduce((sum, s) => sum + (s.duration || 0), 0)
      return formatDuration(total)
    })
    
    const totalAlerts = computed(() => {
      return sessions.value.reduce((sum, s) => sum + (s.alert_count || 0), 0)
    })
    
    const avgConfidence = computed(() => {
      if (sessions.value.length === 0) return 0
      const total = sessions.value.reduce((sum, s) => sum + (s.avg_confidence || 0), 0)
      return Math.round(total / sessions.value.length)
    })
    
         // Computed properties pour la vidéo
     const currentFrame = computed(() => {
       if (sessionFrames.value.length === 0) return null
       const frame = sessionFrames.value[currentFrameIndex.value] || sessionFrames.value[0]
       console.log('🎬 currentFrame computed:', frame)
       return frame
     })
     
     const currentFrameImage = computed(() => {
       if (!currentFrame.value) {
         console.log('⚠️ currentFrameImage: pas de frame courante')
         return ''
       }
       const imageData = currentFrame.value.frame_data
       console.log('🖼️ currentFrameImage computed:', {
         hasData: !!imageData,
         dataLength: imageData ? imageData.length : 0,
         dataPreview: imageData ? imageData.substring(0, 50) + '...' : 'null'
       })
       return imageData
     })
    
    // Computed properties pour les permissions
    const canExport = computed(() => props.userRole === 'admin')
    
    // Méthodes
    async function loadSessions() {
      loading.value = true
      try {
        const response = await api.request(`/get_sessions?limit=${limitFilter.value}`)
        sessions.value = response.sessions || []
        currentPage.value = 1 // Reset à la première page
        console.log(`📊 ${sessions.value.length} sessions chargées`)
      } catch (error) {
        console.error('Erreur chargement sessions:', error)
        sessions.value = []
      } finally {
        loading.value = false
      }
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
    
    function getConfidenceClass(confidence) {
      if (confidence >= 80) return 'high'
      if (confidence >= 60) return 'medium'
      return 'low'
    }
    
    function formatDate(dateString) {
      if (!dateString) return 'N/A'
      const date = new Date(dateString)
      return date.toLocaleDateString('fr-FR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      })
    }
    
    function formatTime(dateString) {
      if (!dateString) return 'N/A'
      const date = new Date(dateString)
      return date.toLocaleTimeString('fr-FR', {
        hour: '2-digit',
        minute: '2-digit'
      })
    }
    
    function formatDateTime(dateString) {
      if (!dateString) return 'N/A'
      const date = new Date(dateString)
      return date.toLocaleString('fr-FR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
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
    
    function viewSessionDetails(session) {
      selectedSession.value = session
    }
    
    function closeModal() {
      selectedSession.value = null
    }
    
    // Méthodes pour la gestion de la vidéo
    async function viewSessionVideo(session) {
      console.log('🎬 viewSessionVideo appelé pour la session:', session)
      selectedVideoSession.value = session
      videoLoading.value = true
      videoError.value = null
      sessionFrames.value = []
      currentFrameIndex.value = 0
      
      try {
        console.log(`🔍 Appel API /get_session_frames/${session.id}`)
        const response = await api.request(`/get_session_frames/${session.id}`)
        console.log('📥 Réponse API:', response)
        
                 if (response.success) {
           sessionFrames.value = response.frames || []
           console.log(`🎥 ${sessionFrames.value.length} frames chargées pour la session ${session.id}`)
           console.log('📋 Frames reçues:', sessionFrames.value)
           
           // Log détaillé de la première frame
           if (sessionFrames.value.length > 0) {
             const firstFrame = sessionFrames.value[0]
             console.log('🔍 Première frame détaillée:', {
               id: firstFrame.id,
               session_id: firstFrame.session_id,
               frame_data_length: firstFrame.frame_data ? firstFrame.frame_data.length : 'null',
               frame_data_preview: firstFrame.frame_data ? firstFrame.frame_data.substring(0, 100) + '...' : 'null',
               timestamp: firstFrame.timestamp,
               prediction: firstFrame.prediction,
               confidence: firstFrame.confidence,
               frame_number: firstFrame.frame_number
             })
           }
         } else {
          videoError.value = response.error || 'Erreur lors du chargement des frames'
          console.error('❌ Erreur API:', response.error)
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
      }, 100) // 10 FPS pour la lecture
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
        
        // Capture stream + MediaRecorder
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
          // Attendre le chargement
          /* eslint-disable no-await-in-loop */
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
    
         function seekToFrame() {
       // La fonction est automatiquement appelée par v-model sur le slider
       // Pas besoin de logique supplémentaire
     }
     
     function onImageLoad(event) {
       console.log('✅ Image chargée avec succès:', {
         src: event.target.src,
         naturalWidth: event.target.naturalWidth,
         naturalHeight: event.target.naturalHeight
       })
     }
     
     function onImageError(event) {
       console.error('❌ Erreur de chargement de l\'image:', {
         src: event.target.src,
         error: event.target.error
       })
     }
    
    function formatTimestamp(timestamp) {
      if (!timestamp) return 'N/A'
      const date = new Date(timestamp * 1000) // Convertir en millisecondes
      return date.toLocaleTimeString('fr-FR', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
    }
    
    async function deleteSession(sessionId) {
      if (!confirm('Êtes-vous sûr de vouloir supprimer cette session ?')) {
        return
      }
      
      try {
        await api.request(`/delete_session/${sessionId}`, { method: 'DELETE' })
        console.log(`🗑️ Session ${sessionId} supprimée`)
        
        // Fermer le modal si ouvert
        if (selectedSession.value && selectedSession.value.id === sessionId) {
          closeModal()
        }
        
        // Recharger les sessions
        await loadSessions()
      } catch (error) {
        console.error('Erreur suppression session:', error)
        alert('Erreur lors de la suppression de la session')
      }
    }
    
    async function clearAllSessions() {
      if (!confirm('Êtes-vous sûr de vouloir effacer TOUT l\'historique ? Cette action est irréversible !')) {
        return
      }
      
      try {
        await api.request('/clear_sessions', { method: 'DELETE' })
        console.log('🧹 Toutes les sessions supprimées')
        alert('Toutes les sessions ont été supprimées avec succès')
        
        // Recharger les sessions (sera vide)
        await loadSessions()
      } catch (error) {
        console.error('Erreur effacement sessions:', error)
        alert('Erreur lors de l\'effacement des sessions')
      }
    }
    
    function exportHistory() {
      if (sessions.value.length === 0) return
      
      const csvContent = generateCSV()
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      const url = URL.createObjectURL(blob)
      
      link.setAttribute('href', url)
      link.setAttribute('download', `historique_sessions_${new Date().toISOString().split('T')[0]}.csv`)
      link.style.visibility = 'hidden'
      
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    }
    
    function generateCSV() {
      const headers = [
        'ID', 'Date création', 'Début', 'Fin', 'Durée (s)', 
        'Éveillé', 'Somnolent', 'Alertes', 'Confiance moyenne'
      ]
      
      const rows = sessions.value.map(s => [
        s.id,
        s.created_at,
        s.start_time,
        s.end_time,
        s.duration,
        s.awake_count,
        s.drowsy_count,
        s.alert_count,
        s.avg_confidence
      ])
      
      return [headers, ...rows]
        .map(row => row.map(cell => `"${cell || ''}"`).join(','))
        .join('\n')
    }
    
    function previousPage() {
      if (currentPage.value > 1) {
        currentPage.value--
      }
    }
    
    function nextPage() {
      if (currentPage.value < totalPages.value) {
        currentPage.value++
      }
    }
    
    // Lifecycle
    onMounted(() => {
      loadSessions()
      
      // Actualisation automatique toutes les 30 secondes
      const interval = setInterval(loadSessions, 30000)
      
      onBeforeUnmount(() => {
        clearInterval(interval)
        // Nettoyer les intervalles vidéo
        if (playInterval.value) {
          clearInterval(playInterval.value)
        }
      })
    })
    
    return {
      // État
      sessions,
      loading,
      selectedSession,
      selectedVideoSession,
      sessionFrames,
      videoLoading,
      videoError,
      isPlaying,
      currentFrameIndex,
      dateFilter,
      statusFilter,
      limitFilter,
      currentPage,
      
      // Computed
      filteredSessions,
      totalSessions,
      totalPages,
      totalDuration,
      totalAlerts,
      avgConfidence,
      currentFrame,
      currentFrameImage,
      canExport,
      
      // Méthodes
      loadSessions,
      getSessionStatus,
      getSessionStatusClass,
      getSessionStatusText,
      getConfidenceClass,
      formatDate,
      formatTime,
      formatDateTime,
      formatDuration,
      viewSessionDetails,
      closeModal,
      viewSessionVideo,
      closeVideoModal,
      playVideo,
      pauseVideo,
      stopVideo,
      exportingVideo,
      exportSessionVideo,
             seekToFrame,
       onImageLoad,
       onImageError,
       formatTimestamp,
       deleteSession,
      clearAllSessions,
      exportHistory,
      previousPage,
      nextPage
    }
  }
}
</script>

<style scoped>
.history-section {
  padding: 2rem 0;
}

.history-header {
  text-align: center;
  margin-bottom: 3rem;
}

.history-header h1 {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  background: linear-gradient(135deg, #ffffff, #e5e7eb);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.history-header p {
  font-size: 1.125rem;
  color: #9ca3af;
}

/* Contrôles */
.history-controls {
  background: linear-gradient(135deg, #1a1f2e, #252a3a);
  border-radius: 16px;
  padding: 2rem;
  border: 1px solid #374151;
  margin-bottom: 2rem;
}

.filters-row {
  display: flex;
  gap: 2rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  min-width: 150px;
}

.filter-group label {
  font-weight: 500;
  color: #d1d5db;
  font-size: 0.875rem;
}

.filter-group select {
  padding: 0.75rem;
  border: 1px solid #374151;
  border-radius: 8px;
  background: #0f1419;
  color: #ffffff;
  font-size: 0.875rem;
  cursor: pointer;
}

.actions-row {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.btn-refresh, .btn-export, .btn-clear {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 0.875rem;
}

.btn-refresh {
  background: linear-gradient(135deg, #4f9eff, #60a5fa);
  color: white;
}

.btn-export {
  background: linear-gradient(135deg, #4ade80, #22c55e);
  color: white;
}

.btn-clear {
  background: linear-gradient(135deg, #ef4444, #dc2626);
  color: white;
}

.btn-refresh:hover, .btn-export:hover, .btn-clear:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
}

.btn-refresh:disabled, .btn-export:disabled, .btn-clear:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

/* Statistiques globales */
.stats-overview {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.stat-item {
  background: linear-gradient(135deg, #1a1f2e, #252a3a);
  border-radius: 12px;
  padding: 1.5rem;
  text-align: center;
  border: 1px solid #374151;
}

.stat-number {
  font-size: 2rem;
  font-weight: 700;
  color: #4f9eff;
  margin-bottom: 0.5rem;
}

.stat-label {
  color: #9ca3af;
  font-size: 0.875rem;
  font-weight: 500;
}

/* Grille des sessions */
.sessions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.session-card {
  background: linear-gradient(135deg, #1a1f2e, #252a3a);
  border-radius: 16px;
  padding: 1.5rem;
  border: 1px solid #374151;
  transition: all 0.3s ease;
}

.session-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2);
  border-color: #4f9eff;
}

.session-card.status-completed {
  border-left: 4px solid #4ade80;
}

.session-card.status-interrupted {
  border-left: 4px solid #f59e0b;
}

/* En-tête de session */
.session-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;
}

.session-info {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.session-date, .session-time {
  display: flex;
  align-items: center;
  gap: 0.5rem;
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

.session-status.status-completed {
  background: rgba(74, 222, 128, 0.1);
  color: #4ade80;
}

.session-status.status-interrupted {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
}

/* Détails de session */
.session-details {
  margin-bottom: 1.5rem;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
}

.detail-row:first-child {
  color: #d1d5db;
}

.detail-row:last-child {
  color: #9ca3af;
}

.duration {
  color: #4f9eff;
  font-weight: 600;
}

/* Statistiques de détection */
.detection-stats {
  margin-bottom: 1.5rem;
}

.stat-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  margin-bottom: 1rem;
}

.stat-item-detection {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  background: rgba(15, 20, 25, 0.5);
  border-radius: 8px;
}

.stat-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  color: white;
}

.stat-icon.awake {
  background: linear-gradient(135deg, #4ade80, #22c55e);
}

.stat-icon.drowsy {
  background: linear-gradient(135deg, #f59e0b, #d97706);
}

.stat-icon.alert {
  background: linear-gradient(135deg, #ef4444, #dc2626);
}

.stat-content {
  flex: 1;
}

.stat-content .stat-value {
  font-size: 1.25rem;
  font-weight: 700;
  margin-bottom: 0.25rem;
}

.stat-content .stat-label {
  font-size: 0.75rem;
  color: #9ca3af;
  text-transform: uppercase;
  font-weight: 500;
}

/* Barre de confiance */
.confidence-bar {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: rgba(15, 20, 25, 0.5);
  border-radius: 8px;
}

.confidence-label {
  font-size: 0.875rem;
  color: #9ca3af;
  min-width: 120px;
}

.confidence-progress {
  flex: 1;
  height: 8px;
  background: #374151;
  border-radius: 4px;
  overflow: hidden;
}

.confidence-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s ease;
}

.confidence-fill.high {
  background: linear-gradient(90deg, #4ade80, #22c55e);
}

.confidence-fill.medium {
  background: linear-gradient(90deg, #f59e0b, #d97706);
}

.confidence-fill.low {
  background: linear-gradient(90deg, #ef4444, #dc2626);
}

.confidence-value {
  font-size: 0.875rem;
  font-weight: 600;
  color: #d1d5db;
  min-width: 40px;
  text-align: right;
}

/* Actions */
.session-actions {
  display: flex;
  gap: 0.75rem;
}

.btn-action {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  border: none;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  flex: 1;
  justify-content: center;
}

.btn-view {
  background: #374151;
  color: #e5e7eb;
}

.btn-view:hover {
  background: #4f9eff;
  color: white;
}

.btn-delete {
  background: transparent;
  color: #ef4444;
  border: 1px solid #ef4444;
  flex: 0 0 auto;
}

.btn-delete:hover {
  background: #ef4444;
  color: white;
}

/* Pagination */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  margin-top: 2rem;
}

.btn-page {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border: 1px solid #374151;
  background: transparent;
  color: #9ca3af;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-page:hover:not(:disabled) {
  border-color: #4f9eff;
  color: #4f9eff;
}

.btn-page:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  color: #9ca3af;
  font-size: 0.875rem;
}

/* Modal */
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
  padding: 2rem;
}

.modal-content {
  background: linear-gradient(135deg, #1a1f2e, #252a3a);
  border-radius: 16px;
  border: 1px solid #374151;
  max-width: 800px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 2rem;
  border-bottom: 1px solid #374151;
}

.modal-header h3 {
  color: #ffffff;
  font-size: 1.5rem;
  font-weight: 600;
}

.btn-close {
  background: transparent;
  border: none;
  color: #9ca3af;
  font-size: 1.25rem;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 4px;
  transition: all 0.3s ease;
}

.btn-close:hover {
  color: #ffffff;
  background: rgba(255, 255, 255, 0.1);
}

.modal-body {
  padding: 2rem;
}

.session-detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
  margin-bottom: 2rem;
}

.detail-section h4 {
  color: #4f9eff;
  font-size: 1.125rem;
  margin-bottom: 1rem;
  font-weight: 600;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.75rem;
  padding: 0.5rem 0;
  border-bottom: 1px solid rgba(55, 65, 81, 0.3);
}

.detail-item .label {
  color: #9ca3af;
  font-weight: 500;
}

.detail-item .value {
  color: #ffffff;
  font-weight: 600;
}

.detail-item .value.awake {
  color: #4ade80;
}

.detail-item .value.drowsy {
  color: #f59e0b;
}

.detail-item .value.alert {
  color: #ef4444;
}

.session-summary {
  background: rgba(15, 20, 25, 0.5);
  border-radius: 12px;
  padding: 1.5rem;
}

.session-summary h4 {
  color: #4f9eff;
  font-size: 1.125rem;
  margin-bottom: 1rem;
  font-weight: 600;
}

.summary-content p {
  color: #d1d5db;
  line-height: 1.6;
  margin-bottom: 1rem;
}

.summary-content strong {
  color: #ffffff;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding: 1.5rem 2rem;
  border-top: 1px solid #374151;
}

.btn-secondary {
  padding: 0.75rem 1.5rem;
  border: 1px solid #374151;
  background: transparent;
  color: #9ca3af;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-secondary:hover {
  border-color: #4f9eff;
  color: #4f9eff;
}

.btn-danger {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border: none;
  background: linear-gradient(135deg, #ef4444, #dc2626);
  color: white;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: 600;
}

.btn-danger:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(239, 68, 68, 0.3);
}

/* États spéciaux */
.loading-state, .empty-state {
  text-align: center;
  padding: 4rem 2rem;
  color: #9ca3af;
}

.spinner {
  width: 60px;
  height: 60px;
  border: 4px solid #374151;
  border-top: 4px solid #4f9eff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1.5rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.empty-state i {
  font-size: 4rem;
  margin-bottom: 1.5rem;
  color: #6b7280;
}

.empty-state h3 {
  color: #d1d5db;
  margin-bottom: 0.5rem;
}

/* Responsive */
@media (max-width: 768px) {
  .filters-row {
    flex-direction: column;
    gap: 1rem;
  }
  
  .actions-row {
    flex-direction: column;
  }
  
  .sessions-grid {
    grid-template-columns: 1fr;
  }
  
  .stat-row {
    grid-template-columns: 1fr;
  }
  
  .confidence-bar {
    flex-direction: column;
    gap: 0.5rem;
    text-align: center;
  }
  
  .modal-content {
    margin: 1rem;
    max-height: calc(100vh - 2rem);
  }
  
  .session-detail-grid {
    grid-template-columns: 1fr;
  }
}

/* Styles pour le bouton vidéo */
.btn-video {
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-video:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(16, 185, 129, 0.3);
}

/* Styles pour la modal vidéo */
.video-modal {
  max-width: 90vw;
  max-height: 90vh;
  width: 1200px;
}

.video-loading, .video-error, .no-frames {
  text-align: center;
  padding: 4rem 2rem;
  color: #9ca3af;
}

.video-error i, .no-frames i {
  font-size: 4rem;
  margin-bottom: 1.5rem;
  color: #ef4444;
}

.video-error h4, .no-frames h4 {
  color: #d1d5db;
  margin-bottom: 0.5rem;
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
  padding: 1rem;
  background: #1f2937;
  border-radius: 8px;
}

.btn-control {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border: none;
  background: #374151;
  color: white;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: 600;
}

.btn-control:hover:not(:disabled) {
  background: #4b5563;
  transform: translateY(-1px);
}

.btn-control:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.progress-container {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex: 1;
  min-width: 200px;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #374151;
  border-radius: 4px;
  outline: none;
  cursor: pointer;
}

.progress-bar::-webkit-slider-thumb {
  appearance: none;
  width: 20px;
  height: 20px;
  background: #4f9eff;
  border-radius: 50%;
  cursor: pointer;
}

.progress-text {
  font-size: 0.875rem;
  color: #9ca3af;
  text-align: center;
}

.video-display {
  display: flex;
  gap: 2rem;
  align-items: flex-start;
}

.frame-image {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.frame-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1.5rem;
  background: #1f2937;
  border-radius: 8px;
  min-width: 250px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: #374151;
  border-radius: 6px;
}

.info-item .label {
  color: #9ca3af;
  font-weight: 500;
}

.info-item span:last-child {
  color: #d1d5db;
  font-weight: 600;
}

.prediction-awake {
  color: #10b981;
}

.prediction-drowsy {
  color: #f59e0b;
}

.prediction-alert {
  color: #ef4444;
}

/* Responsive pour la vidéo */
@media (max-width: 768px) {
  .video-modal {
    margin: 1rem;
    max-width: calc(100vw - 2rem);
    max-height: calc(100vh - 2rem);
  }
  
  .video-display {
    flex-direction: column;
  }
  
  .video-controls {
    flex-direction: column;
    align-items: stretch;
  }
  
  .progress-container {
    min-width: auto;
  }
}
</style>
