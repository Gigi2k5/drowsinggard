<template>
  <div class="webcam-feed">
    <div class="webcam-container">
      <video 
        ref="videoElement" 
        autoplay 
        muted 
        playsinline
        class="webcam-video"
      />
      
      <!-- Overlay de statut -->
      <div class="status-overlay" v-if="isStreaming">
        <div class="status-indicator" :class="currentStatus">
          <i :class="statusIcon"></i>
          <span>{{ statusText }}</span>
        </div>
      </div>
    </div>

    <!-- Contrôles -->
    <div class="webcam-controls">
      <button 
        @click="toggleWebcam" 
        :class="['btn-control', { active: isStreaming }]"
      >
        <i :class="isStreaming ? 'fas fa-stop' : 'fas fa-play'"></i>
        {{ isStreaming ? 'Arrêter' : 'Démarrer' }}
      </button>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { api } from '../services/api'

export default {
  name: 'WebcamFeed',
  props: {
    modelValue: {
      type: Boolean,
      default: false
    },
    sessionId: {
      type: Number,
      default: null
    },
    // Nombre de frames à ignorer après le démarrage (warm-up)
    warmUpFrames: {
      type: Number,
      default: 5
    },
    // Seuil utilisé côté serveur pour considérer 'drowsy' (envoyé à l'API)
    threshold: {
      type: Number,
      default: 0.65
    },
    // Taille de la fenêtre (buffer) demandée côté serveur pour la décision finale
    bufferSize: {
      type: Number,
      default: 7
    }
    ,
    // Nombre de secondes consécutives requises pour déclencher une alerte
    alertDebounceSeconds: {
      type: Number,
      default: 3
    },
    // Envoi automatique des frames capturées vers l'API /save_frame (requiert authentification)
    autoSaveFrames: {
      type: Boolean,
      default: true
    }
  },
  emits: ['update:modelValue', 'status-update', 'alert-detected', 'alert-cleared', 'prediction-update', 'frame-captured'],
  setup(props, { emit }) {
    const videoElement = ref(null)
    const isStreaming = ref(false)
    const currentStatus = ref('awake')
    let stream = null
    let frameCounter = 0
    let warmupCount = 0
    // Variables pour debounce/agrégation des alertes
    let drowsyStreak = 0
    let alertActive = false
  // Identifiant client pour lier les frames avant que le backend retourne un session_id
  let clientSessionId = null

    // Computed properties
    const statusText = computed(() => {
      switch (currentStatus.value) {
        case 'awake': return 'Éveillé'
        case 'drowsy': return 'Somnolent'
        case 'alert': return 'Alerte !'
        default: return 'Inconnu'
      }
    })

    const statusIcon = computed(() => {
      switch (currentStatus.value) {
        case 'awake': return 'fas fa-eye'
        case 'drowsy': return 'fas fa-eye-slash'
        case 'alert': return 'fas fa-exclamation-triangle'
        default: return 'fas fa-question'
      }
    })

    // Méthodes
    async function toggleWebcam() {
      if (isStreaming.value) {
        stopWebcam()
      } else {
        await startWebcam()
      }
    }

    async function startWebcam() {
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 640, height: 480 },
          audio: false
        })
        
        if (videoElement.value) {
          videoElement.value.srcObject = stream
          // Attendre que les métadonnées vidéo soient disponibles pour obtenir des dimensions non nulles
          await new Promise(resolve => {
            if (videoElement.value.readyState >= 1 && videoElement.value.videoWidth > 0) {
              resolve()
            } else {
              videoElement.value.onloadedmetadata = () => resolve()
            }
          })
          await videoElement.value.play()
          isStreaming.value = true
          // Réinitialiser le compteur de frames pour une nouvelle session
          frameCounter = 0
          warmupCount = 0
          // Reset alert debounce state
          drowsyStreak = 0
          alertActive = false
          // Générer un clientSessionId pour lier les frames si pas de sessionId immediate
          try {
            if (props.sessionId) {
              clientSessionId = null
            } else if (window.crypto && typeof window.crypto.randomUUID === 'function') {
              clientSessionId = window.crypto.randomUUID()
            } else {
              // Fallback UUIDv4 simple
              clientSessionId = 'xxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
                const r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
                return v.toString(16);
              })
            }
            console.log('🔑 clientSessionId généré:', clientSessionId)
            
            // Émettre le clientSessionId vers le parent pour qu'il puisse sauvegarder la session avec
            emit('client-session-created', clientSessionId)
          } catch (e) {
            console.warn('⚠️ Impossible de générer clientSessionId:', e)
            clientSessionId = null
          }
          // Démarrer (ou redémarrer) l'intervalle de surveillance si nécessaire
          if (!statusInterval) startStatusInterval()
          emit('update:modelValue', true)
          emit('status-update', 'started')
        }
      } catch (error) {
        console.error('Erreur webcam:', error)
        alert('Impossible d\'accéder à la webcam')
      }
    }

    function stopWebcam() {
      // Arrêter l'intervalle de surveillance
      if (statusInterval) {
        clearInterval(statusInterval)
        statusInterval = null
        console.log('🛑 Intervalle de surveillance arrêté')
      }
      
      if (stream) {
        stream.getTracks().forEach(track => track.stop())
        stream = null
      }
      
      if (videoElement.value) {
        videoElement.value.srcObject = null
      }
      
      isStreaming.value = false
      // Reset alert debounce state when stopping
      drowsyStreak = 0
      alertActive = false
      emit('update:modelValue', false)
      emit('status-update', 'stopped')
    }

    // Lifecycle
    let statusInterval = null

    function startStatusInterval() {
      if (statusInterval) return

      // Surveillance automatique du statut toutes les 500ms pour du vrai temps réel
      statusInterval = setInterval(async () => {
        if (isStreaming.value) {
          try {
            // Capturer une image de la webcam
            const canvas = document.createElement('canvas')
            const video = videoElement.value
            const videoWidth = (video && video.videoWidth) ? video.videoWidth : 640
            const videoHeight = (video && video.videoHeight) ? video.videoHeight : 480

            // Éviter les captures 1x1 lorsque la vidéo n'est pas prête
            if (videoWidth < 2 || videoHeight < 2) {
              console.warn('⏳ Vidéo non prête, capture ignorée (dimensions:', videoWidth, 'x', videoHeight, ')')
              return
            }

            canvas.width = videoWidth
            canvas.height = videoHeight
            const ctx = canvas.getContext('2d')
            ctx.drawImage(video, 0, 0, videoWidth, videoHeight)

            // Convertir en base64
            const imageData = canvas.toDataURL('image/jpeg', 0.8)

            // Warm-up: ignorer les premières frames pour laisser la caméra se stabiliser
            if (warmupCount < props.warmUpFrames) {
              warmupCount++
              console.log(`🔁 Warm-up frame ${warmupCount}/${props.warmUpFrames} ignorée`)
              return
            }

            // Envoyer à l'API de prédiction (on passe threshold et buffer_size configurables)
            const response = await api.predict(imageData, { threshold: props.threshold, buffer_size: props.bufferSize })

            if (response.success) {
              const newStatus = response.prediction
              currentStatus.value = newStatus

              // Debounce/Agrégation des alertes : n'alerter que si drowsy > X secondes consécutives
              const intervalSec = 0.5 // intervalle de capture fixé à 500ms
              const requiredFrames = Math.ceil(props.alertDebounceSeconds / intervalSec)
              if (newStatus === 'drowsy') {
                drowsyStreak++
              } else {
                drowsyStreak = 0
              }

              if (!alertActive && drowsyStreak >= requiredFrames) {
                alertActive = true
                emit('alert-detected', 'drowsy')
              }

              // Si on était en alerte et que l'état redevient awake, on peut émettre clear
              if (alertActive && newStatus === 'awake') {
                alertActive = false
                emit('alert-cleared')
              }

              // Émettre toutes les données de prédiction pour la latence en temps réel
              emit('prediction-update', {
                prediction: newStatus,
                confidence: response.confidence,
                latency: response.latency_ms,
                timestamp: new Date().toISOString()
              })

              // Log pour debug
              console.log(`🔍 Prédiction IA: ${newStatus} (confiance: ${response.confidence}%, latence: ${response.latency_ms}ms)`)

              // Construire un payload complet et normalisé (toujours envoyer client_session_id)
              const frameData = {
                session_id: props.sessionId || null,
                client_session_id: clientSessionId || null,
                frame_data: imageData || null,
                timestamp: Math.floor(Date.now() / 1000), // timestamp en secondes
                prediction: newStatus || 'unknown',
                confidence: response.confidence != null ? response.confidence : 0,
                frame_number: ++frameCounter // numéro de frame incrémental
              }

              // Log client avant envoi pour corrélation avec les logs serveur
              try {
                console.log('📸 Envoi frame -> keys:', Object.keys(frameData), 'session_id:', frameData.session_id, 'client_session_id:', frameData.client_session_id, 'frame_number:', frameData.frame_number)
              } catch (e) {
                // ignore logging errors
              }

              // Émettre vers le parent
              emit('frame-captured', frameData)

              // Envoi automatique vers l'API backend si activé
              if (props.autoSaveFrames) {
                api.saveFrame(frameData).catch(err => {
                  console.warn('⚠️ Envoi frame échoué:', err && err.message ? err.message : err)
                })
              }
            }
          } catch (error) {
            console.error('Erreur prédiction IA:', error)
            // En cas d'erreur, garder le statut actuel
          }
        }
      }, 500) // 500ms = 2 FPS pour du vrai temps réel
    }

    onMounted(() => {
      console.log('🔍 WebcamFeed monté avec sessionId:', props.sessionId)
    })
    
    onBeforeUnmount(() => {
      if (statusInterval) {
        clearInterval(statusInterval)
        statusInterval = null
      }
      stopWebcam()
    })

    return {
      videoElement,
      isStreaming,
      currentStatus,
      statusText,
      statusIcon,
      toggleWebcam
    }
  }
}
</script>

<style scoped>
.webcam-feed {
  width: 100%;
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

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.webcam-controls {
  display: flex;
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
  background: linear-gradient(135deg, #ef4444, #dc2626);
  color: white;
}

.btn-control:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
}
</style>
