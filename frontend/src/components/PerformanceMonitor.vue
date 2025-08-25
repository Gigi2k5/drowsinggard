<script>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { api } from '../services/api'

export default {
  name: 'PerformanceMonitor',
  setup() {
    const metrics = ref(null)
    const loading = ref(false)
    const error = ref(null)

    async function loadMetrics() {
      loading.value = true
      error.value = null
      
      try {
        const response = await api.request('/performance')
        // Ajouter un timestamp pour voir les mises à jour
        response.last_update = new Date().toLocaleTimeString('fr-FR')
        metrics.value = response
        console.log('📊 Métriques mises à jour:', response)
      } catch (err) {
        error.value = 'Erreur lors du chargement des métriques'
        console.error('Erreur performance:', err)
      } finally {
        loading.value = false
      }
    }

    onMounted(() => {
      loadMetrics()
      // Mise à jour automatique toutes les 15 secondes (moins fréquent)
      const interval = setInterval(loadMetrics, 15000)
      
      // Nettoyage à la destruction du composant
      onBeforeUnmount(() => {
        clearInterval(interval)
      })
    })

    return {
      metrics,
      loading,
      error,
      loadMetrics
    }
  }
}
</script>

<template>
  <div class="performance-monitor">
    <h3><i class="fas fa-chart-line"></i> Moniteur de Performance</h3>
    
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Chargement des métriques...</p>
    </div>
    
    <div v-else-if="error" class="error-state">
      <i class="fas fa-exclamation-triangle"></i>
      <p>{{ error }}</p>
      <button class="btn-retry" @click="loadMetrics">
        <i class="fas fa-redo"></i>
        Réessayer
      </button>
    </div>
    
    <div v-else-if="metrics" class="metrics-grid">
             <div class="metric-card">
         <div class="metric-icon">
           <i class="fas fa-database"></i>
         </div>
         <div class="metric-content">
           <div class="metric-value">{{ metrics.cache?.size || 0 }}</div>
           <div class="metric-label">Cache Size</div>
         </div>
       </div>
      
             <div class="metric-card">
         <div class="metric-icon">
           <i class="fas fa-brain"></i>
         </div>
         <div class="metric-content">
           <div class="metric-value">{{ metrics.model?.model_parameters?.toLocaleString() || 0 }}</div>
           <div class="metric-label">Paramètres du modèle</div>
         </div>
       </div>
      
             <div class="metric-card">
         <div class="metric-icon">
           <i class="fas fa-memory"></i>
         </div>
         <div class="metric-content">
           <div class="metric-value">{{ Math.round(metrics.system?.memory_percent || 0) }}%</div>
           <div class="metric-label">Utilisation mémoire</div>
         </div>
       </div>
      
             <div class="metric-card">
         <div class="metric-icon">
           <i class="fas fa-microchip"></i>
         </div>
         <div class="metric-content">
           <div class="metric-value">{{ Math.round(metrics.system?.cpu_percent || 0) }}%</div>
           <div class="metric-label">Utilisation CPU</div>
         </div>
       </div>
    </div>
    
    <div class="monitor-footer">
      <button class="btn-refresh" @click="loadMetrics">
        <i class="fas fa-sync-alt"></i>
        Actualiser
      </button>
      <div class="auto-update-info">
        <i class="fas fa-clock"></i>
        <span>Mise à jour automatique toutes les 15s</span>
        <span v-if="metrics?.last_update" class="last-update">
          | Dernière: {{ metrics.last_update }}
        </span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.performance-monitor {
  background: linear-gradient(135deg, #1a1f2e, #252a3a);
  border-radius: 16px;
  padding: 2rem;
  border: 1px solid #374151;
}

.performance-monitor h3 {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
  color: #4f9eff;
  font-size: 1.25rem;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.metric-card {
  background: rgba(15, 20, 25, 0.5);
  border-radius: 12px;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  border: 1px solid #374151;
  transition: all 0.3s ease;
}

.metric-card:hover {
  border-color: #4f9eff;
  transform: translateY(-2px);
}

.metric-icon {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: linear-gradient(135deg, #4f9eff, #60a5fa);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  color: white;
}

.metric-content {
  flex: 1;
}

.metric-value {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 0.25rem;
  color: #ffffff;
}

.metric-label {
  font-size: 0.875rem;
  color: #9ca3af;
  font-weight: 500;
}

.loading-state,
.error-state {
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

.error-state i {
  font-size: 3rem;
  color: #ef4444;
  margin-bottom: 1rem;
}

.btn-retry,
.btn-refresh {
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

.btn-retry:hover,
.btn-refresh:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(79, 158, 255, 0.3);
}

.monitor-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1rem;
}

.auto-update-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #9ca3af;
  font-size: 0.875rem;
}

.auto-update-info i {
  color: #4f9eff;
}

.last-update {
  color: #6b7280;
  font-size: 0.75rem;
}

@media (max-width: 768px) {
  .metrics-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
