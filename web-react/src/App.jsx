import { useState, useEffect, useCallback, useRef } from 'react'
import Header from './components/Header'
import RequirementsPanel from './components/RequirementsPanel'
import Filters from './components/Filters'
import StatsBar from './components/StatsBar'
import ProductCard from './components/ProductCard'
import './App.css'

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
  const [classifying, setClassifying] = useState(false)
  const classifyTimer = useRef(null)

  const applyFilters = useCallback((products) => {
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
        `${p.marca} ${p.clave} ${p.procesador} ${p.descripcion || ''}`.toLowerCase().includes(q)
      )
    }
    result.sort((a, b) => (b.score || 0) - (a.score || 0))
    setFilteredProducts(result)
  }, [categoryFilter, statusFilter, searchQuery])

  const loadData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch('/api/products')
      if (!res.ok) throw new Error('Error al cargar datos del servidor')
      const data = await res.json()
      if (!data.products || data.products.length === 0) {
        throw new Error('No se encontraron datos. Ejecuta primero: python -m src compare --cat "All in One" --cat "Laptops"')
      }
      setAllProducts(data.products)
      if (data.last_updated) {
        setLastUpdated(new Date(data.last_updated))
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  const reclassify = useCallback(async (req) => {
    if (allProducts.length === 0) return
    setClassifying(true)
    try {
      const payload = {
        products: allProducts.map(p => ({
          clave: p.clave,
          marca: p.marca || '',
          procesador: p.procesador || '',
          ram_gb: p.ram_gb || 0,
          storage_gb: p.storage_gb || 0,
          storage_type: p.storage_type || 'UNKNOWN',
          os: p.os || 'Unknown',
          cpu_turbo_ghz: p.cpu_turbo_ghz ?? null,
          cpu_cores: p.cpu_cores ?? null,
          cpu_source: p.cpu_source || 'none',
          url: p.url || '',
          imagen: p.imagen || '',
          categoria: p.categoria || '',
          categoriaLabel: p.categoriaLabel || '',
          descripcion: p.descripcion || '',
        })),
        requirements: {
          cpu: { min_ghz: req.cpu.min_ghz, min_cores: req.cpu.min_cores, rec_ghz: req.cpu.rec_ghz, rec_cores: req.cpu.rec_cores },
          ram_min_gb: req.ram_min_gb,
          ram_rec_gb: req.ram_rec_gb,
          disk_min_gb: req.disk_min_gb,
          disk_rec_gb: req.disk_rec_gb,
          ssd_required_below_gb: req.ssd_required_below_gb,
          os_min: req.os_min,
          os_rec: req.os_rec,
        }
      }
      const res = await fetch('/api/classify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!res.ok) throw new Error('Error al reclasificar')
      const result = await res.json()
      const updates = new Map(result.products.map(p => [p.clave, p]))
      const updated = allProducts.map(p => {
        const cls = updates.get(p.clave)
        return cls ? { ...p, nivel: cls.nivel, puede_correr: cls.puede_correr, razones: cls.razones, score: cls.score } : p
      })
      setAllProducts(updated)
    } catch (err) {
      console.error('Reclassification error:', err)
    } finally {
      setClassifying(false)
    }
  }, [allProducts])

  useEffect(() => { loadData() }, [loadData])

  useEffect(() => { applyFilters(allProducts) }, [allProducts, applyFilters])

  useEffect(() => {
    if (classifyTimer.current) clearTimeout(classifyTimer.current)
    classifyTimer.current = setTimeout(() => { reclassify(requirements) }, 300)
    return () => { if (classifyTimer.current) clearTimeout(classifyTimer.current) }
  }, [requirements])

  const handleRefresh = async () => {
    setRefreshing(true)
    setRefreshOutput('Iniciando...')
    try {
      const res = await fetch('/api/refresh', { method: 'POST' })
      if (res.status === 429) {
        const err = await res.json()
        setRefreshOutput(err.detail || 'Espera antes de recargar')
        setRefreshing(false)
        return
      }
      const { task_id } = await res.json()
      setRefreshOutput('Scrapeando y comparando...')
      const poll = setInterval(async () => {
        const statusRes = await fetch(`/api/refresh-status/${task_id}`)
        const status = await statusRes.json()
        if (status.status === 'done') {
          clearInterval(poll)
          setRefreshOutput(status.error ? `Error: ${status.error}` : 'Datos actualizados')
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

  const stats = allProducts.reduce((acc, p) => {
    acc[p.nivel] = (acc[p.nivel] || 0) + 1
    return acc
  }, {})

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

  return (
    <div className="app">
      <Header
        lastUpdated={lastUpdated}
        refreshing={refreshing}
        refreshOutput={refreshOutput}
        showRequirements={showRequirements}
        onRefresh={handleRefresh}
        onToggleRequirements={() => setShowRequirements(!showRequirements)}
      />

      {showRequirements && (
        <RequirementsPanel
          requirements={requirements}
          onChange={handleReqChange}
          onReset={() => setRequirements(DEFAULT_REQUIREMENTS)}
          classifying={classifying}
        />
      )}

      <Filters
        categoryFilter={categoryFilter}
        statusFilter={statusFilter}
        searchQuery={searchQuery}
        onCategoryChange={setCategoryFilter}
        onStatusChange={setStatusFilter}
        onSearchChange={setSearchQuery}
        onClear={() => { setCategoryFilter(''); setStatusFilter(''); setSearchQuery('') }}
      />

      <StatsBar stats={stats} />

      <div className="search-bar">
        <input
          type="text"
          placeholder="Buscar por marca, clave, procesador..."
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
        />
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

export default App
