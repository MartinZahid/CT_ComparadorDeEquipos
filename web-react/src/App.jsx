import { useState, useEffect } from 'react'
import './App.css'

const STATUS_LABELS = {
  recommended: '✅ Recomendado',
  minimos: '✅ Mínimos',
  capaz: '⚠️ Capaz',
  no_corre: '❌ No corre',
  sin_datos_cpu: '❓ Sin datos CPU'
}

const STATUS_CLASSES = {
  recommended: 'status-recommended',
  minimos: 'status-minimos',
  capaz: 'status-capaz',
  no_corre: 'status-no_corre',
  sin_datos_cpu: 'status-sin_datos_cpu'
}

function App() {
  const [allProducts, setAllProducts] = useState([])
  const [filteredProducts, setFilteredProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [categoryFilter, setCategoryFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [lastUpdated, setLastUpdated] = useState(null)

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [aioRes, laptopRes] = await Promise.all([
        fetch('/comparacion-all-in-one.json?' + Date.now()).catch(() => null),
        fetch('/comparacion-laptops.json?' + Date.now()).catch(() => null)
      ])

      let products = []
      let timestamps = []

      if (aioRes && aioRes.ok) {
        const aioData = await aioRes.json()
        aioData.resultados.forEach(r => {
          products.push({ ...r, categoria: 'all-in-one', categoriaLabel: 'All in One' })
        })
        if (aioData.fecha_generacion) timestamps.push(aioData.fecha_generacion)
      }

      if (laptopRes && laptopRes.ok) {
        const laptopData = await laptopRes.json()
        laptopData.resultados.forEach(r => {
          products.push({ ...r, categoria: 'laptops', categoriaLabel: 'Laptops' })
        })
        if (laptopData.fecha_generacion) timestamps.push(laptopData.fecha_generacion)
      }

      if (products.length === 0) {
        throw new Error('No se encontraron datos. Ejecuta primero: python -m src compare --cat "All in One" --cat "Laptops"')
      }

      setAllProducts(products)
      setFilteredProducts(products)
      if (timestamps.length > 0) {
        setLastUpdated(new Date(Math.max(...timestamps.map(t => new Date(t).getTime()))))
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleRefresh = () => {
    loadData()
  }

  useEffect(() => {
    let result = allProducts

    if (categoryFilter) {
      result = result.filter(p => p.categoria === categoryFilter)
    }

    if (statusFilter) {
      result = result.filter(p => p.nivel === statusFilter)
    }

    if (searchQuery) {
      const q = searchQuery.toLowerCase()
      result = result.filter(p => 
        `${p.marca} ${p.clave} ${p.procesador} ${p.descripcion}`.toLowerCase().includes(q)
      )
    }

    result.sort((a, b) => (b.score || 0) - (a.score || 0))

    setFilteredProducts(result)
  }, [allProducts, categoryFilter, statusFilter, searchQuery])

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Cargando productos...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="error-container">
        <p>Error: {error}</p>
        <button className="btn-refresh" onClick={handleRefresh}>Reintentar</button>
      </div>
    )
  }

  // Stats
  const stats = allProducts.reduce((acc, p) => {
    acc[p.nivel] = (acc[p.nivel] || 0) + 1
    return acc
  }, {})

  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <h1>Compatibilidad Point</h1>
          <p>Equipos CTOnline clasificados según requisitos mínimos y recomendados</p>
        </div>
        
        <div className="header-actions">
          {lastUpdated && (
            <span className="last-updated">
              🕒 Actualizado: {lastUpdated.toLocaleString()}
            </span>
          )}
          <button className="btn-refresh" onClick={handleRefresh}>
            🔄 Actualizar productos
          </button>
        </div>
      </header>

      <div className="filters">
        <div className="filter-group">
          <label htmlFor="categoryFilter">Categoría:</label>
          <select id="categoryFilter" value={categoryFilter} onChange={e => setCategoryFilter(e.target.value)}>
            <option value="">Todas</option>
            <option value="all-in-one">All in One</option>
            <option value="laptops">Laptops</option>
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="statusFilter">Estado:</label>
          <select id="statusFilter" value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
            <option value="">Todos</option>
            <option value="recommended">✅ Recomendados</option>
            <option value="minimos">✅ Mínimos</option>
            <option value="capaz">⚠️ Capaces</option>
            <option value="no_corre">❌ No corren</option>
            <option value="sin_datos_cpu">❓ Sin datos CPU</option>
          </select>
        </div>

        <button className="btn-clear" onClick={() => { setCategoryFilter(''); setStatusFilter(''); setSearchQuery(''); }}>
          Limpiar filtros
        </button>
      </div>

      <div className="stats-bar">
        <div className="stat stat-recommended">
          <div className="stat-value">{stats.recommended || 0}</div>
          <div className="stat-label">Recomendados</div>
        </div>
        <div className="stat stat-minimos">
          <div className="stat-value">{stats.minimos || 0}</div>
          <div className="stat-label">Mínimos</div>
        </div>
        <div className="stat stat-capaz">
          <div className="stat-value">{stats.capaz || 0}</div>
          <div className="stat-label">Capaces</div>
        </div>
        <div className="stat stat-no_corre">
          <div className="stat-value">{stats.no_corre || 0}</div>
          <div className="stat-label">No corren</div>
        </div>
        <div className="stat stat-sin_datos_cpu">
          <div className="stat-value">{stats.sin_datos_cpu || 0}</div>
          <div className="stat-label">Sin datos CPU</div>
        </div>
      </div>

      <div className="search-bar">
        <input
          type="text"
          placeholder="Buscar por marca, clave, procesador..."
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
        />
        <span className="result-count">
          {filteredProducts.length} de {allProducts.length} productos
        </span>
      </div>

      <main className="main">
        {filteredProducts.length === 0 ? (
          <div className="empty-state">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <circle cx="11" cy="11" r="8"/>
              <path d="M21 21l-4.35-4.35"/>
            </svg>
            <p>No se encontraron productos con los filtros actuales</p>
          </div>
        ) : (
          <div className="products-grid">
            {filteredProducts.map(product => (
              <ProductCard key={product.clave} product={product} />
            ))}
          </div>
        )}
      </main>
    </div>
  )
}

