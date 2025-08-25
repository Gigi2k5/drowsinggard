<template>
  <div id="app">
    <!-- Navigation principale -->
    <nav class="navbar">
      <div class="nav-container">
        <div class="nav-brand">
          <i class="fas fa-shield-alt"></i>
          <span>DrowsiGuard</span>
        </div>
        
        <div class="nav-menu">
          <button 
            @click="activeTab = 'monitor'" 
            :class="['nav-item', { active: activeTab === 'monitor' }]"
          >
            <i class="fas fa-video"></i>
            Surveillance
          </button>
          
          <button 
            @click="activeTab = 'history'" 
            :class="['nav-item', { active: activeTab === 'history' }]"
          >
            <i class="fas fa-history"></i>
            Historique
          </button>
          
          <button 
            @click="activeTab = 'settings'" 
            :class="['nav-item', { active: activeTab === 'settings' }]"
          >
            <i class="fas fa-cog"></i>
            Paramètres
          </button>
        </div>
      </div>
    </nav>

    <!-- Contenu principal -->
    <main class="main-content">
      <!-- Onglet Surveillance -->
      <div v-if="activeTab === 'monitor'" class="tab-content">
        <div class="monitor-container">
          <!-- En-tête de surveillance -->
          <header class="monitor-header">
            <h1>Surveillance en Temps Réel</h1>
            <p>Détection automatique de somnolence via IA</p>
          </header>

                     <!-- Zone webcam -->
           <WebcamFeed 
             v-model="isStreaming"
             :session-id="currentSessionId"
             @status-update="handleWebcamStatus"
             @alert-detected="handleAlertDetected"
             @prediction-update="handlePredictionUpdate"
             @frame-captured="handleFrameCaptured"
           />

          <!-- Panneau de statistiques -->
          <div class="stats-panel">
            <div class="stat-card">
              <div class="stat-icon">
                <i class="fas fa-clock"></i>
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ sessionDuration }}</div>
                <div class="stat-label">Durée de session</div>
              </div>
            </div>
            
            <div class="stat-card">
              <div class="stat-icon">
                <i class="fas fa-exclamation-triangle"></i>
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ alertCount }}</div>
                <div class="stat-label">Alertes détectées</div>
              </div>
            </div>
            
            <div class="stat-card">
              <div class="stat-icon">
                <i class="fas fa-tachometer-alt"></i>
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ avgLatency }}ms</div>
                <div class="stat-label">Latence moyenne</div>
              </div>
            </div>
          </div>

          <!-- Composants de monitoring -->
          <PerformanceMonitor />
          <FaceDetectionTest />
        </div>
      </div>

            <!-- Onglet Historique -->
      <div v-if="activeTab === 'history'" class="tab-content">
        <HistorySection />
      </div>

      <!-- Onglet Paramètres -->
      <div v-if="activeTab === 'settings'" class="tab-content">
        <div class="settings-container">
          <header class="settings-header">
            <h1>Paramètres</h1>
            <p>Configurez votre expérience DrowsiGuard</p>
          </header>

          <div class="settings-grid">
            <!-- Paramètres Audio -->
            <AudioSettings 
              v-model="audioSettings"
              @test-audio="testAudio"
            />

            <!-- Paramètres de Détection -->
            <div class="settings-section">
              <h3><i class="fas fa-eye"></i> Paramètres de Détection</h3>
              
              <div class="setting-item">
                <label>Seuil d'alerte :</label>
                <input 
                  type="number" 
                  v-model="detectionSettings.threshold" 
                  min="1" 
                  max="10"
                />
                <span>frames consécutives</span>
              </div>
              
              <div class="setting-item">
                <label>Qualité d'image :</label>
                <select v-model="detectionSettings.quality">
                  <option value="0.5">Basse</option>
                  <option value="0.7">Moyenne</option>
                  <option value="0.9">Haute</option>
                </select>
              </div>
              
              <div class="setting-item">
                <label>
                  <input type="checkbox" v-model="detectionSettings.faceDetection" />
                  Détection faciale
                </label>
              </div>
            </div>

            <!-- Test de l'API -->
            <ApiTest />

            <!-- Informations Système -->
            <ApiStatus />
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { api } from './services/api'
import AudioSettings from './components/AudioSettings.vue'
import ApiStatus from './components/ApiStatus.vue'
import ApiTest from './components/ApiTest.vue'
import PerformanceMonitor from './components/PerformanceMonitor.vue'
import FaceDetectionTest from './components/FaceDetectionTest.vue'
import HistorySection from './components/HistorySection.vue'
import WebcamFeed from './components/WebcamFeed.vue'

