import { useEffect, useState } from 'react'
import { api, money, reader, shrinkPhoto } from '../api'
import type { CheckRequest, CheckResult } from '../api'
import DetailedCheck from './DetailedCheck'
import Results from './Results'

// A guided check: one question per screen, three numbers at most. The detailed form stays available for people
// who want line-by-line checks.
type Docs = 'bill' | 'both' | 'eob'
interface Answers {
  docs?: Docs
  insured?: boolean
  billDue?: number | null
  eobOwe?: number | null
  paid?: number | null
  gfe?: number | null
  emergency?: boolean
  ambulance?: 'none' | 'ground' | 'air'
  network?: 'in' | 'out' | 'unknown'
}

const num = (v: string) => (v.trim() === '' ? null : Number(v))

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

function Amount({ label, hint, value, onChange, autoFocus }: {
  label: string; hint?: string; value: number | null | undefined; onChange: (v: number | null) => void; autoFocus?: boolean
}) {
  return (
    <label className="field big">{label}{hint && <small>{hint}</small>}
      <span className="dollar"><span aria-hidden="true">$</span>
        <input type="number" inputMode="decimal" min="0" step="0.01" placeholder="0.00" autoFocus={autoFocus}
          value={value ?? ''} onChange={(e) => onChange(num(e.target.value))} />
      </span>
    </label>
  )
}

