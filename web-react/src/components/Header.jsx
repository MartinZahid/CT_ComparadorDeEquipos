function Header({ lastUpdated, refreshing, refreshOutput, showRequirements, onRefresh, onToggleRequirements }) {
  return (
    <header className="header">
      <div className="header-content">
        <h1>Compatibilidad Point</h1>
        <p>Equipos CTOnline clasificados según requisitos mínimos y recomendados</p>
      </div>

      <div className="header-actions">
        {lastUpdated && (
          <span className="last-updated">
            Actualizado: {lastUpdated.toLocaleString()}
          </span>
        )}
        <button className="btn-refresh" onClick={onRefresh} disabled={refreshing}>
          {refreshing ? 'Scrapeando...' : 'Actualizar productos'}
        </button>
        {refreshing && refreshOutput && (
          <span className="refresh-status">{refreshOutput}</span>
        )}
        <button className="btn-toggle" onClick={onToggleRequirements}>
          {showRequirements ? 'Ocultar requisitos' : 'Editar requisitos'}
        </button>
      </div>
    </header>
  )
}

export default Header