export default {
  name: 'App',
  components: {
    AudioSettings,
    ApiStatus,
    ApiTest,
    PerformanceMonitor,
    FaceDetectionTest,
    HistorySection,
    WebcamFeed
  },
  setup() {
    // État de l'application
    const activeTab = ref('monitor')
    const isStreaming = ref(false)
    const isRecording = ref(false)

    const sessionDuration = ref('00:00')
    const alertCount = ref(0)
    const avgLatency = ref(0)
    
    // État des sessions
    const sessions = ref([])
    const loading = ref(false)
    const dateFilter = ref('7')
    const statusFilter = ref('all')
    const currentSessionId = ref(null)
    
    // Paramètres
    const audioSettings = ref({
      type: 'beep',
      volume: 0.7,
      customFile: null
    })
    
    const detectionSettings = ref({
      threshold: 3,
      quality: 0.7,
      faceDetection: true
    })
    
    // Statut système
    const backendStatus = ref('disconnected')
    const modelStatus = ref('not-loaded')
    
    // Références DOM
    let sessionTimer = null
    let startTime = null
    let realTimeInterval = null

    // Computed properties

    const filteredSessions = computed(() => {
      let filtered = sessions.value
      
      if (statusFilter.value !== 'all') {
        filtered = filtered.filter(s => s.status === statusFilter.value)
      }
      
      return filtered
    })

    // Méthodes webcam gérées par le composant WebcamFeed

    function toggleRecording() {
      if (isRecording.value) {
        stopRecording()
      } else {
        startRecording()
      }
    }

    function startRecording() {
      isRecording.value = true
      // Logique d'enregistrement
    }

    function stopRecording() {
      isRecording.value = false
      // Logique d'arrêt d'enregistrement
    }

    // Gestion de session
    function startSession() {
      // Générer un nouvel ID de session
      currentSessionId.value = Date.now()
      startTime = Date.now()
      sessionTimer = setInterval(updateSessionDuration, 1000)
      console.log(`🚀 Nouvelle session démarrée avec l'ID: ${currentSessionId.value}`)
    }

    async function stopSession() {
      if (sessionTimer) {
        clearInterval(sessionTimer)
        sessionTimer = null
      }
      
      // Sauvegarder la session avant de réinitialiser
      if (startTime) {
        await saveSession()
      }
      
      startTime = null
      sessionDuration.value = '00:00'
      
      // Réinitialiser complètement les stats à l'arrêt
      alertCount.value = 0
      avgLatency.value = 0
      
      // Réinitialiser l'ID de session
      currentSessionId.value = null
      
      console.log('🛑 Session arrêtée - Stats réinitialisées: Alertes=0, Latence=0ms, SessionID=null')
    }

    function updateSessionDuration() {
      if (startTime) {
        const elapsed = Math.floor((Date.now() - startTime) / 1000)
        const minutes = Math.floor(elapsed / 60)
        const seconds = elapsed % 60
        sessionDuration.value = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
      }
    }

    // Surveillance en temps réel pendant la session
    function startRealTimeMonitoring() {
      // Mise à jour toutes les 500ms pour du vrai temps réel
      realTimeInterval = setInterval(async () => {
        if (isStreaming.value) {
          try {
            // Récupérer les vraies données de performance du backend
            const response = await api.request('/performance')
            
            // Log des métriques système (la latence est maintenant gérée par handlePredictionUpdate)
            console.log(`📊 Métriques système: Cache ${response.cache?.size || 0}/${response.cache?.max_size || 0}, CPU: ${response.system?.cpu_percent || 0}%`)
            
          } catch (error) {
            console.error('Erreur surveillance temps réel:', error)
          }
        }
      }, 500) // 500ms = 2 FPS pour du vrai temps réel
    }
    
    function stopRealTimeMonitoring() {
      if (realTimeInterval) {
        clearInterval(realTimeInterval)
        realTimeInterval = null
      }
    }

    // Mise à jour des statistiques système (pas les stats de session)
    async function updateStats() {
      try {
        const response = await api.request('/performance')
        // Cette fonction ne met plus à jour alertCount et avgLatency
        // car ils sont maintenant gérés par la surveillance en temps réel
        console.log('Stats système mises à jour:', response)
      } catch (error) {
        console.error('Erreur mise à jour stats système:', error)
      }
    }

    // Gestion des sessions
    async function saveSession() {
      if (!startTime) return // Pas de session à sauvegarder
      
      try {
        const endTime = Date.now()
        const duration = Math.floor((endTime - startTime) / 1000) // durée en secondes
        
        // Calculer les statistiques de la session
        const sessionData = {
          start_time: new Date(startTime).toISOString(),
          end_time: new Date(endTime).toISOString(),
          duration: duration,
          awake_count: Math.floor(duration * 0.6), // Estimation basée sur la durée
          drowsy_count: Math.floor(duration * 0.3), // Estimation basée sur la durée
          alert_count: alertCount.value, // Nombre réel d'alertes détectées
          avg_confidence: 75 // Confiance moyenne par défaut
        }
        
        console.log('💾 Sauvegarde de la session:', sessionData)
        
        const response = await api.request('/save_session', {
          method: 'POST',
          body: JSON.stringify(sessionData)
        })
        
        if (response.success) {
          console.log('✅ Session sauvegardée avec succès')
          // Recharger l'historique pour afficher la nouvelle session
          await loadSessions()
        } else {
          console.error('❌ Erreur sauvegarde session:', response.error)
        }
        
      } catch (error) {
        console.error('❌ Erreur sauvegarde session:', error)
      }
    }

    async function loadSessions() {
      loading.value = true
      try {
        const response = await api.request('/get_sessions?limit=50')
        sessions.value = response.sessions || []
      } catch (error) {
        console.error('Erreur chargement sessions:', error)
      } finally {
        loading.value = false
      }
    }

    function formatDate(dateString) {
      const date = new Date(dateString)
      return date.toLocaleDateString('fr-FR')
    }

    function formatDuration(seconds) {
      const minutes = Math.floor(seconds / 60)
      const remainingSeconds = seconds % 60
      return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
    }

    function viewSession(session) {
      console.log('Voir session:', session)
      // Logique d'affichage détaillé
    }

    async function deleteSession(sessionId) {
      if (confirm('Supprimer cette session ?')) {
        try {
          await api.request(`/delete_session/${sessionId}`, { method: 'DELETE' })
          await loadSessions()
        } catch (error) {
          console.error('Erreur suppression:', error)
        }
      }
    }

    // Paramètres audio
    function handleAudioFile(event) {
      const file = event.target.files[0]
      if (file) {
        audioSettings.value.customFile = URL.createObjectURL(file)
      }
    }

    function testAudio() {
      // Logique de test audio
      console.log('Test audio avec:', audioSettings.value)
      
      // Créer un contexte audio
      const audioContext = new (window.AudioContext || window.webkitAudioContext)()
      
      if (audioSettings.value.type === 'custom' && audioSettings.value.customFile) {
        // Jouer le fichier personnalisé
        const audio = new Audio(audioSettings.value.customFile)
        audio.volume = audioSettings.value.volume
        audio.play().catch(err => console.error('Erreur lecture audio:', err))
      } else {
        // Générer un son de test selon le type
        const oscillator = audioContext.createOscillator()
        const gainNode = audioContext.createGain()
        
        oscillator.connect(gainNode)
        gainNode.connect(audioContext.destination)
        
        // Configurer le son selon le type
        switch (audioSettings.value.type) {
          case 'beep':
            oscillator.frequency.setValueAtTime(800, audioContext.currentTime)
            oscillator.type = 'sine'
            break
          case 'alarm':
            oscillator.frequency.setValueAtTime(400, audioContext.currentTime)
            oscillator.type = 'square'
            break
          case 'bell':
            oscillator.frequency.setValueAtTime(600, audioContext.currentTime)
            oscillator.type = 'triangle'
            break
        }
        
        gainNode.gain.setValueAtTime(audioSettings.value.volume, audioContext.currentTime)
        
        oscillator.start()
        oscillator.stop(audioContext.currentTime + 0.5)
      }
    }

    function handleWebcamStatus(status) {
      console.log('Statut webcam:', status)
      if (status === 'started') {
        startSession()
        // Initialiser les stats au démarrage
        alertCount.value = 0
        avgLatency.value = 0
        // Démarrer la surveillance en temps réel
        startRealTimeMonitoring()
        console.log('▶️ Webcam démarrée - Surveillance activée')
      } else if (status === 'stopped') {
        stopSession()
        // Arrêter la surveillance
        stopRealTimeMonitoring()
        // Forcer la réinitialisation des stats
        alertCount.value = 0
        avgLatency.value = 0
        console.log('⏹️ Webcam arrêtée - Stats réinitialisées')
      }
    }
    
    // Fonction pour recevoir les vraies alertes détectées par l'IA
    function handleAlertDetected(prediction) {
      // Ne traiter les alertes que si la webcam est active
      if (isStreaming.value && (prediction === 'drowsy' || prediction === 'alert')) {
        alertCount.value++
        console.log('Alerte détectée! Total:', alertCount.value)
      }
    }
    
    // Fonction pour recevoir les mises à jour de prédiction en temps réel
    function handlePredictionUpdate(predictionData) {
      // Ne traiter les prédictions que si la webcam est active
      if (isStreaming.value) {
        // Mettre à jour la latence moyenne avec la VRAIE latence du backend
        if (predictionData.latency) {
          avgLatency.value = Math.round(predictionData.latency)
          console.log(`⚡ Latence mise à jour: ${predictionData.latency}ms`)
        }
        
        // Log pour debug
        console.log(`📊 Prédiction mise à jour: ${predictionData.prediction} (${predictionData.confidence}%)`)
      }
    }

    // Fonction pour gérer les frames capturées pendant la session
    async function handleFrameCaptured(frameData) {
      console.log('🎬 handleFrameCaptured appelé avec:', {
        sessionId: frameData.sessionId,
        isStreaming: isStreaming.value,
        currentSessionId: currentSessionId.value,
        prediction: frameData.prediction,
        confidence: frameData.confidence
      })
      
      if (isStreaming.value && currentSessionId.value) {
        try {
          // Enregistrer la frame dans la base de données via l'API
          const response = await api.request('/save_frame', {
            method: 'POST',
            body: JSON.stringify({
              session_id: frameData.sessionId,
              frame_data: frameData.frameData,
              timestamp: frameData.timestamp,
              prediction: frameData.prediction,
              confidence: frameData.confidence,
              frame_number: frameData.frameNumber
            })
          })
          
          if (response.success) {
            console.log(`✅ Frame enregistrée avec succès pour la session ${frameData.sessionId}`)
          } else {
            console.error(`❌ Erreur sauvegarde frame: ${response.error}`)
          }
        } catch (error) {
          console.error('❌ Erreur enregistrement frame:', error)
        }
      } else {
        console.log('⚠️ Frame non enregistrée: webcam inactive ou pas de session ID')
      }
    }

    // Vérification du backend
    async function checkBackend() {
      try {
        await api.request('/health')
        backendStatus.value = 'connected'
      } catch (error) {
        backendStatus.value = 'disconnected'
      }
    }

    // Lifecycle
    onMounted(() => {
      loadSessions()
      checkBackend()
      updateStats() // Mise à jour initiale
      
      // Mise à jour automatique des stats toutes les 10 secondes
      const statsInterval = setInterval(updateStats, 10000)
      
      // Nettoyage à la destruction
      onBeforeUnmount(() => {
        if (statsInterval) clearInterval(statsInterval)
        if (realTimeInterval) clearInterval(realTimeInterval)
        if (sessionTimer) clearInterval(sessionTimer)
        
        // Réinitialiser les stats
        alertCount.value = 0
        avgLatency.value = 0
        sessionDuration.value = '00:00'
        
        console.log('🧹 Composant détruit - Nettoyage terminé')
      })
    })

    return {
      // État
      activeTab,
      isStreaming,
      isRecording,
      sessionDuration,
      alertCount,
      avgLatency,
      sessions,
      loading,
      dateFilter,
      statusFilter,
      currentSessionId,
      audioSettings,
      detectionSettings,
      backendStatus,
      modelStatus,
      

      
              // Computed
      filteredSessions,
      
      // Méthodes
      toggleRecording,
      loadSessions,
      saveSession,
      formatDate,
      formatDuration,
      viewSession,
      deleteSession,
      handleAudioFile,
      testAudio,
      handleWebcamStatus,
      handleAlertDetected,
      handlePredictionUpdate,
      handleFrameCaptured,
      updateStats
    }
  }
}
</script>

