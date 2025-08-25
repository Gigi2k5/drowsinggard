<template>
  <div class="audio-settings">
    <h3><i class="fas fa-volume-up"></i> Paramètres Audio</h3>
    
    <div class="setting-item">
      <label>Type d'alerte :</label>
      <select v-model="audioType">
        <option value="beep">Bip</option>
        <option value="alarm">Alarme</option>
        <option value="bell">Cloche</option>
        <option value="custom">Personnalisé</option>
      </select>
    </div>
    
    <div class="setting-item" v-if="audioType === 'custom'">
      <label>Fichier audio :</label>
      <input type="file" accept="audio/*" @change="handleAudioFile" />
    </div>
    
    <div class="setting-item">
      <label>Volume : {{ Math.round(volume * 100) }}%</label>
      <input 
        type="range" 
        min="0" 
        max="1" 
        step="0.1" 
        v-model="volume"
      />
    </div>
    
    <button class="btn-test" @click="testAudio">
      <i class="fas fa-play"></i>
      Tester l'audio
    </button>
  </div>
</template>

<script>
import { ref, watch } from 'vue'

export default {
  name: 'AudioSettings',
  emits: ['update:modelValue', 'test-audio'],
  setup(props, { emit }) {
    const audioType = ref('beep')
    const volume = ref(0.7)
    const customFile = ref(null)

    function handleAudioFile(event) {
      const file = event.target.files[0]
      if (file) {
        customFile.value = URL.createObjectURL(file)
      }
    }

    function testAudio() {
      console.log('Test audio:', { audioType: audioType.value, volume: volume.value })
      // Émettre l'événement pour que le parent gère le test
      emit('test-audio')
    }

    // Émettre les changements
    watch([audioType, volume], ([newType, newVolume]) => {
      emit('update:modelValue', {
        type: newType,
        volume: newVolume,
        customFile: customFile.value
      })
    })

    return {
      audioType,
      volume,
      customFile,
      handleAudioFile,
      testAudio
    }
  }
}
</script>

<style scoped>
.audio-settings {
  background: linear-gradient(135deg, #1a1f2e, #252a3a);
  border-radius: 16px;
  padding: 2rem;
  border: 1px solid #374151;
}

.audio-settings h3 {
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

.setting-item select,
.setting-item input[type="file"] {
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
</style>
