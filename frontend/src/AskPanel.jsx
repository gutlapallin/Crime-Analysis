import { useState } from 'react'
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid,
} from 'recharts'

const EXAMPLES = [
  'Which hour of the day has the most crime?',
  'Is crime higher in summer or winter?',
  'Which community areas have the most crime?',
  'Does theft increase on Christmas?',
]

export default function AskPanel() {
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  async function ask(q) {
    const text = (q ?? question).trim()
    if (!text) return
    setQuestion(text)
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const res = await fetch('/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: text }),
      })
      let data = null
      try { data = await res.json() } catch { /* non-JSON response */ }
      if (!res.ok) {
        setError(
          res.status === 429
            ? 'Too many questions. Please wait a minute and try again.'
            : (data && data.error) || `Something went wrong (HTTP ${res.status}). Please try again.`
        )
      } else {
        setResult(data)
      }
    } catch (e) {
      setError('Could not reach the server.')
    } finally {
      setLoading(false)
    }
  }

  const rows = (result && result.rows) || []
  const cols = rows.length ? Object.keys(rows[0]) : []
  const showChart =
    result && result.chart !== 'none' && result.x && result.y &&
    cols.includes(result.x) && cols.includes(result.y)
  // MySQL sums can arrive as strings, so convert the y values to numbers
  const chartData = showChart
    ? rows.map(r => ({ ...r, [result.y]: Number(r[result.y]) }))
    : []

  const box = {
    border: '1px solid #ccc', borderRadius: 8, padding: 16,
    margin: '16px 0', background: '#fff', color: '#222',
  }

  return (
    <div style={box}>
      <h2 style={{ marginTop: 0 }}>Ask the data</h2>
      <div style={{ display: 'flex', gap: 8 }}>
        <input
          value={question}
          onChange={e => setQuestion(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && ask()}
          placeholder="Ask a question about Chicago crime..."
          maxLength={500}
          style={{ flex: 1, padding: 8, fontSize: 16 }}
        />
        <button onClick={() => ask()} disabled={loading || !question.trim()}
                style={{ padding: '8px 16px', fontSize: 16 }}>
          {loading ? 'Thinking...' : 'Ask'}
        </button>
      </div>

      <div style={{ marginTop: 8, display: 'flex', flexWrap: 'wrap', gap: 6 }}>
        {EXAMPLES.map(ex => (
          <button key={ex} onClick={() => ask(ex)} disabled={loading}
                  style={{ fontSize: 12, padding: '4px 8px', cursor: 'pointer' }}>
            {ex}
          </button>
        ))}
      </div>

      {error && <p style={{ color: '#b00020' }}>{error}</p>}

      {result && (
        <div style={{ marginTop: 16 }}>
          <p style={{ fontSize: 16 }}>{result.answer}</p>

          {showChart && (
            <div style={{ width: '100%', height: 300 }}>
              <ResponsiveContainer>
                {result.chart === 'line' ? (
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey={result.x} />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey={result.y} stroke="#1976d2" />
                  </LineChart>
                ) : (
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey={result.x} />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey={result.y} fill="#1976d2" />
                  </BarChart>
                )}
              </ResponsiveContainer>
            </div>
          )}

          {result.sql && (
            <details style={{ marginTop: 12 }}>
              <summary>SQL used{result.source ? ' · ' + result.source : ''}{result.tables_used ? ' (' + result.tables_used.join(', ') + ')' : ''}</summary>
              <pre style={{ whiteSpace: 'pre-wrap', background: '#f5f5f5', padding: 8 }}>{result.sql}</pre>
            </details>
          )}

          {rows.length > 0 && (
            <details style={{ marginTop: 8 }}>
              <summary>Data ({rows.length} rows)</summary>
              <div style={{ overflowX: 'auto', maxHeight: 300 }}>
                <table style={{ borderCollapse: 'collapse', fontSize: 14 }}>
                  <thead>
                    <tr>{cols.map(c => (
                      <th key={c} style={{ border: '1px solid #ddd', padding: 4, textAlign: 'left' }}>{c}</th>
                    ))}</tr>
                  </thead>
                  <tbody>
                    {rows.map((r, i) => (
                      <tr key={i}>{cols.map(c => (
                        <td key={c} style={{ border: '1px solid #ddd', padding: 4 }}>{String(r[c])}</td>
                      ))}</tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </details>
          )}
        </div>
      )}
    </div>
  )
}
