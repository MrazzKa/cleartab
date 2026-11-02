import { useEffect, useState } from 'react'
import { api, money } from '../api'
import type { AssistanceResponse, Hospital } from '../api'

const STATUS: Record<string, string> = {
  free: 'Free care', discount: 'Discount', above: 'Above the income limit', unknown: 'Ask the hospital',
  not_eligible: 'Not covered',
}

export default function Assistance() {
  const [size, setSize] = useState(1)
  const [income, setIncome] = useState('')
  const [coverage, setCoverage] = useState<'insured' | 'self_pay'>('self_pay')
  const [system, setSystem] = useState('')
  const [hospitals, setHospitals] = useState<Hospital[]>([])
  const [res, setRes] = useState<AssistanceResponse | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => { api.hospitals().then(setHospitals).catch(() => setHospitals([])) }, [])
  const systems = [...new Set(hospitals.map((h) => h.health_system))].sort()

  const go = async () => {
    setError(''); setBusy(true)
    try { setRes(await api.assistance(size, Number(income || 0), coverage, system || undefined)) } catch (e) {
      setError((e as Error).message)
    } finally { setBusy(false) }
  }

  return (
    <div className="stack-lg">
      <section className="hero">
        <h1>Can you get help paying a hospital bill?</h1>
        <p>Nonprofit hospitals must publish a financial assistance policy. Many people with insurance qualify too,
          for the part insurance did not pay. Enter your household and income; nothing is stored.</p>
      </section>
      <section className="card stack">
        <div className="grid2">
          <label className="field">People in your household
            <input type="number" min={1} max={20} value={size} onChange={(e) => setSize(Math.max(1, Number(e.target.value) || 1))} />
          </label>
          <label className="field">Yearly household income before taxes
            <input type="number" inputMode="decimal" min={0} placeholder="e.g. 42000" value={income} onChange={(e) => setIncome(e.target.value)} />
          </label>
          <label className="field">Did insurance pay part of the bill?
            <select value={coverage} onChange={(e) => setCoverage(e.target.value as 'insured' | 'self_pay')}>
              <option value="self_pay">No, I have no insurance or did not use it</option>
              <option value="insured">Yes, I owe the part insurance did not pay</option>
            </select>
          </label>
          <label className="field">Hospital system (optional)
            <select value={system} onChange={(e) => setSystem(e.target.value)}>
              <option value="">Show all</option>
              {systems.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </label>
        </div>
        <div><button type="button" onClick={go} disabled={busy || income === ''}>{busy ? 'Checking…' : 'See what I may qualify for'}</button></div>
        {error && <p className="error-box" role="alert">{error}</p>}
      </section>

      {res && (
        <section className="stack">
          <p>Your income is <b>{res.fpl_percent}%</b> of the {res.guidelines.year} federal poverty guideline
            ({money(res.poverty_line)} for {size} {size === 1 ? 'person' : 'people'};{' '}
            <a href={res.guidelines.source_url} target="_blank" rel="noreferrer">HHS</a>).</p>
          {res.results.map((r) => (
            <article key={r.system} className="card stack">
              <div className="row" style={{ justifyContent: 'space-between' }}>
                <h2>{r.system}</h2>
                <span className={`badge ${r.status}`}>{STATUS[r.status]}</span>
              </div>
              <p><b>{r.result}</b></p>
              <div className="grid2 small">
                <p><span className="muted">Covers: </span>{r.covers}</p>
                <p><span className="muted">When to apply: </span>{r.window}</p>
                <p><span className="muted">How: </span>{r.how_to_apply}</p>
                <p><span className="muted">Assets: </span>{r.assets_test}</p>
              </div>
              {r.phone && <p>Call <span className="mono">{r.phone}</span> and ask for financial assistance.</p>}
              {r.notes && <p className="small muted">{r.notes}</p>}
              <p className="sources">Source: <a href={r.source_url} target="_blank" rel="noreferrer">hospital's published policy</a> (read {r.retrieved_at})</p>
            </article>
          ))}
          <p className="small muted">{res.note}</p>
        </section>
      )}
    </div>
  )
}
