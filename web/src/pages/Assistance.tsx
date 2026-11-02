import { useEffect, useMemo, useState } from 'react'
import { api, money } from '../api'
import type { AssistanceResponse, AssistanceResult, Hospital } from '../api'

// "Lower my bill": which hospital, household, income -> what that hospital's own policy says, and an application
// kit. Income and the letter's personal details stay in this browser tab; only household size, income and the
// hospital system go to the API for one answer, and the API never logs or stores them.
const HEADLINE: Record<AssistanceResult['status'], string> = {
  free: 'You may qualify for free care',
  discount: 'You may qualify for a discount',
  above: 'Your income is above this hospital’s published limit',
  unknown: 'This hospital does not publish clear limits',
  not_eligible: 'This policy does not cover your situation',
}

function Choice({ options, onPick }: { options: [string, string, string?][]; onPick: (v: string) => void }) {
  return (
    <div className="choices">
      {options.map(([v, label, hint]) => (
        <button key={v} type="button" className="choice" onClick={() => onPick(v)}>
          <span>{label}</span>{hint && <small>{hint}</small>}
        </button>
      ))}
    </div>
  )
}

function Letter({ hospital, size, income, pct }: { hospital: string; size: number; income: number; pct: number }) {
  const [v, setV] = useState({ name: '', account: '', dates: '', phone: '' })
  const [copied, setCopied] = useState(false)
  const or = (x: string, p: string) => x.trim() || p
  const text = [
    or(v.name, '[Your name]'), new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' }), '',
    `To: Financial Assistance, Patient Financial Services, ${hospital}`,
    `Re: Request for financial assistance, account ${or(v.account, '[Account number]')}`, '',
    'Hello,', '',
    `I am requesting financial assistance under your Financial Assistance Policy for my care on ${or(v.dates, '[Dates of care]')}.`
    + ` My household has ${size} ${size === 1 ? 'person' : 'people'} and our yearly income is about ${money(income)}, about`
    + ` ${pct}% of the federal poverty guideline.`, '',
    'I am enclosing your application and the documents it asks for. Please tell me if anything else is needed,'
    + ' and please pause any collection activity on this account while my application is reviewed.', '',
    `Thank you. You can reach me at ${or(v.phone, '[Phone or email]')}.`, '', or(v.name, '[Your name]'),
  ].join('\n')
  const copy = async () => {
    try { await navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 2000) } catch {
      (document.getElementById('fa-letter') as HTMLTextAreaElement | null)?.select()
    }
  }
  return (
    <div className="stack">
      <p className="small muted">Fill in your details to finish the letter. They stay on this page and are never sent anywhere.</p>
      <div className="grid2">
        <label className="field">Your name<input value={v.name} onChange={(e) => setV({ ...v, name: e.target.value })} /></label>
        <label className="field">Account number on the bill<input value={v.account} onChange={(e) => setV({ ...v, account: e.target.value })} /></label>
        <label className="field">Dates of care<input value={v.dates} placeholder="e.g. March 3, 2026" onChange={(e) => setV({ ...v, dates: e.target.value })} /></label>
        <label className="field">Phone or email<input value={v.phone} onChange={(e) => setV({ ...v, phone: e.target.value })} /></label>
      </div>
      <textarea id="fa-letter" readOnly value={text} />
      <div><button type="button" onClick={copy}>{copied ? 'Copied' : 'Copy letter'}</button></div>
    </div>
  )
}

