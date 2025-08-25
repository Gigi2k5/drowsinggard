<script>
import { ref, onBeforeUnmount } from 'vue'
import { api } from '../services/api'

export default {
  name: 'FaceDetectionTest',
  setup() {
    const videoElement = ref(null)
    const isStreaming = ref(false)
    const capturedImage = ref(null)
    const testResults = ref(null)
    const loading = ref(false)
    let stream = null

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
        }
      } catch (error) {
        console.error('Erreur webcam:', error)
        alert('Impossible d\'accéder à la webcam')
      }
    }

    function stopWebcam() {
      if (stream) {
        stream.getTracks().forEach(track => track.stop())
        stream = null
      }
      
      if (videoElement.value) {
        videoElement.value.srcObject = null
      }
      
      isStreaming.value = false
      capturedImage.value = null
    }

    function captureImage() {
      if (!videoElement.value) return
      
      const canvas = document.createElement('canvas')
      canvas.width = videoElement.value.videoWidth
      canvas.height = videoElement.value.videoHeight
      
      const ctx = canvas.getContext('2d')
      ctx.drawImage(videoElement.value, 0, 0)
      
      capturedImage.value = canvas.toDataURL('image/jpeg', 0.8)
    }

    async function runTest() {
      if (!capturedImage.value) return
      
      loading.value = true
      testResults.value = null
      
      try {
        const response = await api.request('/face_detection_test', {
          method: 'POST',
          body: JSON.stringify({ image: capturedImage.value })
        })
        
        testResults.value = response
      } catch (error) {
        console.error('Erreur test détection faciale:', error)
        alert('Erreur lors du test de détection faciale')
      } finally {
        loading.value = false
      }
    }

    function getResultClass(result) {
      if (!result) return ''
      return result.success ? 'success' : 'error'
    }

    onBeforeUnmount(() => {
      stopWebcam()
    })

    return {
      videoElement,
      isStreaming,
      capturedImage,
      testResults,
      loading,
      toggleWebcam,
      captureImage,
      runTest,
      getResultClass
    }
  }
}
</script>

<template>
  <div class="face-detection-test">
    <h3><i class="fas fa-user-check"></i> Test de Détection Faciale</h3>
    
    <div class="test-container">
      <div class="webcam-preview">
        <video 
          ref="videoElement" 
          autoplay 
          muted 
          playsinline
          class="preview-video"
        />
        
        <div v-if="isStreaming" class="capture-overlay">
          <button class="btn-capture" @click="captureImage">
            <i class="fas fa-camera"></i>
            Capturer
          </button>
        </div>
      </div>
      
      <div class="test-controls">
        <button 
          @click="toggleWebcam" 
          :class="['btn-control', { active: isStreaming }]"
        >
          <i :class="isStreaming ? 'fas fa-stop' : 'fas fa-play'"></i>
          {{ isStreaming ? 'Arrêter' : 'Démarrer' }} Webcam
        </button>
        
        <button 
          @click="runTest" 
          class="btn-test"
          :disabled="!capturedImage"
        >
          <i class="fas fa-play"></i>
          Lancer le Test
        </button>
      </div>
    </div>
    
    <!-- Résultats du test -->
    <div v-if="testResults" class="test-results">
      <h4>Résultats du Test :</h4>
      
      <div class="results-grid">
        <div class="result-card" :class="getResultClass(testResults.mtcnn)">
          <div class="result-header">
            <i class="fas fa-brain"></i>
            <span>MTCNN</span>
          </div>
          <div class="result-content">
            <div class="result-status">
              {{ testResults.mtcnn.success ? '✅' : '❌' }}
              {{ testResults.mtcnn.success ? `${testResults.mtcnn.faces} visage(s) détecté(s)` : 'Échec' }}
            </div>
            <div v-if="testResults.mtcnn.error" class="result-error">
              {{ testResults.mtcnn.error }}
            </div>
          </div>
        </div>
        
        <div class="result-card" :class="getResultClass(testResults.opencv)">
          <div class="result-header">
            <i class="fas fa-eye"></i>
            <span>OpenCV</span>
          </div>
          <div class="result-content">
            <div class="result-status">
              {{ testResults.opencv.success ? '✅' : '❌' }}
              {{ testResults.opencv.success ? `${testResults.opencv.faces} visage(s) détecté(s)` : 'Échec' }}
            </div>
            <div v-if="testResults.opencv.error" class="result-error">
              {{ testResults.opencv.error }}
            </div>
          </div>
        </div>
      </div>
      
      <div class="test-info">
        <div class="info-row">
          <span>Taille image :</span>
          <span>{{ testResults.image_width }} x {{ testResults.image_height }}</span>
        </div>
        <div class="info-row">
          <span>Détection activée :</span>
          <span>{{ testResults.face_detection_enabled ? '✅ Oui' : '❌ Non' }}</span>
        </div>
      </div>
    </div>
    
    <!-- État de chargement -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Test en cours...</p>
    </div>
  </div>
