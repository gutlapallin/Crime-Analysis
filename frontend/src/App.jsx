import { useEffect, useState } from 'react'
import './App.css'
import ChartView from './components/ChartView'
import InsightCard from './components/InsightCard'
import { TABLE_META } from './constants/tables'

function buildNotesText(title, notes) {
  const lines = [`Notes for: ${title}`]
  notes.forEach(item => {
    const createdTime = new Date(item.createdAt).toLocaleString()
    lines.push('')
    lines.push(`Note from ${createdTime}`)
    if (item.hypothesisStatus) {
      lines.push(`Hypothesis status: ${item.hypothesisStatus}`)
    }
    if (item.summary && Array.isArray(item.summary.bullets)) {
      lines.push('')
      item.summary.bullets.forEach(bullet => {
        lines.push(`- ${bullet}`)
      })
    }
    if (item.summary && item.summary.conclusion) {
      lines.push('')
      lines.push(`Conclusion: ${item.summary.conclusion}`)
    }
  })
  return lines.join('\n')
}

export default function App() {
  const [categories, setCategories] = useState({})
  const [loadingCat, setLoadingCat] = useState(true)
  const [selectedTable, setSelectedTable] = useState(null)
  const [selectedLabel, setSelectedLabel] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [data, setData] = useState([])
  const [stats, setStats] = useState({})
  const [loadingData, setLoadingData] = useState(false)
  const [error, setError] = useState(null)

  const [insights, setInsights] = useState([])
  const [insightsLoading, setInsightsLoading] = useState(false)
  const [insightsError, setInsightsError] = useState(null)
  const [selectedInsightId, setSelectedInsightId] = useState(null)

  useEffect(() => {
    fetch('/api/categories')
      .then(res => res.json())
      .then(setCategories)
      .catch(() => setError('could not load categories'))
      .finally(() => setLoadingCat(false))
  }, [])

  useEffect(() => {
    if (!selectedTable) {
      setData([])
      setStats({})
      setInsights([])
      return
    }
    setLoadingData(true)
    setError(null)

    fetch('/api/data?table=' + encodeURIComponent(selectedTable))
      .then(res => res.json())
      .then(json => {
        setData(json.data || [])
        setStats(json.stats || {})
      })
      .catch(() => setError('could not load data'))
      .finally(() => setLoadingData(false))
  }, [selectedTable])

  const selectedMeta = (() => {
    if (!selectedTable) return null
    const meta = TABLE_META[selectedTable] || {}
    return {
      title: meta.question || selectedLabel || selectedTable,
      hypothesis: meta.hypothesis || null,
      description: meta.description || null,
      category: meta.category || null,
    }
  })()

  const currentInsights = insights.filter(item => item.tableKey === selectedTable)

  const normalizedSearch = searchTerm.trim().toLowerCase()

  function goHome() {
    setSelectedTable(null)
    setSelectedLabel(null)
    setSearchTerm('')
    setInsightsError(null)
    setSelectedInsightId(null)
    window.scrollTo(0, 0)
  }

  async function handleGenerateInsight() {
    if (!selectedTable) return
    setInsightsLoading(true)
    setInsightsError(null)
    try {
      const res = await fetch('/api/insights_llm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tableKey: selectedTable,
          stats,
          sampleRows: Array.isArray(data) ? data : [],
          question: selectedMeta?.title || selectedLabel || selectedTable,
          hypothesis: selectedMeta?.hypothesis || null,
        }),
      })
      if (!res.ok) {
        throw new Error('failed')
      }
      const json = await res.json()
      const now = new Date()
      const insight = {
        id: Date.now(),
        tableKey: selectedTable,
        title: selectedMeta ? selectedMeta.title : selectedLabel || selectedTable,
        createdAt: now.toISOString(),
        hypothesisStatus: json.hypothesis_status || null,
        metrics: json.metrics || {},
        summary: json.summary || null,
      }
      setInsights(prev => [insight, ...prev])
      setSelectedInsightId(insight.id)
    } catch (e) {
      setInsightsError('We could not generate an insight for this view right now.')
    } finally {
      setInsightsLoading(false)
    }
  }

  function handleDeleteInsight(id) {
    setInsights(prev => prev.filter(item => item.id !== id))
    if (selectedInsightId === id) {
      setSelectedInsightId(null)
    }
  }

  async function handleCopyInsights() {
    if (currentInsights.length === 0) {
      setInsightsError('There are no notes to copy for this view yet.')
      return
    }
    const headerTitle = selectedMeta ? selectedMeta.title : selectedLabel || selectedTable
    const text = buildNotesText(headerTitle, currentInsights)
    try {
      await navigator.clipboard.writeText(text)
      setInsightsError(null)
    } catch (e) {
      setInsightsError('We could not copy your notes. You can still select and copy them manually.')
    }
  }

  if (loadingCat) {
    return (
      <div className="app-root">
        <header className="app-header">
          <div>
            <h1 className="app-title">Chicago Crime Analysis</h1>
            <p className="app-subtitle">Loading question catalog…</p>
          </div>
          <span className="app-badge">CS 179G · Big Data</span>
        </header>
      </div>
    )
  }

  if (error && !selectedTable) {
    return (
      <div className="app-root">
        <header className="app-header">
          <div>
            <h1 className="app-title">Chicago Crime Analysis</h1>
            <p className="app-subtitle">Explore patterns, hotspots, and long‑term trends.</p>
          </div>
          <span className="app-badge">CS 179G · Big Data</span>
        </header>
        <div className="app-shell">
          <aside className="shell-sidebar">
            <h2 className="sidebar-heading">Questions</h2>
            <p className="sidebar-caption">We could not load the list of analyses from the server.</p>
          </aside>
          <main className="shell-main">
            <section className="panel">
              <p className="panel-error">{error}</p>
            </section>
          </main>
        </div>
      </div>
    )
  }

  return (
    <div className="app-root">
      <header className="app-header">
        <div>
          <h1 className="app-title">Chicago Crime Analysis</h1>
          <p className="app-subtitle">
            Explore patterns in reported crime across time and place in Chicago.
          </p>
        </div>
        <div className="app-header-actions">
          {selectedTable && (
            <button
              type="button"
              className="home-tab-btn"
              onClick={goHome}
            >
              Home
            </button>
          )}
          <span className="app-badge">CS 179G · Big Data</span>
        </div>
      </header>

      <div className="app-shell">
        <aside className="shell-sidebar">
          <h2 className="sidebar-heading">Questions &amp; hypotheses</h2>
          <p className="sidebar-caption">
            Pick a question to load the corresponding analysis and visualizations.
          </p>

          <div className="sidebar-search">
            <input
              type="search"
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              placeholder="Search e.g. airport, transit…"
              className="sidebar-search-input"
            />
          </div>

          {Object.keys(categories).map(categoryName => {
            const rawEntries = Object.entries(categories[categoryName])
            const filteredEntries = !normalizedSearch
              ? rawEntries
              : rawEntries.filter(([label, table]) => {
                  const meta = TABLE_META[table] || {}
                  const haystack =
                    (label + ' ' + (meta.question || '') + ' ' + (meta.description || '')).toLowerCase()
                  return haystack.includes(normalizedSearch)
                })

            if (filteredEntries.length === 0) {
              return null
            }

            return (
              <div key={categoryName} className="sidebar-section">
                <div className="sidebar-section-title">{categoryName}</div>
                <ul className="sidebar-list">
                  {filteredEntries.map(([label, table]) => {
                    const meta = TABLE_META[table] || {}
                    const isActive = table === selectedTable
                    return (
                      <li key={table} className="sidebar-item">
                        <button
                          type="button"
                          className={
                            'sidebar-link' + (isActive ? ' sidebar-link--active' : '')
                          }
                          onClick={() => {
                            setSelectedTable(table)
                            setSelectedLabel(label)
                          }}
                        >
                          <span className="sidebar-link-label">
                            {meta.question || label}
                          </span>
                          <span className="sidebar-link-meta">
                            {meta.description || 'View aggregated results'}
                          </span>
                        </button>
                      </li>
                    )
                  })}
                </ul>
              </div>
            )
          })}
        </aside>

        <main className="shell-main">
          {!selectedTable && (
            <section className="panel">
              <div className="intro-grid">
                <div className="intro-main">
                  <div className="intro-kicker">Welcome</div>
                  <h2 className="intro-title">Explore Chicago crime in a simple way</h2>
                  <p className="intro-body">
                    This site helps you explore patterns in reported crime across Chicago. The goal
                    is to make it easier to see when and where crime is more common, so it is easier
                    to think about safety and risk.
                  </p>
                  <div className="intro-steps">
                    <div className="intro-step">
                      <span className="intro-step-dot">1</span>
                      <div>
                        <div className="intro-step-label">Pick a question on the left</div>
                        <div className="intro-step-text">
                          For example: crime by time of day, by season, over the years, or by area.
                        </div>
                      </div>
                    </div>
                    <div className="intro-step">
                      <span className="intro-step-dot">2</span>
                      <div>
                        <div className="intro-step-label">Look at the numbers and table</div>
                        <div className="intro-step-text">
                          See simple summary numbers plus a small table of results for that view.
                        </div>
                      </div>
                    </div>
                    <div className="intro-step">
                      <span className="intro-step-dot">3</span>
                      <div>
                        <div className="intro-step-label">Create short notes about what you see</div>
                        <div className="intro-step-text">
                          Use the insight panel to turn the numbers into concise explanations you
                          can save or share with others.
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="intro-side">
                  <div className="intro-side-card">
                    <div className="intro-side-title">What this is for</div>
                    <p className="intro-side-text">
                      The goal is to use real data to think about safety in Chicago. The same style
                      of analysis can support people who live in the city, people planning a visit,
                      and local decision‑makers who care about fair access to safe places.
                    </p>
                    <ul className="intro-side-list">
                      <li>Helps surface areas and times with more reported crime</li>
                      <li>Focuses on overall patterns instead of single incidents</li>
                      <li>Useful for thinking about safety when living in or visiting Chicago</li>
                    </ul>
                  </div>
                </div>
              </div>
            </section>
          )}

          {selectedTable && (
            <>
              <section className="panel">
                <div className="panel-header">
                  <div>
                    <h2 className="panel-title">
                      {selectedMeta ? selectedMeta.title : selectedLabel || selectedTable}
                    </h2>
                    {selectedMeta?.hypothesis && (
                      <p className="panel-hypothesis">
                        <strong>Hypothesis:</strong> {selectedMeta.hypothesis}
                      </p>
                    )}
                    {selectedMeta?.description && (
                      <p className="panel-description">{selectedMeta.description}</p>
                    )}
                  </div>
                  {selectedMeta?.category && (
                    <span className="panel-pill">{selectedMeta.category}</span>
                  )}
                </div>

                {loadingData && <p className="panel-muted">Loading data…</p>}
                {!loadingData && error && (
                  <p className="panel-error">Could not load data for this view.</p>
                )}

                {!loadingData && !error && (
                  <>
                    {Object.keys(stats).length > 0 && (
                      <div className="stats">
                        {Object.entries(stats).map(([k, v]) => (
                          <span key={k} className="stats-pill">
                            {k}: {String(v)}
                          </span>
                        ))}
                      </div>
                    )}

                    <div className="panel-subgrid">
                      <div className="placeholder-card">
                        <div>
                          <div className="placeholder-title">Visualizations</div>
                          <p className="placeholder-body">
                            Explore the main pattern for this question with a chart or map view.
                          </p>
                        </div>
                        <ChartView table={selectedTable} data={data} />
                      </div>
                      <div className="placeholder-card insight-panel-card">
                        <div className="insight-panel-header">
                          <div>
                            <div className="placeholder-title">Insight and report notes</div>
                            <p className="placeholder-body">
                              Create short notes from the numbers in this view.
                            </p>
                          </div>
                        </div>

                        <div className="insight-actions">
                          <button
                            type="button"
                            className="insight-generate-btn"
                            onClick={handleGenerateInsight}
                            disabled={!selectedTable || loadingData || insightsLoading}
                          >
                            {insightsLoading ? 'Creating insight…' : 'Explain this view'}
                          </button>
                          <button
                            type="button"
                            className="insight-export-btn"
                            onClick={handleCopyInsights}
                            disabled={currentInsights.length === 0}
                          >
                            Copy notes
                          </button>
                        </div>

                        {insightsError && (
                          <p className="insights-error">{insightsError}</p>
                        )}

                        <div className="insights-list">
                          {currentInsights.length === 0 && !insightsLoading && (
                            <p className="insights-empty">
                              No notes yet for this question. Start by choosing “Explain this view”.
                            </p>
                          )}
                          {currentInsights.map(item => (
                            <InsightCard
                              key={item.id}
                              item={item}
                              selectedInsightId={selectedInsightId}
                              onSelect={setSelectedInsightId}
                              onDelete={handleDeleteInsight}
                            />
                          ))}
                        </div>
                      </div>
                    </div>
                  </>
                )}
              </section>

              <section className="panel table-panel">
                {data.length === 0 && !loadingData && !error ? (
                  <p className="panel-muted">No rows returned for this selection.</p>
                ) : (
                  <>
                    <div className="table-heading-row">
                      <div className="table-title">Underlying table</div>
                      <div className="table-caption">
                        A simple view of the data behind this question so you can see what the
                        numbers are based on.
                      </div>
                    </div>
                    {data.length > 0 && (
                      <table>
                        <thead>
                          <tr>
                            {Object.keys(data[0]).map(col => (
                              <th key={col}>{col}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {data.map((row, i) => (
                            <tr key={i}>
                              {Object.keys(data[0]).map(col => (
                                <td key={col}>{row[col] != null ? String(row[col]) : ''}</td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                  </>
                )}
              </section>
            </>
          )}
        </main>
      </div>
    </div>
  )
}