<style>
/* Reset et base */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  background: #0f1419;
  color: #ffffff;
  line-height: 1.6;
}

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* Navigation */
.navbar {
  background: rgba(15, 20, 25, 0.95);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid #374151;
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1rem 2rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 1.5rem;
  font-weight: 700;
  color: #4f9eff;
}

.nav-brand i {
  font-size: 1.75rem;
}

.nav-menu {
  display: flex;
  gap: 0.5rem;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.25rem;
  background: transparent;
  border: 1px solid #374151;
  border-radius: 12px;
  color: #9ca3af;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.nav-item:hover {
  border-color: #4f9eff;
  color: #4f9eff;
}

.nav-item.active {
  background: rgba(79, 158, 255, 0.1);
  border-color: #4f9eff;
  color: #4f9eff;
}

.nav-item i {
  font-size: 1rem;
}

/* Contenu principal */
.main-content {
  flex: 1;
  padding: 2rem;
}

.tab-content {
  max-width: 1200px;
  margin: 0 auto;
}

/* En-têtes de section */
.monitor-header,
.history-header,
.settings-header {
  text-align: center;
  margin-bottom: 3rem;
}

.monitor-header h1,
.history-header h1,
.settings-header h1 {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  background: linear-gradient(135deg, #ffffff, #e5e7eb);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.monitor-header p,
.history-header p,
.settings-header p {
  font-size: 1.125rem;
  color: #9ca3af;
}

/* Zone webcam */
.webcam-zone {
  margin-bottom: 3rem;
}

.webcam-container {
  position: relative;
  background: #1a1f2e;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  border: 1px solid #374151;
  margin-bottom: 2rem;
}

.webcam-video {
  width: 100%;
  height: auto;
  display: block;
}

.status-overlay {
  position: absolute;
  top: 1.5rem;
  left: 1.5rem;
  right: 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1.25rem;
  border-radius: 12px;
  font-weight: 600;
  font-size: 0.875rem;
  backdrop-filter: blur(10px);
}

.status-indicator.awake {
  background: rgba(34, 197, 94, 0.9);
  color: white;
}

.status-indicator.drowsy {
  background: rgba(251, 191, 36, 0.9);
  color: white;
}

.status-indicator.alert {
  background: rgba(239, 68, 68, 0.9);
  color: white;
  animation: pulse 2s infinite;
}

.recording-indicator {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1.25rem;
  background: rgba(239, 68, 68, 0.9);
  color: white;
  border-radius: 12px;
  font-weight: 600;
  font-size: 0.875rem;
  backdrop-filter: blur(10px);
}

.rec-dot {
  width: 12px;
  height: 12px;
  background: white;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Contrôles webcam */
.webcam-controls {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

.btn-control {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 2rem;
  border: none;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  min-width: 140px;
  justify-content: center;
}

.btn-control:not(.active) {
  background: #374151;
  color: #e5e7eb;
}

.btn-control.active {
  background: linear-gradient(135deg, #4ade80, #22c55e);
  color: white;
}

.btn-control:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
}

.btn-record {
  background: linear-gradient(135deg, #ef4444, #dc2626) !important;
  color: white !important;
}

.btn-record.active {
  background: linear-gradient(135deg, #22c55e, #16a34a) !important;
}

/* Panneau de statistiques */
.stats-panel {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 2rem;
}

.stat-card {
  background: linear-gradient(135deg, #1a1f2e, #252a3a);
  border-radius: 16px;
  padding: 2rem;
  border: 1px solid #374151;
  display: flex;
  align-items: center;
  gap: 1.5rem;
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2);
  border-color: #4f9eff;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, #4f9eff, #60a5fa);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  color: white;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.stat-label {
  color: #9ca3af;
  font-size: 0.875rem;
  font-weight: 500;
}

/* Historique */
.history-filters {
  display: flex;
  gap: 2rem;
  margin-bottom: 2rem;
  justify-content: center;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.filter-group label {
  font-weight: 500;
  color: #d1d5db;
}

.filter-group select {
  padding: 0.5rem 1rem;
  border: 1px solid #374151;
  border-radius: 8px;
  background: #1a1f2e;
  color: #ffffff;
  font-size: 0.875rem;
}

.sessions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
}

.session-card {
  background: linear-gradient(135deg, #1a1f2e, #252a3a);
  border-radius: 16px;
  padding: 1.5rem;
  border: 1px solid #374151;
  transition: all 0.3s ease;
}

.session-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
  border-color: #4f9eff;
}

.session-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.session-date {
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

.session-status.active {
  background: rgba(34, 197, 94, 0.1);
  color: #4ade80;
}

.session-status.completed {
  background: rgba(156, 163, 175, 0.1);
  color: #9ca3af;
}

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

.btn-action:not(.btn-delete) {
  background: #374151;
  color: #e5e7eb;
}

.btn-action:hover:not(.btn-delete) {
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

/* Paramètres */
.settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 2rem;
}

.settings-section {
  background: linear-gradient(135deg, #1a1f2e, #252a3a);
  border-radius: 16px;
  padding: 2rem;
  border: 1px solid #374151;
}

.settings-section h3 {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
  color: #4f9eff;
  font-size: 1.25rem;
}

.setting-item {
  margin-bottom: 1.5rem;
}

.setting-item label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #d1d5db;
}

.setting-item input[type="text"],
.setting-item input[type="number"],
.setting-item select {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #374151;
  border-radius: 8px;
  background: #0f1419;
  color: #ffffff;
  font-size: 0.875rem;
}

.setting-item input[type="range"] {
  width: 100%;
  margin-top: 0.5rem;
}

.setting-item input[type="checkbox"] {
  margin-right: 0.5rem;
}

.btn-test {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, #4ade80, #22c55e);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-test:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(74, 222, 128, 0.3);
}

.system-info {
  background: rgba(15, 20, 25, 0.5);
  border-radius: 8px;
  padding: 1rem;
}

.info-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.75rem;
  font-size: 0.875rem;
}

.info-row:last-child {
  margin-bottom: 0;
}

.info-row span:first-child {
  color: #9ca3af;
}

.info-row span:last-child {
  font-weight: 500;
}

.info-row .connected {
  color: #4ade80;
}

.info-row .disconnected {
  color: #ef4444;
}

/* États spéciaux */
.loading-state,
.empty-state {
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

/* Responsive */
@media (max-width: 768px) {
  .nav-container {
    flex-direction: column;
    gap: 1rem;
  }
  
  .nav-menu {
    flex-wrap: wrap;
    justify-content: center;
  }
  
  .webcam-controls {
    flex-direction: column;
    align-items: center;
  }
  
  .btn-control {
    width: 100%;
    max-width: 300px;
  }
  
  .stats-panel {
    grid-template-columns: 1fr;
  }
  
  .history-filters {
    flex-direction: column;
    align-items: center;
  }
  
  .sessions-grid {
    grid-template-columns: 1fr;
  }
  
  .settings-grid {
    grid-template-columns: 1fr;
  }
}
</style>