</template>

<style scoped>
.face-detection-test {
  background: linear-gradient(135deg, #1a1f2e, #252a3a);
  border-radius: 16px;
  padding: 2rem;
  border: 1px solid #374151;
}

.face-detection-test h3 {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
  color: #4f9eff;
  font-size: 1.25rem;
}

.test-container {
  margin-bottom: 2rem;
}

.webcam-preview {
  position: relative;
  background: #1a1f2e;
  border-radius: 16px;
  overflow: hidden;
  margin-bottom: 1.5rem;
  border: 1px solid #374151;
}

.preview-video {
  width: 100%;
  height: auto;
  display: block;
}

.capture-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.webcam-preview:hover .capture-overlay {
  opacity: 1;
}

.btn-capture {
  background: linear-gradient(135deg, #4ade80, #22c55e);
  color: white;
  border: none;
  padding: 1rem 2rem;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  transition: all 0.3s ease;
}

.btn-capture:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(74, 222, 128, 0.3);
}

.test-controls {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

.btn-control,
.btn-test {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
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

.btn-test {
  background: linear-gradient(135deg, #4f9eff, #60a5fa);
  color: white;
}

.btn-test:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-control:hover:not(.active),
.btn-test:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
}

.test-results {
  background: rgba(15, 20, 25, 0.5);
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}

.test-results h4 {
  margin: 0 0 1rem 0;
  color: #ffffff;
  font-size: 1.125rem;
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.result-card {
  background: rgba(15, 20, 25, 0.8);
  border-radius: 8px;
  padding: 1rem;
  border: 1px solid #374151;
  transition: all 0.3s ease;
}

.result-card.success {
  border-color: #4ade80;
  background: rgba(74, 222, 128, 0.1);
}

.result-card.error {
  border-color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

.result-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
  font-weight: 600;
  color: #4f9eff;
}

.result-content {
  color: #d1d5db;
  font-size: 0.875rem;
}

.result-status {
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.result-error {
  color: #ef4444;
  font-size: 0.75rem;
}

.test-info {
  background: rgba(15, 20, 25, 0.8);
  border-radius: 8px;
  padding: 1rem;
}

.info-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
}

.info-row:last-child {
  margin-bottom: 0;
}

.info-row span:first-child {
  color: #9ca3af;
}

.info-row span:last-child {
  color: #d1d5db;
  font-weight: 500;
}

.loading-state {
  text-align: center;
  padding: 3rem 2rem;
  color: #9ca3af;
}

.spinner {
  width: 50px;
  height: 50px;
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

@media (max-width: 768px) {
  .test-controls {
    flex-direction: column;
    align-items: center;
  }
  
  .btn-control,
  .btn-test {
    width: 100%;
    max-width: 300px;
  }
  
  .results-grid {
    grid-template-columns: 1fr;
  }
}
</style>