function ProductCard({ product }) {
  const statusClass = STATUS_CLASSES[product.nivel] || 'status-sin_datos_cpu'
  const statusLabel = STATUS_LABELS[product.nivel] || product.nivel

  const specs = [
    { label: 'Procesador', value: product.procesador || 'Desconocido' },
    { label: 'RAM', value: `${product.ram_gb} GB` },
    { label: 'Almacenamiento', value: `${product.storage_gb} GB ${product.storage_type}` },
    { label: 'Sistema', value: product.os }
  ]

  const handleImageError = (e) => {
    e.target.style.display = 'none'
    e.target.nextElementSibling.style.display = 'flex'
  }

  return (
    <article className="product-card">
      <div className="product-image-wrapper">
        {product.imagen ? (
          <>
            <img
              className="product-image"
              src={product.imagen}
              alt={`${product.marca} ${product.clave}`}
              loading="lazy"
              onError={handleImageError}
            />
            <div className="product-image placeholder" style={{ display: 'none' }}>🖥️</div>
          </>
        ) : (
          <div className="product-image placeholder">🖥️</div>
        )}
        
        <span className={`status-badge ${statusClass}`}>{statusLabel}</span>
      </div>

      <div className="product-content">
        <div className="product-header">
          <div>
            <h3 className="product-title">{product.marca} {product.clave}</h3>
            <span className="product-category">{product.categoriaLabel}</span>
          </div>
        </div>

        <div className="product-specs">
          {specs.map((spec, i) => (
            <div key={i} className="spec">
              <span className="spec-label">{spec.label}</span>
              <span className="spec-value">{spec.value}</span>
            </div>
          ))}
        </div>

        <details className="product-reasons">
          <summary>Detalles de compatibilidad</summary>
          <ul>
            {product.razones?.map((reason, i) => (
              <li key={i} className={reason.includes('NO') || reason.includes('no cumpl') || reason.includes('<') ? 'fail' : ''}>
                {reason}
              </li>
            ))}
          </ul>
        </details>

        {product.url && (
          <a href={product.url} target="_blank" rel="noopener noreferrer" className="btn-link">
            Ver producto en CTOnline →
          </a>
        )}
      </div>
    </article>
  )
}

export default App