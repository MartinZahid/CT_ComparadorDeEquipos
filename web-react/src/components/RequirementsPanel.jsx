function RequirementsPanel({ requirements, onChange, onReset, classifying }) {
  return (
    <div className="requirements-panel">
      <h3>Requisitos de compatibilidad</h3>
      <p className="req-hint">
        Modifica los valores y la clasificaci&oacute;n se recalcular&aacute; en el servidor
        {classifying && <span className="classifying-hint"> (reclasificando...)</span>}
      </p>

      <div className="req-grid">
        <div className="req-section">
          <h4>CPU</h4>
          <div className="req-row">
            <label>GHz m&iacute;n: <input type="number" step="0.1" value={requirements.cpu.min_ghz} onChange={e => onChange('cpu.min_ghz', e.target.value)} /></label>
            <label>N&uacute;cleos m&iacute;n: <input type="number" value={requirements.cpu.min_cores} onChange={e => onChange('cpu.min_cores', e.target.value)} /></label>
          </div>
          <div className="req-row">
            <label>GHz rec: <input type="number" step="0.1" value={requirements.cpu.rec_ghz} onChange={e => onChange('cpu.rec_ghz', e.target.value)} /></label>
            <label>N&uacute;cleos rec: <input type="number" value={requirements.cpu.rec_cores} onChange={e => onChange('cpu.rec_cores', e.target.value)} /></label>
          </div>
        </div>

        <div className="req-section">
          <h4>RAM</h4>
          <div className="req-row">
            <label>GB m&iacute;n: <input type="number" value={requirements.ram_min_gb} onChange={e => onChange('ram_min_gb', e.target.value)} /></label>
            <label>GB rec: <input type="number" value={requirements.ram_rec_gb} onChange={e => onChange('ram_rec_gb', e.target.value)} /></label>
          </div>
        </div>

        <div className="req-section">
          <h4>Disco</h4>
          <div className="req-row">
            <label>GB m&iacute;n: <input type="number" value={requirements.disk_min_gb} onChange={e => onChange('disk_min_gb', e.target.value)} /></label>
            <label>GB rec: <input type="number" value={requirements.disk_rec_gb} onChange={e => onChange('disk_rec_gb', e.target.value)} /></label>
          </div>
          <div className="req-row">
            <label>SSD obligatorio si &le; GB: <input type="number" value={requirements.ssd_required_below_gb} onChange={e => onChange('ssd_required_below_gb', e.target.value)} /></label>
          </div>
        </div>

        <div className="req-section">
          <h4>Sistema Operativo</h4>
          <div className="req-row">
            <label>OS m&iacute;n: <input type="text" value={requirements.os_min} onChange={e => onChange('os_min', e.target.value)} /></label>
            <label>OS rec: <input type="text" value={requirements.os_rec} onChange={e => onChange('os_rec', e.target.value)} /></label>
          </div>
        </div>
      </div>

      <button className="btn-reset" onClick={onReset}>Restaurar por defecto</button>
    </div>
  )
}

export default RequirementsPanel
