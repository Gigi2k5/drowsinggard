<template>
  <section class="landing">
    <div class="hero">
      <div class="badge">
        <span class="dot"></span>
        Détection IA en temps réel
      </div>
      <h1>
        Surveillez votre
        <span class="highlight">état de vigilance</span>
      </h1>
      <p class="subtitle">
        Application intelligente de détection de somnolence utilisant l'IA pour assurer votre sécurité
        lors de tâches nécessitant une attention soutenue.
      </p>
      <div class="cta">
        <button class="btn btn-primary" @click="$emit('open-auth')">
          <i class="fas fa-play"></i>
          Démarrer le suivi
        </button>
        <button class="btn btn-dark" @click="$emit('open-auth')">
          <i class="fas fa-history"></i>
          Voir l'historique
        </button>
      </div>
    </div>

    <div class="features">
      <h2>Fonctionnalités avancées</h2>
      <p class="features-subtitle">Technologie de pointe pour une surveillance fiable et précise</p>
      <div class="cards">
        <div class="card">
          <div class="icon"><i class="fas fa-camera"></i></div>
          <h3>Détection en temps réel</h3>
          <p>Analyse continue via webcam avec détection faciale MTCNN et traitement optimisé.</p>
        </div>
        <div class="card">
          <div class="icon"><i class="fas fa-brain"></i></div>
          <h3>IA PyTorch</h3>
          <p>Modèle CNN pré‑entraîné pour classifier précisément éveil et somnolence.</p>
        </div>
        <div class="card">
          <div class="icon"><i class="fas fa-bolt"></i></div>
          <h3>Alertes intelligentes</h3>
          <p>Alerte sonore automatique après détection sur plusieurs frames consécutives.</p>
        </div>
      </div>
      <div class="metrics">
        <div class="metric"><span class="value">99.2%</span><span class="label">Précision du modèle</span></div>
        <div class="metric"><span class="value">&lt; 200ms</span><span class="label">Temps de réponse</span></div>
        <div class="metric"><span class="value">24/7</span><span class="label">Surveillance continue</span></div>
        <div class="metric"><span class="value">Mobile</span><span class="label">Compatible</span></div>
      </div>
    </div>
  </section>
</template>

<script>
export default {
  name: 'LandingHero',
  emits: ['open-auth']
}
</script>

<style scoped>
.landing {
  min-height: 100vh;
  background: radial-gradient(1200px 600px at 20% 0%, #0b1739 0%, #0a1024 40%, #070c1a 100%);
  color: #eaf0ff;
}
.hero {
  max-width: 960px;
  margin: 0 auto;
  padding: 96px 24px 24px;
  text-align: center;
}
.badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  border-radius: 999px;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.08);
  font-size: 14px;
  color: #c9d6ff;
}
.badge .dot {
  width: 8px; height: 8px; border-radius: 50%; background: #7bdcff; box-shadow: 0 0 8px #7bdcff;
}
h1 { font-size: 56px; line-height: 1.1; margin: 24px 0 12px; font-weight: 800; }
.highlight { color: #4c8bf5; }
.subtitle { color: #a9b6d9; max-width: 820px; margin: 0 auto 28px; }
.cta { display: flex; gap: 16px; justify-content: center; flex-wrap: wrap; }
.btn { display: inline-flex; align-items: center; gap: 10px; padding: 12px 18px; border: none; border-radius: 10px; cursor: pointer; font-weight: 600; }
.btn-primary { background: #4c8bf5; color: #fff; box-shadow: 0 8px 24px rgba(76,139,245,0.35); }
.btn-dark { background: #0e152e; color: #eaf0ff; border: 1px solid rgba(255,255,255,0.08); }

.features { padding: 48px 24px 72px; max-width: 1100px; margin: 0 auto; }
.features h2 { text-align: center; font-size: 32px; margin-bottom: 6px; }
.features-subtitle { text-align: center; color: #9fb0d8; margin-bottom: 26px; }
.cards { display: grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap: 18px; }
.card { background: linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0.02)); border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; padding: 20px; }
.card .icon { width: 56px; height: 56px; border-radius: 14px; display: grid; place-items: center; margin: 0 auto 12px; font-size: 22px; }
.card h3 { margin: 0 0 6px; color: #ffffff; }
.card p { margin: 0; color: #a9b6d9; }
.cards .card:nth-child(1) .icon { background: rgba(76,139,245,0.18); color: #6ea2ff; }
.cards .card:nth-child(2) .icon { background: rgba(0, 201, 167, 0.18); color: #38e2c7; }
.cards .card:nth-child(3) .icon { background: rgba(255, 193, 7, 0.20); color: #ffd54d; }
.metrics { display: grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap: 12px; margin-top: 28px; }
.metric { background: rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.07); border-radius: 12px; padding: 16px; text-align: center; }
.metric .value { display: block; font-weight: 800; font-size: 20px; color: #cfe2ff; }
.metric .label { color: #8fa1cc; font-size: 13px; }

@media (max-width: 900px) {
  h1 { font-size: 40px; }
  .cards { grid-template-columns: 1fr; }
  .metrics { grid-template-columns: repeat(2, minmax(0,1fr)); }
}
</style>
