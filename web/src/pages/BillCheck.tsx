import { useEffect, useMemo, useState } from 'react'
import { api } from '../api'
import type { BillLine, CheckRequest, CheckResult, DemoCase, EobLine, Hospital } from '../api'
import Results from './Results'

const blankEob = (): EobLine => ({
  description: '', units: 1, copay: 0, deductible: 0, coinsurance: 0, not_covered: 0, status: 'paid', remark: '',
})
const blankBillLine = (): BillLine => ({ description: '', units: 1, amount: 0 })

const emptyRequest = (): CheckRequest => ({
  context: { coverage: 'insured', network: 'in', emergency: false, ambulance: 'none', gfe_received: false },
  eob: { claim_number: '', lines: [blankEob()] },
  bill: { provider_type: 'unknown', lines: [], insurance_paid: 0, adjustments: 0, patient_payments: 0, balance_due: null },
})

const num = (v: string): number | null => (v.trim() === '' ? null : Number(v))

function Money({ label, value, onChange, hint }: {
  label: string; value: number | null | undefined; onChange: (v: number | null) => void; hint?: string
}) {
  return (
    <label className="field">{label}{hint && <small>{hint}</small>}
      <input inputMode="decimal" type="number" step="0.01" min="0" value={value ?? ''}
        onChange={(e) => onChange(num(e.target.value))} />
    </label>
  )
}

function Seg<T extends string>({ value, options, onChange, label }: {
  value: T; options: [T, string][]; onChange: (v: T) => void; label: string
}) {
  return (
    <div className="field" role="group" aria-label={label}>
      <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{label}</span>
      <div className="seg">
        {options.map(([v, l]) => (
          <button type="button" key={v} aria-pressed={value === v} onClick={() => onChange(v)}>{l}</button>
        ))}
      </div>
    </div>
  )
}

