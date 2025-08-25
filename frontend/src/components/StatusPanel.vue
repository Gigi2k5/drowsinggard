<script>
import { computed } from 'vue'

export default {
  name: 'StatusPanel',
  props: {
    status: {
      type: String,
      default: 'awake'
    },
    confidence: {
      type: Number,
      default: 0
    },
    latency: {
      type: Number,
      default: 0
    }
  },
  setup(props) {
    const statusColor = computed(() => {
      switch (props.status) {
        case 'awake': return 'success'
        case 'drowsy': return 'warning'
        case 'alert': return 'danger'
        default: return 'secondary'
      }
    })

    const statusIcon = computed(() => {
      switch (props.status) {
        case 'awake': return 'fas fa-eye'
        case 'drowsy': return 'fas fa-eye-slash'
        case 'alert': return 'fas fa-exclamation-triangle'
        default: return 'fas fa-question'
      }
    })

    const statusTitle = computed(() => {
      switch (props.status) {
        case 'awake': return 'État Éveillé'
        case 'drowsy': return 'Somnolence Détectée'
        case 'alert': return 'Alerte !'
        default: return 'Statut Inconnu'
      }
    })

    const statusDescription = computed(() => {
      switch (props.status) {
        case 'awake': return 'Vous êtes en état d\'éveil normal'
        case 'drowsy': return 'Attention, signes de somnolence détectés'
        case 'alert': return 'Somnolence critique détectée !'
        default: return 'Statut non déterminé'
      }
    })

    const performanceText = computed(() => {
      if (props.latency > 0) {
        return `Latence: ${props.latency}ms | Confiance: ${Math.round(props.confidence * 100)}%`
      }
      return 'En attente de données...'
    })

    return {
      statusColor,
      statusIcon,
      statusTitle,
      statusDescription,
      performanceText
    }
  }
}
</script>

<template>
  <div class="status-panel">
    <div class="status-card" :class="`status-${statusColor}`">
      <div class="status-icon">
        <i :class="statusIcon"></i>
      </div>
      <div class="status-content">
        <h3>{{ statusTitle }}</h3>
        <p>{{ statusDescription }}</p>
      </div>
    </div>
    
    <div class="status-card status-info">
      <div class="status-icon">
        <i class="fas fa-tachometer-alt"></i>
      </div>
      <div class="status-content">
        <h3>Performance</h3>
        <p>{{ performanceText }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.status-panel {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
  margin-bottom: 2rem;
}

.status-card {
  background: linear-gradient(135deg, #1a1f2e, #252a3a);
  border-radius: 16px;
  padding: 2rem;
  border: 1px solid #374151;
  display: flex;
  align-items: center;
  gap: 1.5rem;
  transition: all 0.3s ease;
}

.status-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2);
}

.status-card.status-success {
  border-color: #4ade80;
  background: linear-gradient(135deg, rgba(74, 222, 128, 0.1), rgba(34, 197, 94, 0.05));
}

.status-card.status-warning {
  border-color: #fbbf24;
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.1), rgba(245, 158, 11, 0.05));
}

.status-card.status-danger {
  border-color: #f87171;
  background: linear-gradient(135deg, rgba(248, 113, 113, 0.1), rgba(239, 68, 68, 0.05));
}

.status-card.status-info {
  border-color: #4f9eff;
  background: linear-gradient(135deg, rgba(79, 158, 255, 0.1), rgba(96, 165, 250, 0.05));
}

.status-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
}

.status-card.status-success .status-icon {
  color: #4ade80;
}

.status-card.status-warning .status-icon {
  color: #fbbf24;
}

.status-card.status-danger .status-icon {
  color: #f87171;
}

.status-card.status-info .status-icon {
  color: #4f9eff;
}

.status-content {
  flex: 1;
}

.status-content h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #ffffff;
}

.status-content p {
  margin: 0;
  color: #9ca3af;
  font-size: 0.875rem;
  line-height: 1.5;
}

@media (max-width: 768px) {
  .status-panel {
    grid-template-columns: 1fr;
  }
  
  .status-card {
    flex-direction: column;
    text-align: center;
    gap: 1rem;
  }
}
</style>


