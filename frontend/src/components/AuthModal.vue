<template>
  <div v-if="show" class="auth-modal-overlay" @click="closeModal">
    <div class="auth-modal-content" @click.stop>
      <div class="auth-modal-header">
        <h2>{{ isLogin ? 'Connexion' : 'Créer un compte' }}</h2>
        <button @click="closeModal" class="btn-close">
          <i class="fas fa-times"></i>
        </button>
      </div>
      
      <div class="auth-modal-body">
        <div v-if="error" class="auth-error">
          <i class="fas fa-exclamation-triangle"></i>
          {{ error }}
        </div>
        
        <form @submit.prevent="handleSubmit" class="auth-form">
          <div class="form-group">
            <label for="username">Nom d'utilisateur</label>
            <input 
              id="username"
              v-model="form.username" 
              type="text" 
              required 
              placeholder="Entrez votre nom d'utilisateur"
            />
          </div>
          
          <div v-if="!isLogin" class="form-group">
            <label for="email">Email</label>
            <input 
              id="email"
              v-model="form.email" 
              type="email" 
              required 
              placeholder="Entrez votre email"
            />
          </div>
          
          <div class="form-group">
            <label for="password">Mot de passe</label>
            <input 
              id="password"
              v-model="form.password" 
              type="password" 
              required 
              placeholder="Entrez votre mot de passe"
            />
          </div>

          <div v-if="!isLogin" class="form-group">
            <label for="confirmPassword">Confirmer le mot de passe</label>
            <input 
              id="confirmPassword"
              v-model="form.confirmPassword"
              type="password"
              required
              placeholder="Retapez votre mot de passe"
            />
          </div>
          
          <button type="submit" class="btn-submit" :disabled="loading">
            <i v-if="loading" class="fas fa-spinner fa-spin"></i>
            <span v-else>{{ isLogin ? 'Se connecter' : 'Créer le compte' }}</span>
          </button>
        </form>
        
        <div class="auth-switch">
          <p>
            {{ isLogin ? 'Pas encore de compte ?' : 'Déjà un compte ?' }}
            <button @click="toggleMode" class="btn-link">
              {{ isLogin ? 'Créer un compte' : 'Se connecter' }}
            </button>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive } from 'vue'
import { api } from '../services/api'

export default {
  name: 'AuthModal',
  props: {
    show: {
      type: Boolean,
      default: false
    }
  },
  emits: ['close', 'login-success'],
  setup(props, { emit }) {
    const isLogin = ref(true)
    const loading = ref(false)
    const error = ref('')
    
    const form = reactive({
      username: '',
      email: '',
      password: '',
      confirmPassword: ''
    })
    
    function closeModal() {
      error.value = ''
      emit('close')
    }
    
    function toggleMode() {
      isLogin.value = !isLogin.value
      error.value = ''
      form.username = ''
      form.email = ''
      form.password = ''
      form.confirmPassword = ''
    }
    
    async function handleSubmit() {
      try {
        loading.value = true
        error.value = ''
        
        if (isLogin.value) {
          // Connexion
          const response = await api.request('/auth/login', {
            method: 'POST',
            body: {
              username: form.username,
              password: form.password
            }
          })
          
          if (response.success) {
            // Stocker le token et les infos utilisateur
            localStorage.setItem('authToken', response.token)
            localStorage.setItem('user', JSON.stringify(response.user))
            
            emit('login-success', response.user)
            closeModal()
          } else {
            error.value = response.error || 'Erreur de connexion'
          }
        } else {
          // Création de compte
          if (!form.password || !form.confirmPassword) {
            error.value = 'Veuillez saisir et confirmer votre mot de passe'
            return
          }
          if (form.password !== form.confirmPassword) {
            error.value = 'Les mots de passe ne correspondent pas'
            return
          }
          const response = await api.request('/auth/register', {
            method: 'POST',
            body: {
              username: form.username,
              email: form.email,
              password: form.password
            }
          })
          
          if (response.success) {
            // Basculer vers la connexion
            isLogin.value = true
            error.value = ''
            form.username = ''
            form.email = ''
            form.password = ''
            form.confirmPassword = ''
            alert('Compte créé avec succès ! Vous pouvez maintenant vous connecter.')
          } else {
            error.value = response.error || 'Erreur lors de la création du compte'
          }
        }
      } catch (err) {
        console.error('Erreur authentification:', err)
        error.value = 'Erreur de connexion au serveur'
      } finally {
        loading.value = false
      }
    }
    
    return {
      isLogin,
      loading,
      error,
      form,
      closeModal,
      toggleMode,
      handleSubmit
    }
  }
}
</script>

<style scoped>
.auth-modal-overlay {
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
}

.auth-modal-content {
  background: linear-gradient(135deg, #1a1f2e, #252a3a);
  border-radius: 16px;
  border: 1px solid #374151;
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
}

.auth-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #374151;
}

.auth-modal-header h2 {
  margin: 0;
  color: #ffffff;
  font-size: 1.5rem;
  font-weight: 600;
}

.btn-close {
  background: none;
  border: none;
  color: #9ca3af;
  font-size: 1.25rem;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.btn-close:hover {
  color: #ffffff;
  background: rgba(255, 255, 255, 0.1);
}

.auth-modal-body {
  padding: 1.5rem;
}

.auth-error {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1.5rem;
  color: #fca5a5;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  color: #d1d5db;
  font-weight: 500;
  font-size: 0.875rem;
}

.form-group input {
  padding: 0.75rem;
  border: 1px solid #374151;
  border-radius: 8px;
  background: #0f1419;
  color: #ffffff;
  font-size: 1rem;
  transition: border-color 0.3s ease;
}

.form-group input:focus {
  outline: none;
  border-color: #4f9eff;
}

.btn-submit {
  background: linear-gradient(135deg, #4f9eff, #60a5fa);
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
}

.btn-submit:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(79, 158, 255, 0.3);
}

.btn-submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.auth-switch {
  text-align: center;
  padding: 1rem 0;
  border-top: 1px solid #374151;
}

.auth-switch p {
  color: #9ca3af;
  margin: 0;
}

.btn-link {
  background: none;
  border: none;
  color: #4f9eff;
  text-decoration: underline;
  cursor: pointer;
  font-size: inherit;
}

.btn-link:hover {
  color: #60a5fa;
}

.demo-credentials {
  background: rgba(79, 158, 255, 0.1);
  border: 1px solid rgba(79, 158, 255, 0.3);
  border-radius: 8px;
  padding: 1rem;
  margin-top: 1rem;
}

.demo-title {
  color: #4f9eff;
  font-weight: 600;
  margin: 0 0 0.5rem 0;
  font-size: 0.875rem;
}

.demo-credentials p {
  color: #9ca3af;
  margin: 0.25rem 0;
  font-size: 0.875rem;
}

.demo-credentials strong {
  color: #d1d5db;
}
</style>
