const STATUS_LABELS = {
  recommended: 'Recomendado',
  minimos: 'M&iacute;nimos',
  capaz: 'Capaz',
  no_corre: 'No corre',
  sin_datos_cpu: 'Sin datos CPU'
}

const STATUS_CLASSES = {
  recommended: 'status-recommended',
  minimos: 'status-minimos',
  capaz: 'status-capaz',
  no_corre: 'status-no_corre',
  sin_datos_cpu: 'status-sin_datos_cpu'
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
            <div className="product-image placeholder" style={{ display: 'none' }}></div>
          </>
        ) : (
          <div className="product-image placeholder"></div>
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
            Ver producto en CTOnline &rarr;
          </a>
        )}
      </div>
    </article>
  )
}

export default ProductCard
