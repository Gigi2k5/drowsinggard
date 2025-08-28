<template>
  <div id="app">
    <!-- Modal d'authentification -->
    <AuthModal 
      v-if="showAuthModal" 
      :show="showAuthModal"
      @close="showAuthModal = false"
      @login-success="handleLoginSuccess"
    />
    
    <!-- Navigation principale (visible seulement après authentification) -->
    <nav class="navbar" v-if="isAuthenticated">
      <div class="nav-container">
        <div class="nav-brand">
          <i class="fas fa-shield-alt"></i>
          <span>DrowsiGuard</span>
  </div>
        
        <div class="nav-menu">
          <!-- Onglets pour utilisateurs normaux -->
          <template v-if="currentUser?.role !== 'admin'">
                      <button 
            @click="changeTab('monitor')" 
            :class="['nav-item', { active: activeTab === 'monitor' }]"
          >
            <i class="fas fa-video"></i>
            Surveillance
          </button>
          
          <button 
            @click="changeTab('history')" 
            :class="['nav-item', { active: activeTab === 'history' }]"
          >
            <i class="fas fa-history"></i>
            Historique
          </button>
          
          <button 
            @click="changeTab('settings')" 
            :class="['nav-item', { active: activeTab === 'settings' }]"
          >
            <i class="fas fa-cog"></i>
            Paramètres
          </button>
