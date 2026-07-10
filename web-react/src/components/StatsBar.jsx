const LEVELS = [
  { key: 'recommended', label: 'Recomendados' },
  { key: 'minimos', label: 'M&iacute;nimos' },
  { key: 'capaz', label: 'Capaces' },
  { key: 'no_corre', label: 'No corren' },
  { key: 'sin_datos_cpu', label: 'Sin datos CPU' },
]

function StatsBar({ stats }) {
  return (
    <div className="stats-bar">
      {LEVELS.map(({ key, label }) => (
        <div key={key} className={`stat stat-${key}`}>
          <div className="stat-value">{stats[key] || 0}</div>
          <div className="stat-label">{label}</div>
        </div>
      ))}
    </div>
  )
}

export default StatsBar
