<!-- CUADROS DE CONFIANZA DATOARRIENDO -->
<div class="da-trust">
  
  <div class="da-trust-card">
    <div class="da-icon">
      <svg viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
      </svg>
    </div>
    <h4>Información 100% Segura</h4>
    <p>Cumplimos con la Ley 1581 de Habeas Data. Tus datos y los de tus arrendatarios están protegidos.</p>
  </div>

  <div class="da-trust-card">
    <div class="da-icon">
      <svg viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2">
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
        <polyline points="22 4 12 14.01 9 11.01"/>
      </svg>
    </div>
    <h4>Evita Arrendatarios Morosos</h4>
    <p>Consulta el historial de pagos y reportes antes de firmar. Toma decisiones con datos reales.</p>
  </div>

  <div class="da-trust-card">
    <div class="da-icon">
      <svg viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2">
        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
        <circle cx="9" cy="7" r="4"/>
        <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
        <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
      </svg>
    </div>
    <h4>Usado por Inmobiliarias</h4>
    <p>La herramienta de confianza para verificar arrendatarios en Colombia. Rápido y confiable.</p>
  </div>

</div>

<style>
.da-trust {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  max-width: 900px;
  margin: 40px auto 0;
  padding: 0 20px;
}

.da-trust-card {
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  padding: 24px 20px;
  text-align: center;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  transition: all 0.2s ease;
}

.da-trust-card:hover {
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.1);
  transform: translateY(-2px);
}

.da-icon {
  width: 48px;
  height: 48px;
  background: #EFF6FF;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
}

.da-icon svg {
  width: 24px;
  height: 24px;
}

.da-trust-card h4 {
  font-size: 15px;
  font-weight: 600;
  color: #1F2937;
  margin: 0 0 8px 0;
}

.da-trust-card p {
  font-size: 13px;
  color: #6B7280;
  line-height: 1.5;
  margin: 0;
}

@media (max-width: 768px) {
  .da-trust {
    grid-template-columns: 1fr;
    gap: 16px;
  }
}
</style>
