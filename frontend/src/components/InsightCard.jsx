import { INSIGHT_STATUS_META } from '../constants/tables'

function getInsightStatusMeta(status) {
  return INSIGHT_STATUS_META[status] || null
}

export default function InsightCard({ item, selectedInsightId, onSelect, onDelete }) {
  const createdTime = new Date(item.createdAt).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  })
  const statusMeta = getInsightStatusMeta(item.hypothesisStatus)

  return (
    <article
      className={'insight-card' + (item.id === selectedInsightId ? ' insight-card--active' : '')}
      onClick={() => onSelect(item.id)}
    >
      <header className="insight-card-header">
        <div>
          <div className="insight-title">{item.title}</div>
          <div className="insight-meta">
            <span className="insight-time">Added at {createdTime}</span>
          </div>
        </div>
        <div className="insight-card-header-right">
          {statusMeta && <span className={statusMeta.className}>{statusMeta.label}</span>}
          <button
            type="button"
            className="insight-delete-btn"
            onClick={e => {
              e.stopPropagation()
              onDelete(item.id)
            }}
          >
            ×
          </button>
        </div>
      </header>
      <div className="insight-body">
        {item.summary && Array.isArray(item.summary.bullets) ? (
          <ul className="insight-bullets">
            {item.summary.bullets.map((bullet, idx) => (
              <li key={idx}>{bullet}</li>
            ))}
          </ul>
        ) : (
          <div className="insight-metrics">
            {Object.keys(item.metrics || {}).length === 0 && (
              <p className="insights-empty">We did not receive extra details for this note yet.</p>
            )}
            {Object.entries(item.metrics || {}).map(([key, value]) => (
              <span key={key} className="insight-pill">
                {key}: {String(value)}
              </span>
            ))}
          </div>
        )}
        {item.summary && item.summary.conclusion && (
          <p className="insight-conclusion">{item.summary.conclusion}</p>
        )}
      </div>
    </article>
  )
}
