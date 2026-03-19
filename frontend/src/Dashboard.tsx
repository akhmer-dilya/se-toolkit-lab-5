import { useState, useEffect } from 'react'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  LineElement,
  PointElement,
} from 'chart.js'
import { Bar, Line } from 'react-chartjs-2'

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  LineElement,
  PointElement,
)

const STORAGE_KEY = 'api_key'

interface ScoreBucket {
  bucket: string
  count: number
}

interface TimelineEntry {
  date: string
  submissions: number
}

interface PassRateEntry {
  task: string
  avg_score: number
  attempts: number
}

interface GroupEntry {
  group: string
  avg_score: number
  students: number
}

interface LabItem {
  id: number
  type: string
  title: string
}

function Dashboard() {
  const [token, setToken] = useState(() => localStorage.getItem(STORAGE_KEY) ?? '')
  const [draft, setDraft] = useState('')
  const [selectedLab, setSelectedLab] = useState<string>('lab-04')
  const [labs, setLabs] = useState<LabItem[]>([])
  const [scoresData, setScoresData] = useState<ScoreBucket[]>([])
  const [timelineData, setTimelineData] = useState<TimelineEntry[]>([])
  const [passRatesData, setPassRatesData] = useState<PassRateEntry[]>([])
  const [groupsData, setGroupsData] = useState<GroupEntry[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!token) return

    fetch('/items/', {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then((data: LabItem[]) => {
        const labItems = data.filter((item) => item.type === 'lab')
        setLabs(labItems)
        if (labItems.length > 0 && !selectedLab) {
          const firstLabId = labItems[0].title.match(/Lab\s*(\d+)/)?.[1]
          if (firstLabId) {
            setSelectedLab(`lab-${firstLabId.padStart(2, '0')}`)
          }
        }
      })
      .catch((err: Error) => setError(err.message))
  }, [token, selectedLab])

  useEffect(() => {
    if (!token || !selectedLab) return

    setLoading(true)
    setError(null)

    const labParam = selectedLab

    Promise.all([
      fetch(`/analytics/scores?lab=${labParam}`, {
        headers: { Authorization: `Bearer ${token}` },
      }),
      fetch(`/analytics/timeline?lab=${labParam}`, {
        headers: { Authorization: `Bearer ${token}` },
      }),
      fetch(`/analytics/pass-rates?lab=${labParam}`, {
        headers: { Authorization: `Bearer ${token}` },
      }),
      fetch(`/analytics/groups?lab=${labParam}`, {
        headers: { Authorization: `Bearer ${token}` },
      }),
    ])
      .then(([scoresRes, timelineRes, passRatesRes, groupsRes]) => {
        if (!scoresRes.ok) throw new Error(`Scores: HTTP ${scoresRes.status}`)
        if (!timelineRes.ok)
          throw new Error(`Timeline: HTTP ${timelineRes.status}`)
        if (!passRatesRes.ok)
          throw new Error(`Pass-rates: HTTP ${passRatesRes.status}`)
        if (!groupsRes.ok) throw new Error(`Groups: HTTP ${groupsRes.status}`)

        return Promise.all([
          scoresRes.json() as Promise<ScoreBucket[]>,
          timelineRes.json() as Promise<TimelineEntry[]>,
          passRatesRes.json() as Promise<PassRateEntry[]>,
          groupsRes.json() as Promise<GroupEntry[]>,
        ])
      })
      .then(([scores, timeline, passRates, groups]) => {
        setScoresData(scores)
        setTimelineData(timeline)
        setPassRatesData(passRates)
        setGroupsData(groups)
        setLoading(false)
      })
      .catch((err: Error) => {
        setError(err.message)
        setLoading(false)
      })
  }, [token, selectedLab])

  function handleConnect(e: React.FormEvent) {
    e.preventDefault()
    const trimmed = draft.trim()
    if (!trimmed) return
    localStorage.setItem(STORAGE_KEY, trimmed)
    setToken(trimmed)
  }

  function handleDisconnect() {
    localStorage.removeItem(STORAGE_KEY)
    setToken('')
    setDraft('')
  }

  function handleLabChange(e: React.ChangeEvent<HTMLSelectElement>) {
    setSelectedLab(e.target.value)
  }

  // Chart data preparation
  const scoresChartData = {
    labels: scoresData.map((s) => s.bucket),
    datasets: [
      {
        label: 'Number of Students',
        data: scoresData.map((s) => s.count),
        backgroundColor: 'rgba(54, 162, 235, 0.6)',
        borderColor: 'rgba(54, 162, 235, 1)',
        borderWidth: 1,
      },
    ],
  }

  const timelineChartData = {
    labels: timelineData.map((t) => t.date),
    datasets: [
      {
        label: 'Submissions',
        data: timelineData.map((t) => t.submissions),
        borderColor: 'rgba(75, 192, 192, 1)',
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        tension: 0.1,
        fill: true,
      },
    ],
  }

  if (!token) {
    return (
      <form className="token-form" onSubmit={handleConnect}>
        <h1>API Key</h1>
        <p>Enter your API key to connect.</p>
        <input
          type="password"
          placeholder="Token"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
        />
        <button type="submit">Connect</button>
      </form>
    )
  }

  return (
    <div>
      <header className="app-header">
        <h1>Analytics Dashboard</h1>
        <button className="btn-disconnect" onClick={handleDisconnect}>
          Disconnect
        </button>
      </header>

      <div className="dashboard-controls">
        <label htmlFor="lab-select">Select Lab: </label>
        <select
          id="lab-select"
          value={selectedLab}
          onChange={handleLabChange}
        >
          {labs.map((lab) => {
            const labMatch = lab.title.match(/Lab\s*(\d+)/)
            const labId = labMatch ? `lab-${labMatch[1].padStart(2, '0')}` : lab.title
            return (
              <option key={lab.id} value={labId}>
                {lab.title}
              </option>
            )
          })}
        </select>
      </div>

      {loading && <p className="loading">Loading data...</p>}
      {error && <p className="error">Error: {error}</p>}

      {!loading && !error && (
        <div className="dashboard-grid">
          {/* Score Distribution Chart */}
          <div className="chart-container">
            <h2>Score Distribution</h2>
            <Bar
              data={scoresChartData}
              options={{
                responsive: true,
                plugins: {
                  legend: {
                    position: 'top' as const,
                  },
                  title: {
                    display: true,
                    text: 'Score Buckets (0-25, 26-50, 51-75, 76-100)',
                  },
                },
              }}
            />
          </div>

          {/* Timeline Chart */}
          <div className="chart-container">
            <h2>Submissions Timeline</h2>
            <Line
              data={timelineChartData}
              options={{
                responsive: true,
                plugins: {
                  legend: {
                    position: 'top' as const,
                  },
                  title: {
                    display: true,
                    text: 'Submissions per Day',
                  },
                },
              }}
            />
          </div>

          {/* Pass Rates Table */}
          <div className="table-container">
            <h2>Pass Rates by Task</h2>
            <table>
              <thead>
                <tr>
                  <th>Task</th>
                  <th>Avg Score</th>
                  <th>Attempts</th>
                </tr>
              </thead>
              <tbody>
                {passRatesData.map((entry) => (
                  <tr key={entry.task}>
                    <td>{entry.task}</td>
                    <td>{entry.avg_score.toFixed(1)}</td>
                    <td>{entry.attempts}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Groups Table */}
          <div className="table-container">
            <h2>Performance by Group</h2>
            <table>
              <thead>
                <tr>
                  <th>Group</th>
                  <th>Avg Score</th>
                  <th>Students</th>
                </tr>
              </thead>
              <tbody>
                {groupsData.map((entry) => (
                  <tr key={entry.group}>
                    <td>{entry.group}</td>
                    <td>{entry.avg_score.toFixed(1)}</td>
                    <td>{entry.students}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

export default Dashboard