export default function BillCheck() {
  const [a, setA] = useState<Answers>({})
  const [step, setStep] = useState(0)
  const [result, setResult] = useState<CheckResult | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [detailed, setDetailed] = useState(false)
  const [canRead, setCanRead] = useState(false)
  const [consent, setConsent] = useState(false)
  const [reading, setReading] = useState(false)
  const [readNote, setReadNote] = useState('')

  useEffect(() => { reader.status().then(setCanRead) }, [])

  const onPhotos = async (files: FileList | null) => {
    if (!files || files.length === 0) return
    setReading(true); setError(''); setReadNote('')
    try {
      const imgs = await Promise.all([...files].slice(0, 3).map(shrinkPhoto))
      const r = await reader.read(imgs)
      if (r.document_type === 'other') throw new Error("That doesn't look like a medical bill or EOB. Try another photo.")
      const eob = r.you_owe_total != null
      const bill = r.balance_due != null
      setA((x) => ({ ...x, docs: eob && bill ? 'both' : eob ? 'eob' : 'bill', insured: eob ? true : x.insured,
        billDue: r.balance_due, eobOwe: r.you_owe_total, paid: r.patient_payments }))
      setReadNote('We read these numbers from your photo. Please check each one against your paper.'
        + (r.unreadable.length ? ` Could not read: ${r.unreadable.join(', ')}.` : ''))
      setStep(eob ? 2 : 1)
    } catch (e) { setError((e as Error).message) } finally { setReading(false) }
  }

  if (detailed) {
    return (
      <div className="stack-lg">
        <button type="button" className="ghost" onClick={() => setDetailed(false)}>← Back to the quick check</button>
        <DetailedCheck />
      </div>
    )
  }

  const set = (patch: Partial<Answers>) => setA((x) => ({ ...x, ...patch }))
  const next = () => setStep((s) => s + 1)
  const hasEob = a.docs === 'both' || a.docs === 'eob'
  const total = 4

  const run = async () => {
    setBusy(true); setError('')
    const insured = a.insured !== false
    const req: CheckRequest = {
      context: {
        coverage: insured ? 'insured' : 'self_pay', network: a.network ?? 'unknown', emergency: !!a.emergency,
        ambulance: a.ambulance ?? 'none', good_faith_estimate: insured ? null : a.gfe ?? null,
        gfe_received: !insured && a.gfe != null,
      },
      eob: insured && hasEob ? { lines: [], you_owe_total: a.eobOwe ?? null } : null,
      bill: a.docs === 'eob' ? null : {
        provider_type: a.ambulance && a.ambulance !== 'none' ? 'ambulance' : 'unknown', lines: [],
        insurance_paid: 0, adjustments: 0, patient_payments: a.paid ?? 0, balance_due: a.billDue ?? null,
      },
    }
    try { setResult(await api.check(req)); setStep(total) } catch (e) { setError((e as Error).message) } finally { setBusy(false) }
  }

  const restart = () => { setA({}); setStep(0); setResult(null) }

  return (
    <div className="stack-lg wizard">
      {step < total && (
        <div className="progress" aria-label={`Step ${step + 1} of ${total}`}>
          {Array.from({ length: total }, (_, i) => <span key={i} className={i <= step ? 'on' : ''} />)}
        </div>
      )}

      {step === 0 && (
        <section className="stack">
          <h1>What did you get?</h1>
          <p className="muted">An explanation of benefits (EOB) comes from your insurer and says "This is not a bill".
            The bill comes from the hospital or doctor.</p>
          <Choice onPick={(v) => { set({ docs: v as Docs, insured: v === 'bill' ? undefined : true }); next() }} options={[
            ['bill', 'A bill', 'from a hospital, doctor or ambulance'],
            ['both', 'A bill and an EOB', 'the best case: we can compare them'],
            ['eob', 'Only an EOB', 'no bill yet'],
          ]} />
          {canRead && (
            <div className="card stack">
              <h2>Or take a photo</h2>
              <p className="small muted">We send the photo to an AI reading service (Groq) to copy the numbers, then you
                check them. ClearTab does not store the photo. Cover your name and member ID if you can.</p>
              <label className="check"><input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} />
                I agree to send the photo for reading</label>
              <label className={`photo ${consent ? '' : 'disabled'}`}>
                <input type="file" accept="image/*" capture="environment" multiple disabled={!consent || reading}
                  onChange={(e) => onPhotos(e.target.files)} />
                {reading ? 'Reading your photo…' : 'Take or choose a photo (up to 3)'}
              </label>
              {error && <p className="error-box" role="alert">{error}</p>}
            </div>
          )}
        </section>
      )}

      {step === 1 && (
        <section className="stack">
          <h1>{a.docs === 'bill' ? 'Did you use insurance for this care?' : 'A few quick questions'}</h1>
          {a.docs === 'bill' && <Choice onPick={(v) => { set({ insured: v === 'yes' }); if (v === 'no') set({ network: 'unknown' }); next() }} options={[
            ['yes', 'Yes, I have insurance', 'but I have no EOB yet'],
            ['no', 'No', "I'm uninsured or paid myself"],
          ]} />}
          {a.docs !== 'bill' && (
            <>
              <h2>Was it emergency care?</h2>
              <Choice onPick={(v) => { set({ emergency: v === 'yes' }); next() }} options={[['yes', 'Yes, emergency'], ['no', 'No']]} />
            </>
          )}
        </section>
      )}

      {step === 2 && (
        <section className="stack">
          <h1>Enter the amounts</h1>
          {readNote ? <p className="action">{readNote}</p> : <p className="muted">Copy them from your papers. Leave a box empty if you don't have it.</p>}
          {a.docs !== 'eob' && <Amount label="How much does the bill ask you to pay?" hint="often called 'amount due' or 'balance'"
            value={a.billDue} onChange={(v) => set({ billDue: v })} autoFocus />}
          {hasEob && <Amount label="How much does the EOB say you owe?" hint="the last column, often 'what you owe' or 'patient responsibility'"
            value={a.eobOwe} onChange={(v) => set({ eobOwe: v })} autoFocus={a.docs === 'eob'} />}
          {a.docs !== 'eob' && <Amount label="Did you already pay this provider anything?" hint="for example a copay at check-in"
            value={a.paid} onChange={(v) => set({ paid: v })} />}
          {a.insured === false && <Amount label="Did they give you a written estimate before the visit?" hint="a 'good faith estimate'; leave empty if not"
            value={a.gfe} onChange={(v) => set({ gfe: v })} />}
          <div><button type="button" onClick={next}>Continue</button></div>
        </section>
      )}

      {step === 3 && (
        <section className="stack">
          <h1>Last question</h1>
          {a.insured !== false && (
            <>
              <h2>Was this provider in your insurance network?</h2>
              <Choice onPick={(v) => set({ network: v as Answers['network'] })} options={[['in', 'In network'], ['out', 'Out of network'], ['unknown', "I don't know"]]} />
              {a.network && <p className="small muted">Selected: {a.network === 'in' ? 'in network' : a.network === 'out' ? 'out of network' : "don't know"}</p>}
            </>
          )}
          <h2>Was an ambulance involved?</h2>
          <div className="seg">
            {([['none', 'No'], ['ground', 'Ground ambulance'], ['air', 'Air ambulance']] as const).map(([v, l]) => (
              <button key={v} type="button" aria-pressed={(a.ambulance ?? 'none') === v} onClick={() => set({ ambulance: v })}>{l}</button>
            ))}
          </div>
          <div className="row">
            <button type="button" onClick={run} disabled={busy}>{busy ? 'Checking…' : 'Check my bill'}</button>
          </div>
          {error && <p className="error-box" role="alert">{error}</p>}
        </section>
      )}

      {step > 0 && step < total && (
        <div className="row"><button type="button" className="ghost" onClick={() => setStep((s) => s - 1)}>← Back</button></div>
      )}

      {result && step === total && (
        <div className="stack-lg">
          <Results result={result} simple />
          <section className="card stack">
            <h2>Want a deeper check?</h2>
            <p className="muted">Enter each line of the bill and the EOB to find duplicate charges, coding problems and
              prices above what the hospital published.</p>
            <div className="row">
              <button type="button" className="secondary" onClick={() => setDetailed(true)}>Enter the lines</button>
              <button type="button" className="ghost" onClick={restart}>Check another bill</button>
            </div>
          </section>
        </div>
      )}

      {step === 0 && (
        <p className="small muted">Prefer to see an example first? <button type="button" className="link" onClick={() => setDetailed(true)}>Open the
          detailed check with sample bills</button>. Example: you paid {money(35)} at check-in and the bill still asks for {money(35)}.</p>
      )}
    </div>
  )
}