export default function BillCheck() {
  const [req, setReq] = useState<CheckRequest>(emptyRequest)
  const [cases, setCases] = useState<DemoCase[]>([])
  const [hospitals, setHospitals] = useState<Hospital[]>([])
  const [plans, setPlans] = useState<string[]>([])
  const [result, setResult] = useState<CheckResult | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [story, setStory] = useState('')

  useEffect(() => {
    api.cases().then(setCases).catch(() => setCases([]))
    api.hospitals().then(setHospitals).catch(() => setHospitals([]))
    api.plans().then(setPlans).catch(() => setPlans([]))
  }, [])

  const ctx = req.context
  const selfPay = ctx.coverage === 'self_pay'
  const setCtx = (patch: Partial<CheckRequest['context']>) => setReq((r) => ({ ...r, context: { ...r.context, ...patch } }))
  const eobLines = req.eob?.lines ?? []
  const bill = req.bill!
  const setEobLine = (i: number, patch: Partial<EobLine>) => setReq((r) => ({
    ...r, eob: { ...r.eob!, lines: r.eob!.lines.map((l, j) => (j === i ? { ...l, ...patch } : l)) },
  }))
  const setBill = (patch: Partial<NonNullable<CheckRequest['bill']>>) => setReq((r) => ({ ...r, bill: { ...r.bill!, ...patch } }))
  const setBillLine = (i: number, patch: Partial<BillLine>) => setBill({ lines: bill.lines.map((l, j) => (j === i ? { ...l, ...patch } : l)) })

  const withPrices = useMemo(() => hospitals.filter((h) => h.has_prices), [hospitals])

  const loadCase = (id: string) => {
    const c = cases.find((x) => x.id === id)
    if (!c) return
    const base = emptyRequest()
    setReq({
      context: { ...base.context, ...c.request.context },
      eob: c.request.eob ? { ...c.request.eob, lines: c.request.eob.lines.map((l) => ({ ...blankEob(), ...l })) } : { claim_number: '', lines: [] },
      bill: c.request.bill ? { ...base.bill!, ...c.request.bill, lines: (c.request.bill.lines ?? []).map((l) => ({ ...blankBillLine(), ...l })) } : base.bill,
    })
    setStory(c.story)
    setResult(null)
  }

  const submit = async () => {
    setBusy(true); setError('')
    const clean: CheckRequest = {
      context: { ...ctx, hospital_ccn: ctx.hospital_ccn || null, insurer: ctx.insurer || null },
      eob: selfPay || eobLines.length === 0 ? null : { ...req.eob!, lines: eobLines.map((l) => ({ ...l, code: l.code || null, service_date: l.service_date || null })) },
      bill: { ...bill, statement_date: bill.statement_date || null, lines: bill.lines.map((l) => ({ ...l, code: l.code || null, service_date: l.service_date || null })) },
    }
    try {
      setResult(await api.check(clean))
      setTimeout(() => document.getElementById('results')?.scrollIntoView({ behavior: 'smooth' }), 50)
    } catch (e) {
      setError((e as Error).message)
    } finally { setBusy(false) }
  }

  return (
    <div className="stack-lg">
      <section className="hero">
        <h1>Check a medical bill</h1>
        <p>Copy the numbers from your explanation of benefits (EOB) and your bill. You don't need to fill everything:
          the more you enter, the more we can check. Nothing is stored.</p>
      </section>

      {cases.length > 0 && (
        <section className="card stack">
          <h2>Try an example</h2>
          <p className="small muted">Made-up patients. Prices in the hospital examples come from the hospitals' own published files.</p>
          <div className="row">
            {cases.map((c) => <button key={c.id} className="secondary" type="button" onClick={() => loadCase(c.id)}>{c.title}</button>)}
          </div>
          {story && <p className="action">{story}</p>}
        </section>
      )}

      <fieldset>
        <legend>1. Your situation</legend>
        <div className="row">
          <Seg label="How did you pay?" value={ctx.coverage}
            options={[['insured', 'With insurance'], ['self_pay', 'No insurance / paid myself']]}
            onChange={(v) => setCtx({ coverage: v })} />
          {!selfPay && <Seg label="Was the provider in your network?" value={ctx.network}
            options={[['in', 'In network'], ['out', 'Out of network'], ['unknown', "Don't know"]]}
            onChange={(v) => setCtx({ network: v })} />}
        </div>
        <div className="grid2">
          <label className="field">Hospital <small>to compare with its published prices</small>
            <select value={ctx.hospital_ccn ?? ''} onChange={(e) => setCtx({ hospital_ccn: e.target.value || null })}>
              <option value="">Not listed / not a hospital</option>
              {withPrices.map((h) => <option key={h.ccn} value={h.ccn}>{h.name} ({h.city})</option>)}
            </select>
          </label>
          {!selfPay && <label className="field">Insurance company
            <select value={ctx.insurer ?? ''} onChange={(e) => setCtx({ insurer: e.target.value || null })}>
              <option value="">Not listed</option>
              {plans.map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
          </label>}
          <Seg label="Ambulance?" value={ctx.ambulance}
            options={[['none', 'No'], ['ground', 'Ground'], ['air', 'Air']]} onChange={(v) => setCtx({ ambulance: v })} />
        </div>
        <label className="check"><input type="checkbox" checked={ctx.emergency} onChange={(e) => setCtx({ emergency: e.target.checked })} />
          This was emergency care</label>
        {selfPay && <div className="grid2">
          <Money label="Good faith estimate total" hint="if the provider gave you one" value={ctx.good_faith_estimate}
            onChange={(v) => setCtx({ good_faith_estimate: v, gfe_received: v != null })} />
        </div>}
      </fieldset>

      {!selfPay && (
        <fieldset>
          <legend>2. Explanation of benefits (from your insurer)</legend>
          <p className="small muted">One block per line on the EOB. "Allowed" is the amount your insurer agreed to pay
            the provider in total; "you owe" is usually the last column.</p>
          <label className="field" style={{ maxWidth: 280 }}>Claim number
            <input value={req.eob?.claim_number ?? ''} onChange={(e) => setReq((r) => ({ ...r, eob: { ...r.eob!, claim_number: e.target.value } }))} />
          </label>
          {eobLines.map((l, i) => (
            <div className="line-card" key={i}>
              <div className="line-head"><span>EOB line {i + 1}</span>
                <button type="button" className="ghost" onClick={() => setReq((r) => ({ ...r, eob: { ...r.eob!, lines: r.eob!.lines.filter((_, j) => j !== i) } }))}>Remove</button>
              </div>
              <div className="grid-lines">
                <label className="field">Date<input type="date" value={l.service_date ?? ''} onChange={(e) => setEobLine(i, { service_date: e.target.value })} /></label>
                <label className="field">Code<input value={l.code ?? ''} maxLength={8} placeholder="e.g. 73721" onChange={(e) => setEobLine(i, { code: e.target.value.toUpperCase() })} /></label>
                <label className="field">Description<input value={l.description} onChange={(e) => setEobLine(i, { description: e.target.value })} /></label>
                <Money label="Charged" value={l.billed} onChange={(v) => setEobLine(i, { billed: v })} />
                <Money label="Allowed" value={l.allowed} onChange={(v) => setEobLine(i, { allowed: v })} />
                <Money label="Copay" value={l.copay} onChange={(v) => setEobLine(i, { copay: v ?? 0 })} />
                <Money label="Deductible" value={l.deductible} onChange={(v) => setEobLine(i, { deductible: v ?? 0 })} />
                <Money label="Coinsurance" value={l.coinsurance} onChange={(v) => setEobLine(i, { coinsurance: v ?? 0 })} />
                <Money label="Not covered" value={l.not_covered} onChange={(v) => setEobLine(i, { not_covered: v ?? 0 })} />
                <Money label="Plan paid" value={l.plan_paid} onChange={(v) => setEobLine(i, { plan_paid: v })} />
                <Money label="You owe" value={l.you_owe} onChange={(v) => setEobLine(i, { you_owe: v })} />
                <label className="field">Status
                  <select value={l.status} onChange={(e) => setEobLine(i, { status: e.target.value as EobLine['status'] })}>
                    <option value="paid">Paid</option><option value="denied">Denied</option>
                    <option value="pending">Pending</option><option value="unknown">Not shown</option>
                  </select>
                </label>
              </div>
            </div>
          ))}
          <div><button type="button" className="secondary" onClick={() => setReq((r) => ({ ...r, eob: { ...r.eob!, lines: [...r.eob!.lines, blankEob()] } }))}>+ Add EOB line</button></div>
        </fieldset>
      )}

      <fieldset>
        <legend>{selfPay ? '2' : '3'}. The bill (from the hospital or doctor)</legend>
        <div className="row">
          <Seg label="Who sent the bill?" value={bill.provider_type}
            options={[['facility', 'Hospital'], ['professional', 'Doctor or group'], ['ambulance', 'Ambulance'], ['unknown', 'Not sure']]}
            onChange={(v) => setBill({ provider_type: v })} />
        </div>
        <div className="grid2">
          <Money label="Amount due on the bill" value={bill.balance_due} onChange={(v) => setBill({ balance_due: v })} />
          <Money label="What you already paid them" hint="for example a copay at check-in" value={bill.patient_payments} onChange={(v) => setBill({ patient_payments: v ?? 0 })} />
          <label className="field">Statement date<input type="date" value={bill.statement_date ?? ''} onChange={(e) => setBill({ statement_date: e.target.value })} /></label>
        </div>
        <p className="small muted">Itemized lines (optional, but needed for duplicate, coding and price checks):</p>
        {bill.lines.map((l, i) => (
          <div className="line-card" key={i}>
            <div className="line-head"><span>Bill line {i + 1}</span>
              <button type="button" className="ghost" onClick={() => setBill({ lines: bill.lines.filter((_, j) => j !== i) })}>Remove</button>
            </div>
            <div className="grid-lines">
              <label className="field">Date<input type="date" value={l.service_date ?? ''} onChange={(e) => setBillLine(i, { service_date: e.target.value })} /></label>
              <label className="field">Code<input value={l.code ?? ''} maxLength={8} onChange={(e) => setBillLine(i, { code: e.target.value.toUpperCase() })} /></label>
              <label className="field">Description<input value={l.description} onChange={(e) => setBillLine(i, { description: e.target.value })} /></label>
              <label className="field">Units<input type="number" min="1" value={l.units} onChange={(e) => setBillLine(i, { units: Number(e.target.value) || 1 })} /></label>
              <Money label="Amount" value={l.amount} onChange={(v) => setBillLine(i, { amount: v ?? 0 })} />
            </div>
          </div>
        ))}
        <div><button type="button" className="secondary" onClick={() => setBill({ lines: [...bill.lines, blankBillLine()] })}>+ Add bill line</button></div>
      </fieldset>

      <div className="row">
        <button type="button" onClick={submit} disabled={busy}>{busy ? 'Checking…' : 'Check my bill'}</button>
        <button type="button" className="ghost" onClick={() => { setReq(emptyRequest()); setResult(null); setStory('') }}>Start over</button>
      </div>
      {error && <p className="error-box" role="alert">{error}</p>}
      {result && <div id="results"><Results result={result} /></div>}
    </div>
  )
}
