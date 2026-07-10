function Filters({ categoryFilter, statusFilter, searchQuery, onCategoryChange, onStatusChange, onSearchChange, onClear }) {
  return (
    <div className="filters">
      <div className="filter-group">
        <label htmlFor="categoryFilter">Categor&iacute;a:</label>
        <select id="categoryFilter" value={categoryFilter} onChange={e => onCategoryChange(e.target.value)}>
          <option value="">Todas</option>
          <option value="all-in-one">All in One</option>
          <option value="laptops">Laptops</option>
        </select>
      </div>

      <div className="filter-group">
        <label htmlFor="statusFilter">Estado:</label>
        <select id="statusFilter" value={statusFilter} onChange={e => onStatusChange(e.target.value)}>
          <option value="">Todos</option>
          <option value="recommended">Recomendados</option>
          <option value="minimos">M&iacute;nimos</option>
          <option value="capaz">Capaces</option>
          <option value="no_corre">No corren</option>
          <option value="sin_datos_cpu">Sin datos CPU</option>
        </select>
      </div>

      <button className="btn-clear" onClick={onClear}>
        Limpiar filtros
      </button>
    </div>
  )
}

export default Filters