function Kit({ r, hospital, size, income, pct }: { r: AssistanceResult; hospital: string; size: number; income: number; pct: number }) {
  return (
    <section className="card stack">
      <h2>How to apply</h2>
      <ol className="steps">
        <li>
          <b>Get the hospital’s application.</b>{' '}
          {r.application_url
            ? <a href={r.application_url} target="_blank" rel="noreferrer">Open {r.system}’s form or page</a>
            : 'Ask the billing office for the financial assistance application.'}
        </li>
        {r.documents.length > 0 && (
          <li><b>Gather these documents:</b>
            <ul className="checklist">{r.documents.map((x) => <li key={x}><label className="check"><input type="checkbox" /> {x}</label></li>)}</ul>
          </li>
        )}
        <li><b>Send it.</b> {r.send_to || r.how_to_apply}{r.phone && <> Phone: <span className="mono">{r.phone}</span>.</>}</li>
        <li><b>Timing.</b> {r.window}{r.nonprofit_501r && ' Federal rules give you at least 240 days after the first bill to apply.'}</li>
        <li><b>Don’t let it go to collections.</b> Under federal rules for nonprofit hospitals, once you send a complete
          application the hospital must pause collection actions (credit reporting, lawsuits, selling the debt) until it
          decides, and refund what you overpaid if you qualify. <a href="https://www.irs.gov/charities-non-profits/billing-and-collections-section-501r6" target="_blank" rel="noreferrer">IRS rule</a></li>
      </ol>
      <details>
        <summary>A letter to send with your application</summary>
        <div style={{ marginTop: 12 }}><Letter hospital={hospital} size={size} income={income} pct={pct} /></div>
      </details>
    </section>
  )
}

