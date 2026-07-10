import { useState, useEffect, useMemo } from 'react'
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

// Default requirements (matching backend defaults)
const DEFAULT_REQUIREMENTS = {
  cpu: { min_ghz: 3.6, min_cores: 4, rec_ghz: 3.6, rec_cores: 4 },
  ram_min_gb: 8,
  ram_rec_gb: 16,
  disk_min_gb: 1,
  disk_rec_gb: 1,
  ssd_required_below_gb: 128,
  os_min: "Windows 10",
  os_rec: "Windows 11"
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
  const [requirements, setRequirements] = useState(DEFAULT_REQUIREMENTS)
  const [showRequirements, setShowRequirements] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [refreshOutput, setRefreshOutput] = useState('')

  // Load data from API
  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch('/api/products')
      if (!res.ok) throw new Error('Error al cargar datos del servidor')
      const data = await res.json()

      if (!data.products || data.products.length === 0) {
        throw new Error('No se encontraron datos. Ejecuta primero: python -m src compare --cat "All in One" --cat "Laptops"')
      }

      const classifiedProducts = classifyProducts(data.products, requirements)
      setAllProducts(classifiedProducts)
      setFilteredProducts(classifiedProducts)
      if (data.last_updated) {
        setLastUpdated(new Date(data.last_updated))
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // Client-side classification logic
  const classifyProducts = (products, req) => {
    return products.map(p => {
      const spec = extractSpec(p)
      const classification = classify(spec, req)
      return { ...p, ...classification }
    })
  }

  // Extract spec from product data
  const extractSpec = (p) => ({
    cpu: {
      turbo_ghz: p.cpu_turbo_ghz,
      cores: p.cpu_cores,
      source: p.cpu_source
    },
    ram_gb: p.ram_gb,
    storage_gb: p.storage_gb,
    storage_type: p.storage_type,
    os: p.os
  })

  // Classification logic (mirrors backend)
  const classify = (spec, req) => {
    const reasons = []
    
    // CPU check
    const cpu = checkCPU(spec.cpu, req)
    reasons.push(cpu.reason)
    
    // RAM check
    const ram = checkRAM(spec.ram_gb, req)
    reasons.push(ram.reason)
    
    // OS check
    const os = checkOS(spec.os, req)
    reasons.push(os.reason)
    
    // Disk check
    const disk = checkDisk(spec.storage_gb, spec.storage_type, req)
    reasons.push(disk.reason)
    
    // No CPU data
    if (spec.cpu.source === "none" || spec.cpu.turbo_ghz === null) {
      return { nivel: "sin_datos_cpu", puede_correr: false, reasons, score: 0 }
    }
    
    const allRec = cpu.rec && ram.rec && os.rec && disk.rec
    const allMin = cpu.min && ram.min && os.min && disk.min
    const cpuRamMin = cpu.min && ram.min
    
    if (allRec) return { nivel: "recommended", puede_correr: true, reasons, score: 100 }
    if (allMin) return { nivel: "minimos", puede_correr: true, reasons, score: 70 }
    if (cpuRamMin) return { nivel: "capaz", puede_correr: true, reasons, score: 50 }
    return { nivel: "no_corre", puede_correr: false, reasons, score: 10 }
  }
  
  const checkCPU = (cpu, req) => {
    if (cpu.turbo_ghz === null || cpu.cores === null) {
      return { min: false, rec: false, reason: "CPU sin datos técnicos" }
    }
    const min = cpu.turbo_ghz >= req.cpu.min_ghz && cpu.cores >= req.cpu.min_cores
    const rec = cpu.turbo_ghz >= req.cpu.rec_ghz && cpu.cores >= req.cpu.rec_cores
    return { min, rec, reason: `CPU turbo ${cpu.turbo_ghz}GHz, ${cpu.cores} nucleos` }
  }
  
  const checkRAM = (ram, req) => ({
    min: ram >= req.ram_min_gb,
    rec: ram >= req.ram_rec_gb,
    reason: `RAM ${ram}GB`
  })
  
  const checkOS = (os, req) => {
    const min = os.startsWith(req.os_min) || os.startsWith(req.os_rec)
    const rec = os.startsWith(req.os_rec)
    return { min, rec, reason: `OS ${os}` }
  }
  
  const checkDisk = (gb, type, req) => {
    const ssdOk = !(gb <= req.ssd_required_below_gb && type !== "SSD")
    const min = gb >= req.disk_min_gb && ssdOk
    const rec = gb >= req.disk_rec_gb && ssdOk
    return { min, rec, reason: `Disco ${gb}GB ${type}` }
  }

  useEffect(() => {
    loadData()
  }, [])

  // Re-classify when requirements change
  useEffect(() => {
    if (allProducts.length > 0) {
      const reclassified = classifyProducts(allProducts, requirements)
      setAllProducts(reclassified)
      applyFilters(reclassified)
    }
  }, [requirements])

  const applyFilters = (products) => {
    let result = products

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
  }

  useEffect(() => {
    applyFilters(allProducts)
  }, [allProducts, categoryFilter, statusFilter, searchQuery])

  const handleRefresh = async () => {
    setRefreshing(true)
    setRefreshOutput('Iniciando...')
    try {
      const res = await fetch('/api/refresh', { method: 'POST' })
      const { task_id } = await res.json()
      setRefreshOutput('Scrapeando y comparando...')

      // Poll for completion
      const poll = setInterval(async () => {
        const statusRes = await fetch(`/api/refresh-status/${task_id}`)
        const status = await statusRes.json()
        if (status.status === 'done') {
          clearInterval(poll)
          setRefreshOutput(status.error ? `Error: ${status.error}` : '¡Datos actualizados!')
          setRefreshing(false)
          loadData()
        } else if (status.output) {
          const lines = status.output.split('\n')
          setRefreshOutput(lines[lines.length - 1] || 'Procesando...')
        }
      }, 2000)
    } catch (err) {
      setRefreshOutput(`Error: ${err.message}`)
      setRefreshing(false)
    }
  }

  const handleReqChange = (field, value) => {
    setRequirements(prev => {
      const keys = field.split('.')
      const newReq = { ...prev }
      let obj = newReq
      for (let i = 0; i < keys.length - 1; i++) {
        obj[keys[i]] = { ...obj[keys[i]] }
        obj = obj[keys[i]]
      }
      obj[keys[keys.length - 1]] = Number(value) || value
      return newReq
    })
  }

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
        <button className="btn-refresh" onClick={loadData}>Reintentar</button>
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
          <button className="btn-refresh" onClick={handleRefresh} disabled={refreshing}>
            {refreshing ? '⏳ Scrapeando...' : '🔄 Actualizar productos'}
          </button>
          {refreshing && refreshOutput && (
            <span className="refresh-status">{refreshOutput}</span>
          )}
          <button className="btn-toggle" onClick={() => setShowRequirements(!showRequirements)}>
            {showRequirements ? '📋 Ocultar requisitos' : '📋 Editar requisitos'}
          </button>
        </div>
      </header>

      {showRequirements && (
        <div className="requirements-panel">
          <h3>⚙️ Requisitos de compatibilidad</h3>
          <p className="req-hint">Modifica los valores y la tabla se actualizará automáticamente</p>
          
          <div className="req-grid">
            <div className="req-section">
              <h4>🖥️ CPU</h4>
              <div className="req-row">
                <label>GHz mín: <input type="number" step="0.1" value={requirements.cpu.min_ghz} onChange={e => handleReqChange('cpu.min_ghz', e.target.value)} /></label>
                <label>Núcleos mín: <input type="number" value={requirements.cpu.min_cores} onChange={e => handleReqChange('cpu.min_cores', e.target.value)} /></label>
              </div>
              <div className="req-row">
                <label>GHz rec: <input type="number" step="0.1" value={requirements.cpu.rec_ghz} onChange={e => handleReqChange('cpu.rec_ghz', e.target.value)} /></label>
                <label>Núcleos rec: <input type="number" value={requirements.cpu.rec_cores} onChange={e => handleReqChange('cpu.rec_cores', e.target.value)} /></label>
              </div>
            </div>

            <div className="req-section">
              <h4>🧠 RAM</h4>
              <div className="req-row">
                <label>GB mín: <input type="number" value={requirements.ram_min_gb} onChange={e => handleReqChange('ram_min_gb', e.target.value)} /></label>
                <label>GB rec: <input type="number" value={requirements.ram_rec_gb} onChange={e => handleReqChange('ram_rec_gb', e.target.value)} /></label>
              </div>
            </div>

            <div className="req-section">
              <h4>💾 Disco</h4>
              <div className="req-row">
                <label>GB mín: <input type="number" value={requirements.disk_min_gb} onChange={e => handleReqChange('disk_min_gb', e.target.value)} /></label>
                <label>GB rec: <input type="number" value={requirements.disk_rec_gb} onChange={e => handleReqChange('disk_rec_gb', e.target.value)} /></label>
              </div>
              <div className="req-row">
                <label>SSD obligatorio si ≤ GB: <input type="number" value={requirements.ssd_required_below_gb} onChange={e => handleReqChange('ssd_required_below_gb', e.target.value)} /></label>
              </div>
            </div>

            <div className="req-section">
              <h4>🪟 Sistema Operativo</h4>
              <div className="req-row">
                <label>OS mín: <input type="text" value={requirements.os_min} onChange={e => handleReqChange('os_min', e.target.value)} /></label>
                <label>OS rec: <input type="text" value={requirements.os_rec} onChange={e => handleReqChange('os_rec', e.target.value)} /></label>
              </div>
            </div>
          </div>
          
          <button className="btn-reset" onClick={() => setRequirements(DEFAULT_REQUIREMENTS)}>🔄 Restaurar por defecto</button>
        </div>
      )}

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
        <div className="stat stat-recommended"><div className="stat-value">{stats.recommended || 0}</div><div className="stat-label">Recomendados</div></div>
        <div className="stat stat-minimos"><div className="stat-value">{stats.minimos || 0}</div><div className="stat-label">Mínimos</div></div>
        <div className="stat stat-capaz"><div className="stat-value">{stats.capaz || 0}</div><div className="stat-label">Capaces</div></div>
        <div className="stat stat-no_corre"><div className="stat-value">{stats.no_corre || 0}</div><div className="stat-label">No corren</div></div>
        <div className="stat stat-sin_datos_cpu"><div className="stat-value">{stats.sin_datos_cpu || 0}</div><div className="stat-label">Sin datos CPU</div></div>
      </div>

      <div className="search-bar">
        <input type="text" placeholder="Buscar por marca, clave, procesador..." value={searchQuery} onChange={e => setSearchQuery(e.target.value)} />
        <span className="result-count">{filteredProducts.length} de {allProducts.length} productos</span>
      </div>

      <main className="main">
        {filteredProducts.length === 0 ? (
          <div className="empty-state">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>
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
              referrerPolicy="no-referrer"
              onError={handleImageError}
            />
            <div className="product-image placeholder" style={{ display: 'none' }}>🖥️</div>
          </>
        ) : (
          <div className="product-image placeholder">🖥️</div>
        )}
        
        <span className={`status-badge ${STATUS_CLASSES[product.nivel] || 'status-sin_datos_cpu'}`}>{statusLabel}</span>
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