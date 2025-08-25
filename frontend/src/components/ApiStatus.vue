<script>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { api } from '../services/api'

export default {
  name: 'ApiStatus',
  setup() {
    const backendStatus = ref('disconnected')
    const modelStatus = ref('not-loaded')
    const lastCheck = ref('Jamais')

    async function checkStatus() {
      try {
        const response = await api.request('/health')
        backendStatus.value = 'connected'
        modelStatus.value = response.model_loaded ? 'loaded' : 'not-loaded'
        lastCheck.value = new Date().toLocaleTimeString('fr-FR')
      } catch (error) {
        backendStatus.value = 'disconnected'
        modelStatus.value = 'not-loaded'
        lastCheck.value = new Date().toLocaleTimeString('fr-FR')
      }
    }

    onMounted(() => {
      checkStatus()
      // Vérification automatique toutes les 5 secondes
      const interval = setInterval(checkStatus, 5000)
      
      // Nettoyage à la destruction du composant
      onBeforeUnmount(() => {
        clearInterval(interval)
      })
    })

    return {
      backendStatus,
      modelStatus,
      lastCheck,
      checkStatus
    }
  }
}
</script>

<template>
  <div class="api-status">
    <h3><i class="fas fa-plug"></i> État de l'API</h3>
    
    <div class="status-info">
      <div class="status-row">
        <span>Backend :</span>
        <span :class="backendStatus">{{ backendStatus === 'connected' ? 'Connecté' : 'Déconnecté' }}</span>
      </div>
      <div class="status-row">
        <span>Modèle IA :</span>
        <span>{{ modelStatus === 'loaded' ? 'Chargé' : 'Non chargé' }}</span>
      </div>
      <div class="status-row">
        <span>Dernière vérification :</span>
        <span>{{ lastCheck }}</span>
      </div>
      <div class="status-row">
        <span>Prochaine mise à jour :</span>
        <span class="update-indicator">🔄 Auto</span>
      </div>
    </div>
    
    <button class="btn-check" @click="checkStatus">
      <i class="fas fa-sync-alt"></i>
      Vérifier
    </button>
  </div>
</template>

<style scoped>
.api-status {
  background: linear-gradient(135deg, #1a1f2e, #252a3a);
  border-radius: 16px;
  padding: 2rem;
  border: 1px solid #374151;
}

.api-status h3 {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
  color: #4f9eff;
  font-size: 1.25rem;
}

.status-info {
  background: rgba(15, 20, 25, 0.5);
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1.5rem;
}

.status-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.75rem;
  font-size: 0.875rem;
}

.status-row:last-child {
  margin-bottom: 0;
}

.status-row span:first-child {
  color: #9ca3af;
}

.status-row span:last-child {
  font-weight: 500;
}

.status-row .connected {
  color: #4ade80;
}

.status-row .disconnected {
  color: #ef4444;
}

.btn-check {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, #4f9eff, #60a5fa);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-check:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(79, 158, 255, 0.3);
}

.update-indicator {
  color: #4f9eff;
  font-weight: 500;
}
</style>
