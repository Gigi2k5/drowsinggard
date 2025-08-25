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
    }
  },
  emits: ['update:modelValue', 'status-update', 'alert-detected', 'prediction-update', 'frame-captured'],
  setup(props, { emit }) {
    const videoElement = ref(null)
    const isStreaming = ref(false)
    const currentStatus = ref('awake')
    let stream = null

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
          await videoElement.value.play()
          isStreaming.value = true
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
      emit('update:modelValue', false)
      emit('status-update', 'stopped')
    }

    // Lifecycle
    let statusInterval = null
    
    onMounted(() => {
      console.log('🔍 WebcamFeed monté avec sessionId:', props.sessionId)
      
      // Surveillance automatique du statut toutes les 500ms pour du vrai temps réel
      statusInterval = setInterval(async () => {
        if (isStreaming.value) {
          try {
            // Capturer une image de la webcam
            const canvas = document.createElement('canvas')
            canvas.width = videoElement.value.videoWidth
            canvas.height = videoElement.value.videoHeight
            const ctx = canvas.getContext('2d')
            ctx.drawImage(videoElement.value, 0, 0)
            
            // Convertir en base64
            const imageData = canvas.toDataURL('image/jpeg', 0.8)
            
            // Envoyer à l'API de prédiction
            const response = await api.request('/predict', {
              method: 'POST',
              body: JSON.stringify({ image: imageData })
            })
            
            if (response.success) {
              const newStatus = response.prediction
              currentStatus.value = newStatus
              
              // Émettre une alerte si détectée
              if (newStatus === 'drowsy' || newStatus === 'alert') {
                emit('alert-detected', newStatus)
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
              
              // Émettre l'événement frame-captured pour l'enregistrement
              if (props.sessionId) {
                const frameData = {
                  sessionId: props.sessionId,
                  frameData: imageData,
                  timestamp: Date.now() / 1000, // timestamp en secondes
                  prediction: newStatus,
                  confidence: response.confidence,
                  frameNumber: Date.now() // numéro de frame basé sur le timestamp
                }
                
                console.log('📸 Émission frame-captured:', {
                  sessionId: frameData.sessionId,
                  prediction: frameData.prediction,
                  confidence: frameData.confidence,
                  timestamp: frameData.timestamp
                })
                
                emit('frame-captured', frameData)
              } else {
                console.log('⚠️ Pas de sessionId, frame non émise')
              }
            }
          } catch (error) {
            console.error('Erreur prédiction IA:', error)
            // En cas d'erreur, garder le statut actuel
          }
        }
      }, 500) // 500ms = 2 FPS pour du vrai temps réel
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
