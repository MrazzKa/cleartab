import { useEffect, useState } from 'react'
import { api, money } from '../api'
import { useT } from '../i18n'

interface PriceRow {
  ccn: string; hospital: string; city: string; phone: string | null; distance_miles: number | null
  gross: { amount: number | null }; cash: { amount: number | null }
  negotiated: { kind: string; median: number | null; min?: number | null; max?: number | null } | null
  completeness: { label: string }; provenance: { source_url: string; downloaded_at: string }
}

export default function Prices() {
  const t = useT()
  const [q, setQ] = useState('knee mri')
  const [plan, setPlan] = useState('cash')
  const [zip, setZip] = useState('85719')
  const [plans, setPlans] = useState<string[]>([])
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [res, setRes] = useState<any>(null)
  const [error, setError] = useState('')

  useEffect(() => { api.plans().then(setPlans).catch(() => setPlans([])) }, [])

  const go = async () => {
    setError('')
    try { setRes(await api.search(q, plan, zip)) } catch (e) { setRes(null); setError((e as Error).message) }
  }

  return (
    <div className="stack-lg">
      <section className="hero">
        <h1>{t('Look up a published price')}</h1>
        <p>{t('What Tucson and Phoenix hospitals published for 50 common procedures. These are facility charges; the doctor bills separately.')}</p>
      </section>
      <section className="card stack">
        <div className="grid2">
          <label className="field">{t('Procedure or code')}<input value={q} onChange={(e) => setQ(e.target.value)} /></label>
          <label className="field">{t('Insurance')}
            <select value={plan} onChange={(e) => setPlan(e.target.value)}>
              <option value="cash">{t('No insurance (cash price)')}</option>
              {plans.map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
          </label>
          <label className="field">{t('ZIP code')}<input inputMode="numeric" maxLength={5} value={zip} onChange={(e) => setZip(e.target.value)} /></label>
        </div>
        <div><button type="button" onClick={go}>{t('Search')}</button></div>
        {error && <p className="error-box" role="alert">{error}</p>}
      </section>
      {res && (
        <section className="stack">
          <h2>{res.procedure.plain_name} <span className="muted mono small">{res.procedure.code}</span></h2>
          <p className="small muted">{res.explainer}</p>
          <div className="table-wrap card">
            <table>
              <thead><tr><th>{t('Hospital')}</th><th>{t('Cash')}</th><th>{plan === 'cash' ? t('List price') : t('Your insurer')}</th><th>{t('Data')}</th></tr></thead>
              <tbody>
                {(res.results as PriceRow[]).map((r) => (
                  <tr key={r.ccn}>
                    <td><b>{r.hospital}</b><br /><span className="small muted">{r.city}{r.distance_miles != null && `, ${r.distance_miles} mi`}</span></td>
                    <td className="num">{money(r.cash.amount)}</td>
                    <td className="num">{plan === 'cash' ? money(r.gross.amount)
                      : r.negotiated?.median != null ? money(r.negotiated.median) : <span className="muted small">{r.negotiated?.kind ?? '-'}</span>}</td>
                    <td className="small"><a href={r.provenance.source_url} target="_blank" rel="noreferrer">{t('file')}</a>, {t(r.completeness.label)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  )
}
