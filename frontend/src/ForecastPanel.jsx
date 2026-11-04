import { useEffect, useState } from 'react'
import {
  ComposedChart, Area, Line, XAxis, YAxis, Tooltip, Legend,
  ResponsiveContainer, CartesianGrid, ReferenceLine,
} from 'recharts'

const fmt = n => (n == null ? '—' : Math.round(n).toLocaleString())

export default function ForecastPanel() {
  const [series, setSeries] = useState('ALL')
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    setLoading(true)
    setError('')
    fetch('/api/forecast?series=' + encodeURIComponent(series))
      .then(async res => {
        const json = await res.json().catch(() => null)
        if (!res.ok) throw new Error((json && json.error) || `HTTP ${res.status}`)
        setData(json)
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [series])

  // One row per month: actual history, then forecast months with the 80% band.
  // The last history month also starts the forecast line so the two connect.
  const history = data ? data.history : []
  const last = history[history.length - 1]
  const chartData = data
    ? [
        ...history.map(h => ({
          date: h.date,
          actual: h.value,
          predicted: h === last ? h.value : null,
        })),
        ...data.forecast.map(f => ({
          date: f.date,
          actual: f.actual,
          predicted: f.predicted,
          band: [f.lower, f.upper],
        })),
      ]
    : []

  const m = data && data.metrics
  const covidMonths = data ? data.forecast.filter(f => f.actual != null) : []
  const worst = covidMonths.reduce(
    (w, f) => (w == null || f.actual / f.predicted < w.actual / w.predicted ? f : w), null)
  const name = series === 'ALL' ? 'All crime' : series.charAt(0) + series.slice(1).toLowerCase()

  const box = {
    border: '1px solid #ccc', borderRadius: 8, padding: 16,
    margin: '16px 0', background: '#fff', color: '#222',
  }
  const stat = { flex: '1 1 140px', padding: 12, background: '#f5f5f5', borderRadius: 6 }

  return (
    <div style={box}>
      <h2 style={{ marginTop: 0 }}>Crime forecast</h2>
      <p style={{ marginTop: 0 }}>
        What crime would have looked like without COVID-19: a Holt-Winters model trained on data
        through February 2020, compared with what actually happened.
      </p>

      <label>
        Crime type:{' '}
        <select value={series} onChange={e => setSeries(e.target.value)} style={{ fontSize: 16, padding: 4 }}>
          {(data ? data.available : ['ALL']).map(s => (
            <option key={s} value={s}>{s === 'ALL' ? 'All crime' : s}</option>
          ))}
        </select>
      </label>

      {error && <p style={{ color: '#b00020' }}>{error}</p>}
      {loading && !data && <p>Loading…</p>}

      {data && m && (
        <>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, margin: '16px 0' }}>
            <div style={stat}>
              <div style={{ fontSize: 13 }}>Mar–Jun 2020 vs. forecast</div>
              <div style={{ fontSize: 24, fontWeight: 700 }}>{m.covid_gap_pct.toFixed(1)}%</div>
            </div>
            <div style={stat}>
              <div style={{ fontSize: 13 }}>Model error (held-out year)</div>
              <div style={{ fontSize: 24, fontWeight: 700 }}>{m.mape.toFixed(1)}%</div>
              <div style={{ fontSize: 12 }}>baseline {m.baseline_mape.toFixed(1)}%</div>
            </div>
            <div style={stat}>
              <div style={{ fontSize: 13 }}>COVID months below the 80% range</div>
              <div style={{ fontSize: 24, fontWeight: 700 }}>{m.months_below_interval} of {covidMonths.length}</div>
            </div>
          </div>

          {worst && (
            <p>
              {name}: the largest drop was in {worst.date}, with {fmt(worst.actual)} reported crimes
              against {fmt(worst.predicted)} expected ({m.worst_month_gap_pct.toFixed(1)}%).
            </p>
          )}

          <div style={{ width: '100%', height: 360 }}>
            <ResponsiveContainer>
              <ComposedChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" minTickGap={24} />
                <YAxis tickFormatter={fmt} width={70} />
                <Tooltip
                  formatter={(v, key) => [Array.isArray(v) ? `${fmt(v[0])} – ${fmt(v[1])}` : fmt(v), key]}
                />
                <Legend />
                <ReferenceLine x={data.forecast[0].date} stroke="#999" strokeDasharray="4 4" />
                <Area dataKey="band" name="80% range" fill="#1976d2" fillOpacity={0.15} stroke="none" />
                <Line dataKey="predicted" name="Forecast (no COVID)" stroke="#1976d2"
                      strokeDasharray="6 4" dot={false} connectNulls={false} />
                <Line dataKey="actual" name="Actual" stroke="#222" dot={false} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>

          <p style={{ fontSize: 13, color: '#555' }}>
            Model: {m.model}, trained {m.train_start} to {m.train_end}. Data ends June 2020, so later
            months show the forecast only.
          </p>
        </>
      )}
    </div>
  )
}
