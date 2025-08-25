<script>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { api } from '../services/api'

export default {
  name: 'ApiTest',
  setup() {
    const testResult = ref(null)
    const loading = ref(false)
    const error = ref(null)

    async function testHealth() {
      loading.value = true
      error.value = null
      try {
        const result = await api.health()
        testResult.value = result
        console.log('✅ Health check réussi:', result)
      } catch (e) {
        error.value = e.message
        console.error('❌ Health check échoué:', e)
      } finally {
        loading.value = false
      }
    }

    async function testPredict() {
      loading.value = true
      error.value = null
      try {
        // Créer une image de test simple (1x1 pixel noir)
        const canvas = document.createElement('canvas')
        canvas.width = 1
        canvas.height = 1
        const ctx = canvas.getContext('2d')
        ctx.fillStyle = 'black'
        ctx.fillRect(0, 0, 1, 1)
        const testImage = canvas.toDataURL('image/jpeg', 0.8)
        
        console.log('🔄 Test prédiction avec image:', testImage.substring(0, 50) + '...')
        const result = await api.predict(testImage)
        testResult.value = result
        console.log('✅ Prédiction réussie:', result)
      } catch (e) {
        error.value = e.message
        console.error('❌ Prédiction échouée:', e)
      } finally {
        loading.value = false
      }
    }

    // Test automatique au chargement et toutes les 10 secondes
    onMounted(() => {
      testHealth()
      const interval = setInterval(testHealth, 10000)
      
      onBeforeUnmount(() => {
        clearInterval(interval)
      })
    })

    return {
      testResult,
      loading,
      error,
      testHealth,
      testPredict
    }
  }
}
</script>

<template>
	<div class="api-test">
		<h3><i class="fas fa-vial"></i> Test de l'API</h3>
		
		<div class="test-buttons">
			<button class="btn-test" @click="testHealth">
				<i class="fas fa-heartbeat"></i>
				Test Health
			</button>
			
			<button class="btn-test" @click="testPredict">
				<i class="fas fa-brain"></i>
				Test Predict
			</button>
		</div>
		
		<div v-if="testResult" class="test-result">
			<h4>Résultat du test :</h4>
			<pre>{{ JSON.stringify(testResult, null, 2) }}</pre>
		</div>
		
		<div v-if="error" class="test-error">
			<h4>Erreur :</h4>
			<p>{{ error }}</p>
		</div>
	</div>
</template>

<style scoped>
.api-test {
	background: linear-gradient(135deg, #1a1f2e, #252a3a);
	border-radius: 16px;
	padding: 2rem;
	border: 1px solid #374151;
}

.api-test h3 {
	display: flex;
	align-items: center;
	gap: 0.75rem;
	margin-bottom: 1.5rem;
	color: #4f9eff;
	font-size: 1.25rem;
}

.test-buttons {
	display: flex;
	gap: 1rem;
	margin-bottom: 2rem;
}

.btn-test {
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

.btn-test:hover {
	transform: translateY(-2px);
	box-shadow: 0 8px 20px rgba(79, 158, 255, 0.3);
}

.test-result,
.test-error {
	background: rgba(15, 20, 25, 0.5);
	border-radius: 8px;
	padding: 1rem;
}

.test-result h4,
.test-error h4 {
	margin: 0 0 0.75rem 0;
	color: #ffffff;
	font-size: 1rem;
}

.test-result pre {
	background: #0f1419;
	padding: 1rem;
	border-radius: 4px;
	overflow-x: auto;
	font-size: 0.875rem;
	color: #e5e7eb;
	margin: 0;
}

.test-error p {
	margin: 0;
	color: #ef4444;
	font-size: 0.875rem;
}

@media (max-width: 768px) {
	.test-buttons {
		flex-direction: column;
	}
}
</style>