export default function Assistance() {
  const [hospitals, setHospitals] = useState<Hospital[]>([])
  const [step, setStep] = useState(0)
  const [ccn, setCcn] = useState('')
  const [size, setSize] = useState(1)
  const [income, setIncome] = useState('')
  const [monthly, setMonthly] = useState(false)
  const [res, setRes] = useState<AssistanceResponse | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => { api.hospitals().then(setHospitals).catch(() => setHospitals([])) }, [])
  const byMetro = useMemo(() => {
    const g: Record<string, Hospital[]> = {}
    hospitals.forEach((h) => { (g[h.metro] ??= []).push(h) })
    return g
  }, [hospitals])
  const hosp = hospitals.find((h) => h.ccn === ccn)
  const yearly = Number(income || 0) * (monthly ? 12 : 1)

  const go = async (coverage: 'insured' | 'self_pay') => {
    setError(''); setBusy(true)
    try { setRes(await api.assistance(size, yearly, coverage, hosp?.health_system)); setStep(3) } catch (e) {
      setError((e as Error).message)
    } finally { setBusy(false) }
  }
  const mine = res?.results.find((r) => hosp && r.registry_systems.includes(hosp.health_system))
  const others = res?.results.filter((r) => r !== mine) ?? []

  return (
    <div className="stack-lg wizard">
      {step < 3 && <div className="progress">{[0, 1, 2].map((i) => <span key={i} className={i <= step ? 'on' : ''} />)}</div>}

      {step === 0 && (
        <section className="stack">
          <h1>Which hospital sent the bill?</h1>
          <p className="muted">Nonprofit hospitals must offer free or discounted care to people who qualify, often even
            with insurance. We’ll show what this hospital’s own policy says.</p>
          <label className="field big">Hospital
            <select value={ccn} onChange={(e) => setCcn(e.target.value)}>
              <option value="">Choose a hospital</option>
              {Object.entries(byMetro).map(([m, hs]) => (
                <optgroup key={m} label={m}>{hs.map((h) => <option key={h.ccn} value={h.ccn}>{h.name} ({h.city})</option>)}</optgroup>
              ))}
              <option value="other">Another hospital</option>
            </select>
          </label>
          <div><button type="button" disabled={!ccn} onClick={() => setStep(1)}>Continue</button></div>
        </section>
      )}

      {step === 1 && (
        <section className="stack">
          <h1>How many people are in your household?</h1>
          <p className="muted">Count yourself, your spouse or partner, and anyone you claim as a dependent.</p>
          <div className="stepper">
            <button type="button" className="secondary" aria-label="Fewer" onClick={() => setSize((s) => Math.max(1, s - 1))}>−</button>
            <span className="big-number" aria-live="polite">{size}</span>
            <button type="button" className="secondary" aria-label="More" onClick={() => setSize((s) => Math.min(20, s + 1))}>+</button>
          </div>
          <div><button type="button" onClick={() => setStep(2)}>Continue</button></div>
        </section>
      )}

      {step === 2 && (
        <section className="stack">
          <h1>What is your household income before taxes?</h1>
          <div className="seg">
            <button type="button" aria-pressed={!monthly} onClick={() => setMonthly(false)}>Per year</button>
            <button type="button" aria-pressed={monthly} onClick={() => setMonthly(true)}>Per month</button>
          </div>
          <label className="field big">{monthly ? 'Monthly' : 'Yearly'} income
            <span className="dollar"><span aria-hidden="true">$</span>
              <input type="number" inputMode="decimal" min="0" placeholder="0" autoFocus value={income} onChange={(e) => setIncome(e.target.value)} />
            </span>
          </label>
          <h2>Did insurance pay part of this bill?</h2>
          <Choice onPick={(v) => go(v === 'yes' ? 'insured' : 'self_pay')} options={[
            ['yes', 'Yes', 'I owe the part insurance did not pay'],
            ['no', 'No', 'I have no insurance or did not use it'],
          ]} />
          {busy && <p className="muted">Checking…</p>}
          {error && <p className="error-box" role="alert">{error}</p>}
        </section>
      )}

      {step > 0 && step < 3 && <div><button type="button" className="ghost" onClick={() => setStep((s) => s - 1)}>← Back</button></div>}

      {step === 3 && res && (
        <div className="stack-lg">
          {mine ? (
            <section className={`verdict ${mine.status === 'free' ? 'looks_right' : mine.status === 'discount' ? 'info' : 'questions'}`}>
              <p className="small muted">{hosp?.name}</p>
              <h1>{HEADLINE[mine.status]}</h1>
              <p className="lead">{mine.result}</p>
              <p className="small muted">Your income is {res.fpl_percent}% of the {res.guidelines.year} federal poverty guideline
                for {size} {size === 1 ? 'person' : 'people'}. The hospital makes the final decision.</p>
            </section>
          ) : (
            <section className="verdict questions">
              <h1>We don’t have this hospital’s policy yet</h1>
              <p className="lead">If it is a nonprofit hospital, federal law requires it to publish a financial assistance
                policy and a plain language summary. Search “{hosp?.name ?? 'hospital name'} financial assistance policy”
                or call the billing number on your bill and ask for the application.</p>
              <p className="small muted">Your income is {res.fpl_percent}% of the federal poverty guideline. At 200% or
                less, most Arizona nonprofit hospitals we checked give free care.</p>
            </section>
          )}
          {mine && mine.notes && <p className="action">{mine.notes}</p>}
          {mine && <Kit r={mine} hospital={hosp?.name ?? mine.system} size={size} income={yearly} pct={res.fpl_percent} />}
          <details className="card">
            <summary>Compare other Arizona hospital systems ({others.length})</summary>
            <div className="stack" style={{ marginTop: 12 }}>
              {others.map((r) => (
                <div key={r.system} className="row" style={{ justifyContent: 'space-between', borderBottom: '1px solid var(--rule)', paddingBottom: 8 }}>
                  <span><b>{r.system}</b><br /><span className="small muted">{r.result}</span></span>
                  <span className={`badge ${r.status}`}>{r.status === 'free' ? 'Free care' : r.status === 'discount' ? 'Discount' : r.status === 'above' ? 'Above limit' : 'Ask'}</span>
                </div>
              ))}
            </div>
          </details>
          <p className="small muted">{res.note} Sources: each hospital’s published policy; <a href={res.guidelines.source_url} target="_blank" rel="noreferrer">HHS poverty guidelines</a>.</p>
          <div className="row">
            <a className="button-link" href="#/bill">Also check whether the bill is right →</a>
            <button type="button" className="ghost" onClick={() => { setStep(0); setRes(null) }}>Start over</button>
          </div>
        </div>
      )}
    </div>
  )
}