</template>

          <!-- Onglet Administration (admin uniquement) -->
          <template v-if="currentUser?.role === 'admin'">
                      <button 
            @click="changeTab('admin')" 
            :class="['nav-item', { active: activeTab === 'admin' }]"
          >
            <i class="fas fa-shield-alt"></i>
            Administration
          </button>
          </template>
        </div>
        
        <!-- Menu utilisateur -->
        <div class="nav-user">
          <div class="user-info">
            <span class="username">{{ currentUser?.username || 'Utilisateur' }}</span>
            <span class="user-role" :class="`role-${currentUser?.role || 'user'}`">
              {{ currentUser?.role === 'admin' ? 'Admin' : 'Utilisateur' }}
            </span>
          </div>
          <button @click="logout" class="btn-logout" title="Se déconnecter">
            <i class="fas fa-sign-out-alt"></i>
          </button>
        </div>
      </div>
    </nav>

    <!-- Contenu principal -->
    <main class="main-content">
      <!-- Page d'accueil (avant authentification) -->
      <LandingHero v-if="!isAuthenticated" @open-auth="openAuth" />

      <!-- Contenu pour utilisateurs normaux -->
      <template v-if="isAuthenticated && currentUser?.role !== 'admin'">
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
             <div style="margin-top: 4rem;">
               <PerformanceMonitor />
             </div>
          </div>
        </div>

        <!-- Onglet Historique -->
        <div v-if="activeTab === 'history'" class="tab-content">
          <HistorySection :user-role="currentUser?.role || 'user'" />
        </div>
        
        <!-- Onglet Paramètres -->
        <div v-if="activeTab === 'settings'" class="tab-content">
          <div class="settings-container">
            <header class="settings-header">
              <h1>Paramètres</h1>
              <p>Configuration de l'application et des alertes</p>
            </header>
            
            <div class="settings-content">
              <div class="settings-section">
                <h2>Paramètres Audio</h2>
                <div class="setting-item">
                  <label for="audio-enabled">Activer les alertes audio</label>
                  <input 
                    id="audio-enabled"
                    v-model="audioSettings.enabled" 
                    type="checkbox"
                  />
                </div>
                
                <div class="setting-item">
                  <label for="audio-volume">Volume des alertes</label>
                  <input 
                    id="audio-volume"
                    v-model="audioSettings.volume" 
                    type="range" 
                    min="0" 
                    max="100" 
                    step="10"
                />
                <span class="volume-value">{{ audioSettings.volume }}%</span>
              </div>
              
                             <div class="setting-item">
                 <label for="audio-frequency">Fréquence des alertes</label>
                 <select id="audio-frequency" v-model="audioSettings.frequency">
                   <option value="immediate">Immédiate</option>
                   <option value="5s">Toutes les 5 secondes</option>
                   <option value="10s">Toutes les 10 secondes</option>
                   <option value="30s">Toutes les 30 secondes</option>
                 </select>
               </div>
               
                               <div class="setting-item">
                  <label for="audio-type">Type d'alerte audio</label>
                  <select id="audio-type" v-model="audioSettings.type">
                    <option value="beep">Bip sonore</option>
                    <option value="chime">Carillon</option>
                    <option value="alert">Alerte</option>
                    <option value="custom">Personnalisé</option>
                  </select>
                </div>
                
                <!-- Input pour fichier audio personnalisé -->
                <div class="setting-item" v-if="audioSettings.type === 'custom'">
                  <label for="custom-audio">Fichier audio personnalisé</label>
                  <input 
                    id="custom-audio"
                    type="file" 
                    accept="audio/*"
                    @change="handleCustomAudioUpload"
                    class="file-input"
                  />
                  <div v-if="audioSettings.customAudioUrl" class="audio-preview">
                    <span class="audio-name">{{ audioSettings.customAudioName }}</span>
                    <button @click="removeCustomAudio" class="btn-remove" type="button">
                      <i class="fas fa-times"></i>
                    </button>
                  </div>
                </div>
                
                <div class="setting-item">
                  <button @click="testAudio" class="btn-test" type="button">
                    <i class="fas fa-volume-up"></i>
                    Tester l'audio
                  </button>
                </div>
            </div>
            
            <div class="settings-section">
              <h2>Paramètres de Détection</h2>
              <div class="setting-item">
                <label for="detection-sensitivity">Sensibilité de détection</label>
                <select id="detection-sensitivity" v-model="detectionSettings.sensitivity">
                  <option value="low">Faible</option>
                  <option value="medium">Moyenne</option>
                  <option value="high">Élevée</option>
                </select>
              </div>
              
              <div class="setting-item">
                <label for="detection-interval">Intervalle de capture (ms)</label>
                <input 
                  id="detection-interval"
                  v-model="detectionSettings.interval" 
                  type="number" 
                  min="100" 
                  max="5000" 
                  step="100"
                />
              </div>
            </div>
            
            <div class="settings-section">
              <h2>Informations du Compte</h2>
              <div class="account-info">
                <div class="info-item">
                  <span class="label">Nom d'utilisateur:</span>
                  <span>{{ currentUser?.username }}</span>
                </div>
                <div class="info-item">
                  <span class="label">Email:</span>
                  <span>{{ currentUser?.email }}</span>
                </div>
                <div class="info-item">
                  <span class="label">Rôle:</span>
                  <span :class="`role-${currentUser?.role}`">
                    {{ currentUser?.role === 'admin' ? 'Administrateur' : 'Utilisateur' }}
                  </span>
                </div>
                <div class="info-item">
                  <span class="label">Compte créé le:</span>
                  <span>{{ formatDate(currentUser?.created_at) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      </template>
      
      <!-- Contenu pour administrateurs -->
      <template v-if="currentUser?.role === 'admin'">
        <!-- Onglet Administration (admin uniquement) -->
        <div v-if="activeTab === 'admin'" class="tab-content">
          <AdminPanel />
        </div>
      </template>
    </main>
  </div>
</template>

<script>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import WebcamFeed from './components/WebcamFeed.vue'
import HistorySection from './components/HistorySection.vue'
import AdminPanel from './components/AdminPanel.vue'
import PerformanceMonitor from './components/PerformanceMonitor.vue'
import AuthModal from './components/AuthModal.vue'
import { api } from './services/api'
import LandingHero from './components/LandingHero.vue'

export default {
  name: 'App',
     components: {
     WebcamFeed,
     HistorySection,
     AdminPanel,
     PerformanceMonitor,
     AuthModal,
     LandingHero
   },
  setup() {
    // État de l'authentification
    const isAuthenticated = ref(false)
    const currentUser = ref(null)
    const showAuthModal = ref(false)
    
    // État de la navigation
    const activeTab = ref('monitor')
    
    // État de la surveillance
    const isStreaming = ref(false)
    const currentSessionId = ref(null)
    const sessionStartTime = ref(null)
    const sessionDuration = ref('00:00')
    const alertCount = ref(0)
    const avgLatency = ref(0)
    const latencyCount = ref(0)
    const totalLatency = ref(0)
    
    // Compteurs de prédictions pour l'historique
    const awakeCount = ref(0)
    const drowsyCount = ref(0)
    const totalConfidence = ref(0)
    const confidenceCount = ref(0)
    
         // État des paramètres
     const audioSettings = ref({
       enabled: true,
       volume: 50,
       frequency: 'immediate',
       type: 'beep',
       customAudioUrl: null,
       customAudioName: null
     })
    
    const detectionSettings = ref({
      sensitivity: 'medium',
      interval: 500
    })
    
    // Intervalles
    let sessionInterval = null
    
    // Vérifier l'authentification au démarrage
    onMounted(() => {
      checkAuthStatus()
    })
    
    // Nettoyer les intervalles
    onBeforeUnmount(() => {
      if (sessionInterval) {
        clearInterval(sessionInterval)
      }
    })
    
    // Fonctions d'authentification
    function checkAuthStatus() {
      const token = localStorage.getItem('authToken')
      const user = localStorage.getItem('user')
      
      if (token && user) {
        try {
          currentUser.value = JSON.parse(user)
          isAuthenticated.value = true
          // Forcer la redirection selon le rôle au chargement
          if (currentUser.value?.role === 'admin') {
            activeTab.value = 'admin'
          } else {
            activeTab.value = 'monitor'
          }
          // Vérifier la validité du token avec le serveur
          verifyToken()
        } catch (error) {
          console.error('Erreur parsing utilisateur:', error)
          logout()
        }
      } else {
        isAuthenticated.value = false
        showAuthModal.value = false
        activeTab.value = 'monitor'
      }
    }
    
    async function verifyToken() {
      try {
        await api.request('/auth/profile')
        // Token valide
      } catch (error) {
        console.error('Token invalide:', error)
        logout()
      }
    }
    
    function handleLoginSuccess(user) {
      currentUser.value = user
      isAuthenticated.value = true
      showAuthModal.value = false
      
      // Rediriger selon le rôle
      if (user.role === 'admin') {
        activeTab.value = 'admin'
      } else {
        activeTab.value = 'monitor'
      }
    }
    
    function changeTab(tabName) {
      // Vérifier les permissions selon le rôle
      if (currentUser.value?.role === 'admin') {
        // L'admin ne peut accéder qu'à l'administration
        if (tabName !== 'admin') {
          console.log('🔒 Accès refusé: L\'admin ne peut accéder qu\'à l\'administration')
          return
        }
      }
      
      activeTab.value = tabName
    }
    
    function logout() {
      localStorage.removeItem('authToken')
      localStorage.removeItem('user')
      currentUser.value = null
      isAuthenticated.value = false
      showAuthModal.value = false
      
      // Réinitialiser l'état
      stopSession()
      activeTab.value = 'monitor'
    }
    
    // Fonctions de surveillance
    function handleWebcamStatus(status) {
      console.log('Statut webcam:', status)
      
      if (status === 'started') {
        startSession()
      } else if (status === 'stopped') {
        stopSession()
      }
    }
    
    function startSession() {
      console.log('🚀 Nouvelle session démarrée avec l\'ID:', Date.now())
      currentSessionId.value = Date.now()
      sessionStartTime.value = Date.now()
      alertCount.value = 0
      avgLatency.value = 0
      latencyCount.value = 0
      totalLatency.value = 0
      
      // Réinitialiser les compteurs de prédictions
      awakeCount.value = 0
      drowsyCount.value = 0
      totalConfidence.value = 0
      confidenceCount.value = 0
      
      // Démarrer le timer de session
      sessionInterval = setInterval(() => {
        if (sessionStartTime.value) {
          const elapsed = Math.floor((Date.now() - sessionStartTime.value) / 1000)
          sessionDuration.value = formatDuration(elapsed)
        }
      }, 1000)
      
      console.log('▶️ Webcam démarrée - Surveillance activée')
    }
    
    function stopSession() {
      console.log('🛑 Session arrêtée - Stats réinitialisées: Alertes=' + alertCount.value + ', Latence=' + avgLatency.value + 'ms')
      
      if (sessionInterval) {
        clearInterval(sessionInterval)
        sessionInterval = null
      }
      
      // Sauvegarder la session si elle a duré plus de 5 secondes
      if (sessionStartTime.value && (Date.now() - sessionStartTime.value) > 5000) {
        saveSession()
      }
      
      // Réinitialiser les stats
      sessionDuration.value = '00:00'
      alertCount.value = 0
      avgLatency.value = 0
      currentSessionId.value = null
      sessionStartTime.value = null
      
      // Réinitialiser les compteurs de prédictions
      awakeCount.value = 0
      drowsyCount.value = 0
      totalConfidence.value = 0
      confidenceCount.value = 0
      
      console.log('⏹️ Webcam arrêtée - Stats réinitialisées')
    }
    
    function handleAlertDetected() {
      alertCount.value++
      console.log('Alerte détectée! Total:', alertCount.value)
      
      // Jouer une alerte audio si activée
      if (audioSettings.value.enabled) {
        playAlertSound()
      }
    }
    
    function handlePredictionUpdate(predictionData) {
      // Mettre à jour la latence
      if (predictionData.latency > 0) {
        totalLatency.value += predictionData.latency
        latencyCount.value++
        avgLatency.value = Math.round(totalLatency.value / latencyCount.value)
        console.log('⚡ Latence mise à jour:', avgLatency.value + 'ms')
      }
      
      // Compter les prédictions pour l'historique
      if (predictionData.prediction === 'awake') {
        awakeCount.value++
      } else if (predictionData.prediction === 'drowsy') {
        drowsyCount.value++
      }
      
      // Calculer la moyenne des confidences
      if (predictionData.confidence > 0) {
        totalConfidence.value += predictionData.confidence
        confidenceCount.value++
      }
    }
    
    async function handleFrameCaptured(frameData) {
      if (!isStreaming.value || !currentSessionId.value) {
        console.log('⚠️ Frame non enregistrée: webcam inactive ou pas de session ID')
        return
      }
      
      try {
        const response = await api.request('/save_frame', {
          method: 'POST',
          body: {
            session_id: null,
            client_session_id: frameData.sessionId,
            frame_data: frameData.frameData,
            prediction: frameData.prediction,
            confidence: frameData.confidence,
            timestamp: frameData.timestamp,
            frame_number: frameData.frameNumber
          }
        })
        
        if (response.success) {
          console.log('✅ Frame enregistrée avec succès pour la session', frameData.sessionId)
        } else {
          console.error('❌ Erreur enregistrement frame:', response.error)
        }
      } catch (error) {
        console.error('❌ Erreur API save_frame:', error)
      }
    }
    
    async function saveSession() {
      if (!sessionStartTime.value) return
      
      const endTime = Date.now()
      const duration = Math.floor((endTime - sessionStartTime.value) / 1000)
      
      const sessionData = {
        start_time: new Date(sessionStartTime.value).toISOString(),
        end_time: new Date(endTime).toISOString(),
        duration: duration,
        awake_count: awakeCount.value,
        drowsy_count: drowsyCount.value,
        alert_count: alertCount.value,
        avg_confidence: confidenceCount.value > 0 ? Math.round(totalConfidence.value / confidenceCount.value) : 0,
        client_session_id: currentSessionId.value
      }
      
      try {
        const response = await api.request('/save_session', {
          method: 'POST',
          body: sessionData
        })
        
        if (response.success) {
          console.log('✅ Session sauvegardée avec succès')
          // Mettre à jour l'ID de session avec celui retourné par le serveur
          currentSessionId.value = response.new_session_id
        } else {
          console.error('❌ Erreur sauvegarde session:', response.error)
        }
      } catch (error) {
        console.error('❌ Erreur API save_session:', error)
      }
    }
    
         function playAlertSound() {
       // Créer un contexte audio
       const audioContext = new (window.AudioContext || window.webkitAudioContext)()
       const oscillator = audioContext.createOscillator()
       const gainNode = audioContext.createGain()
       
       oscillator.connect(gainNode)
       gainNode.connect(audioContext.destination)
       
       // Configuration du son selon le type sélectionné
       const audioType = audioSettings.value.type
       const volume = audioSettings.value.volume / 100
       
       switch (audioType) {
         case 'beep':
           // Bip simple
           oscillator.frequency.setValueAtTime(800, audioContext.currentTime)
           oscillator.frequency.setValueAtTime(600, audioContext.currentTime + 0.1)
           oscillator.frequency.setValueAtTime(800, audioContext.currentTime + 0.2)
           break
           
         case 'chime':
           // Carillon mélodique
           oscillator.frequency.setValueAtTime(523, audioContext.currentTime) // Do
           oscillator.frequency.setValueAtTime(659, audioContext.currentTime + 0.1) // Mi
           oscillator.frequency.setValueAtTime(784, audioContext.currentTime + 0.2) // Sol
           break
           
         case 'alert':
           // Alerte d'urgence
           oscillator.frequency.setValueAtTime(1000, audioContext.currentTime)
           oscillator.frequency.setValueAtTime(800, audioContext.currentTime + 0.05)
           oscillator.frequency.setValueAtTime(1000, audioContext.currentTime + 0.1)
           oscillator.frequency.setValueAtTime(800, audioContext.currentTime + 0.15)
           oscillator.frequency.setValueAtTime(1000, audioContext.currentTime + 0.2)
           break
           
                   case 'custom':
            // Son personnalisé - utiliser le fichier audio chargé
            if (audioSettings.value.customAudioUrl) {
              // Créer un élément audio pour le fichier personnalisé
              const audio = new Audio(audioSettings.value.customAudioUrl)
              audio.volume = volume
              audio.play().catch(error => {
                console.error('Erreur lecture audio personnalisé:', error)
                // Fallback vers le son par défaut
                oscillator.frequency.setValueAtTime(800, audioContext.currentTime)
                oscillator.frequency.setValueAtTime(600, audioContext.currentTime + 0.1)
                oscillator.frequency.setValueAtTime(800, audioContext.currentTime + 0.2)
              })
              return // Sortir de la fonction car on utilise l'audio personnalisé
            } else {
              // Fallback si pas de fichier personnalisé
              oscillator.frequency.setValueAtTime(400, audioContext.currentTime)
              oscillator.frequency.setValueAtTime(600, audioContext.currentTime + 0.1)
              oscillator.frequency.setValueAtTime(800, audioContext.currentTime + 0.2)
              oscillator.frequency.setValueAtTime(600, audioContext.currentTime + 0.3)
              oscillator.frequency.setValueAtTime(400, audioContext.currentTime + 0.4)
            }
            break
           
         default:
           // Bip par défaut
           oscillator.frequency.setValueAtTime(800, audioContext.currentTime)
           oscillator.frequency.setValueAtTime(600, audioContext.currentTime + 0.1)
           oscillator.frequency.setValueAtTime(800, audioContext.currentTime + 0.2)
       }
       
       // Configuration du volume et de l'enveloppe
       gainNode.gain.setValueAtTime(0, audioContext.currentTime)
       gainNode.gain.linearRampToValueAtTime(volume, audioContext.currentTime + 0.05)
       gainNode.gain.linearRampToValueAtTime(0, audioContext.currentTime + 0.3)
       
       // Durée selon le type
       const duration = audioType === 'custom' ? 0.5 : 0.3
       
       oscillator.start(audioContext.currentTime)
       oscillator.stop(audioContext.currentTime + duration)
     }
     
           function testAudio() {
        // Fonction pour tester l'audio sans déclencher d'alerte
        console.log('🔊 Test audio avec type:', audioSettings.value.type)
        playAlertSound()
      }
      
      function handleCustomAudioUpload(event) {
        const file = event.target.files[0]
        if (file) {
          // Vérifier que c'est un fichier audio
          if (!file.type.startsWith('audio/')) {
            alert('Veuillez sélectionner un fichier audio valide')
            return
          }
          
          // Créer une URL pour le fichier
          const url = URL.createObjectURL(file)
          audioSettings.value.customAudioUrl = url
          audioSettings.value.customAudioName = file.name
          
          console.log('🎵 Audio personnalisé chargé:', file.name)
        }
      }
      
      function removeCustomAudio() {
        // Libérer l'URL de l'objet
        if (audioSettings.value.customAudioUrl) {
          URL.revokeObjectURL(audioSettings.value.customAudioUrl)
        }
        
        audioSettings.value.customAudioUrl = null
        audioSettings.value.customAudioName = null
        
        console.log('🗑️ Audio personnalisé supprimé')
      }
    
    function formatDuration(seconds) {
      const minutes = Math.floor(seconds / 60)
      const secs = seconds % 60
      return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
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

    function openAuth() {
      showAuthModal.value = true
    }
    
    return {
      // Authentification
      isAuthenticated,
      currentUser,
      showAuthModal,
      
      // Navigation
      activeTab,
      
      // Surveillance
      isStreaming,
      currentSessionId,
      sessionDuration,
      alertCount,
      avgLatency,
      awakeCount,
      drowsyCount,
      
      // Paramètres
      audioSettings,
      detectionSettings,
      
             // Composants
       WebcamFeed,
       HistorySection,
       AdminPanel,
       PerformanceMonitor,
       AuthModal,
       LandingHero,
      
      // Méthodes
      handleLoginSuccess,
      changeTab,
      logout,
      handleWebcamStatus,
      handleAlertDetected,
      handlePredictionUpdate,
             handleFrameCaptured,
       saveSession,
       playAlertSound,
       testAudio,
       handleCustomAudioUpload,
       removeCustomAudio,
       formatDuration,
       formatDate,
       openAuth
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
  flex-wrap: wrap;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 2rem;
  font-weight: 700;
  color: #4f9eff;
}

.nav-brand i {
  font-size: 2.25rem;
}

.nav-menu {
  display: flex;
  gap: 0.5rem;
  justify-content: center;
  flex: 1;
  margin: 0 2rem;
  flex-wrap: wrap;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 1rem;
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

/* Navigation utilisateur */
.nav-user {
  display: flex;
  align-items: center;
  gap: 1rem;
  justify-content: flex-end;
}

.user-info {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.25rem;
  margin-right: 1rem;
}

.username {
  color: #ffffff;
  font-weight: 600;
  font-size: 0.875rem;
}

.user-role {
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
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

.btn-logout {
  background: none;
  border: 1px solid #374151;
  color: #9ca3af;
  padding: 0.5rem;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-logout:hover {
  border-color: #ef4444;
  color: #ef4444;
}

/* Contenu principal */
 .main-content {
   flex: 1;
   padding: 4rem 2rem;
   display: flex;
   flex-direction: column;
   align-items: center;
 }

 .tab-content {
   max-width: 1200px;
   width: 100%;
   margin: 0 auto;
   padding: 0 2rem;
   display: flex;
   flex-direction: column;
   align-items: center;
 }

/* En-têtes de section */
.monitor-header,
.history-header,
 .settings-header {
   text-align: center;
   margin-bottom: 5rem;
   padding: 3rem 0;
   width: 100%;
   max-width: 800px;
 }

.monitor-header h1,
.history-header h1,
.settings-header h1 {
  font-size: 3rem;
  font-weight: 700;
  margin-bottom: 1rem;
  background: linear-gradient(135deg, #ffffff, #e5e7eb);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.025em;
}

.monitor-header p,
.history-header p,
.settings-header p {
  font-size: 1.25rem;
  color: #9ca3af;
  font-weight: 400;
  line-height: 1.6;
}

/* Zone webcam */
.webcam-zone {
  margin-bottom: 4rem;
  width: 100%;
  max-width: 800px;
}

.webcam-container {
  position: relative;
  background: #1a1f2e;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  border: 1px solid #374151;
  margin-bottom: 3rem;
  padding: 2rem;
  width: 100%;
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
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 2.5rem;
  margin-top: 3rem;
  width: 100%;
  max-width: 1000px;
}

.stat-card {
  background: linear-gradient(135deg, #1a1f2e, #252a3a);
  border-radius: 20px;
  padding: 2.5rem;
  border: 1px solid #374151;
  display: flex;
  align-items: center;
  gap: 2rem;
  transition: all 0.3s ease;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2);
  border-color: #4f9eff;
}

.stat-icon {
  width: 70px;
  height: 70px;
  border-radius: 50%;
  background: linear-gradient(135deg, #4f9eff, #60a5fa);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.75rem;
  color: white;
  box-shadow: 0 8px 20px rgba(79, 158, 255, 0.3);
  flex-shrink: 0;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 2.25rem;
  font-weight: 700;
  margin-bottom: 0.75rem;
  color: #ffffff;
}

.stat-label {
  color: #9ca3af;
  font-size: 0.95rem;
  font-weight: 500;
  letter-spacing: 0.025em;
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
   padding: 1rem 2rem;
   background: linear-gradient(135deg, #4ade80, #22c55e);
   color: white;
   border: none;
   border-radius: 12px;
   font-weight: 600;
   font-size: 1rem;
   cursor: pointer;
   transition: all 0.3s ease;
   box-shadow: 0 4px 15px rgba(74, 222, 128, 0.2);
 }

 .btn-test:hover {
   transform: translateY(-3px);
   box-shadow: 0 8px 25px rgba(74, 222, 128, 0.4);
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

/* Paramètres */
 .settings-content {
   max-width: 900px;
   margin: 0 auto;
   padding: 0 1rem;
 }

 .settings-section {
   background: linear-gradient(135deg, #1a1f2e, #252a3a);
   border-radius: 20px;
   padding: 2.5rem;
   border: 1px solid #374151;
   margin-bottom: 3rem;
   box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
   transition: all 0.3s ease;
 }
 
 .settings-section:hover {
   transform: translateY(-2px);
   box-shadow: 0 15px 40px rgba(0, 0, 0, 0.3);
   border-color: #4f9eff;
 }

 .settings-section h2 {
   color: #ffffff;
   margin: 0 0 2rem 0;
   font-size: 1.75rem;
   font-weight: 600;
   display: flex;
   align-items: center;
   gap: 0.75rem;
 }
 
 .settings-section h2::before {
   content: '';
   width: 4px;
   height: 24px;
   background: linear-gradient(135deg, #4f9eff, #60a5fa);
   border-radius: 2px;
 }

 .setting-item {
   display: flex;
   align-items: center;
   gap: 1.5rem;
   margin-bottom: 1.5rem;
   padding: 1.5rem;
   background: rgba(15, 20, 25, 0.5);
   border-radius: 12px;
   border: 1px solid #374151;
   transition: all 0.3s ease;
 }
 
 .setting-item:hover {
   border-color: #4f9eff;
   background: rgba(15, 20, 25, 0.7);
 }

 .setting-item label {
   color: #d1d5db;
   font-weight: 500;
   min-width: 220px;
   font-size: 0.95rem;
 }

 .setting-item input[type="checkbox"] {
   width: 22px;
   height: 22px;
   accent-color: #4f9eff;
   cursor: pointer;
 }

 .setting-item input[type="range"] {
   flex: 1;
   height: 8px;
   border-radius: 4px;
   background: #374151;
   outline: none;
   cursor: pointer;
   margin: 0 1rem;
 }

 .setting-item input[type="range"]::-webkit-slider-thumb {
   appearance: none;
   width: 20px;
   height: 20px;
   border-radius: 50%;
   background: #4f9eff;
   cursor: pointer;
   box-shadow: 0 2px 6px rgba(79, 158, 255, 0.3);
   transition: all 0.2s ease;
 }
 
 .setting-item input[type="range"]::-webkit-slider-thumb:hover {
   transform: scale(1.1);
   box-shadow: 0 4px 12px rgba(79, 158, 255, 0.4);
 }

 .setting-item select {
   padding: 0.75rem 1rem;
   border: 1px solid #374151;
   border-radius: 8px;
   background: #0f1419;
   color: #ffffff;
   font-size: 0.875rem;
   cursor: pointer;
   min-width: 150px;
   transition: all 0.2s ease;
 }
 
 .setting-item select:hover {
   border-color: #4f9eff;
   background: #1a1f2e;
 }
 
 .setting-item select:focus {
   outline: none;
   border-color: #4f9eff;
   box-shadow: 0 0 0 3px rgba(79, 158, 255, 0.1);
 }

 .setting-item input[type="number"] {
   padding: 0.75rem 1rem;
   border: 1px solid #374151;
   border-radius: 8px;
   background: #0f1419;
   color: #ffffff;
   font-size: 0.875rem;
   width: 140px;
   text-align: center;
   transition: all 0.2s ease;
 }
 
 .setting-item input[type="number"]:hover {
   border-color: #4f9eff;
   background: #1a1f2e;
 }
 
 .setting-item input[type="number"]:focus {
   outline: none;
   border-color: #4f9eff;
   box-shadow: 0 0 0 3px rgba(79, 158, 255, 0.1);
 }

 .volume-value {
   color: #4f9eff;
   font-weight: 600;
   min-width: 80px;
   text-align: center;
   font-size: 1rem;
   padding: 0.5rem 1rem;
   background: rgba(79, 158, 255, 0.1);
   border-radius: 6px;
   border: 1px solid rgba(79, 158, 255, 0.2);
 }
 
 /* Styles pour l'audio personnalisé */
 .file-input {
   padding: 0.5rem;
   border: 1px solid #374151;
   border-radius: 6px;
   background: #0f1419;
   color: #ffffff;
   font-size: 0.875rem;
   cursor: pointer;
   width: 100%;
 }
 
 .file-input::-webkit-file-upload-button {
   background: #4f9eff;
   color: white;
   border: none;
   padding: 0.5rem 1rem;
   border-radius: 4px;
   cursor: pointer;
   margin-right: 1rem;
 }
 
 .file-input::-webkit-file-upload-button:hover {
   background: #3b82f6;
 }
 
 .audio-preview {
   display: flex;
   align-items: center;
   gap: 0.75rem;
   margin-top: 0.5rem;
   padding: 0.5rem;
   background: rgba(79, 158, 255, 0.1);
   border: 1px solid #4f9eff;
   border-radius: 6px;
 }
 
 .audio-name {
   color: #4f9eff;
   font-size: 0.875rem;
   font-weight: 500;
   flex: 1;
 }
 
 .btn-remove {
   background: none;
   border: none;
   color: #ef4444;
   cursor: pointer;
   padding: 0.25rem;
   border-radius: 4px;
   transition: all 0.2s ease;
 }
 
 .btn-remove:hover {
   background: rgba(239, 68, 68, 0.1);
 }

 .account-info {
   display: flex;
   flex-direction: column;
   gap: 1.5rem;
   margin-top: 1rem;
 }

 .info-item {
   display: flex;
   justify-content: space-between;
   align-items: center;
   padding: 1rem 1.5rem;
   background: rgba(15, 20, 25, 0.5);
   border-radius: 8px;
   border: 1px solid #374151;
   transition: all 0.2s ease;
 }
 
 .info-item:hover {
   background: rgba(15, 20, 25, 0.7);
   border-color: #4f9eff;
   transform: translateX(4px);
 }

 .info-item .label {
   color: #9ca3af;
   font-size: 0.9rem;
   font-weight: 500;
 }

 .info-item span:last-child {
   color: #d1d5db;
   font-weight: 600;
   font-size: 0.95rem;
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
  .nav-container { flex-direction: column; gap: 0.75rem; padding: 0.75rem 1rem; }
  .nav-brand { font-size: 1.5rem; }
  .nav-brand i { font-size: 1.75rem; }
  .nav-menu { width: 100%; margin: 0; gap: 0.5rem; justify-content: center; }
  .nav-item { padding: 0.5rem 0.75rem; font-size: 0.9rem; }
  .nav-user { width: 100%; justify-content: center; }
  
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
    gap: 1rem;
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

@media (max-width: 480px) {
  .nav-item i { display: none; }
  .nav-item { padding: 0.45rem 0.65rem; font-size: 0.85rem; }
  .monitor-header h1, .history-header h1, .settings-header h1 { font-size: 2rem; }
  .monitor-header p, .history-header p, .settings-header p { font-size: 1rem; }
  .stat-value { font-size: 1.75rem; }
  .stat-icon { width: 56px; height: 56px; font-size: 1.25rem; }
  .webcam-container { padding: 1rem; }
}
</style>
