import { useEffect, useState } from 'react'
import { ambulanceServices, api, money, reader, shrinkPhoto } from '../api'
import type { AmbulanceService } from '../api'
import type { CheckRequest, CheckResult } from '../api'
import { useLang, useT } from '../i18n'
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
  con?: string
  level?: 'als' | 'bls' | 'unknown'
  miles?: number | null
  transported?: boolean
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
  const t = useT()
  const { lang } = useLang()
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
  const [services, setServices] = useState<AmbulanceService[]>([])
  useEffect(() => { reader.status().then(setCanRead); ambulanceServices().then(setServices) }, [])

  const onPhotos = async (files: FileList | null) => {
    if (!files || files.length === 0) return
    setReading(true); setError(''); setReadNote('')
    try {
      const imgs = await Promise.all([...files].slice(0, 3).map(shrinkPhoto))
      const r = await reader.read(imgs)
      if (r.document_type === 'other') throw new Error(t("That doesn't look like a medical bill or EOB. Try another photo."))
      const eob = r.you_owe_total != null
      const bill = r.balance_due != null
      setA((x) => ({ ...x, docs: eob && bill ? 'both' : eob ? 'eob' : 'bill', insured: eob ? true : x.insured,
        billDue: r.balance_due, eobOwe: r.you_owe_total, paid: r.patient_payments }))
      setReadNote(t('We read these numbers from your photo. Please check each one against your paper.')
        + (r.unreadable.length ? ` ${t('Could not read:')} ${r.unreadable.join(', ')}.` : ''))
      setStep(eob ? 2 : 1)
    } catch (e) { setError((e as Error).message) } finally { setReading(false) }
  }

  if (detailed) {
    return (
      <div className="stack-lg">
        <button type="button" className="ghost" onClick={() => setDetailed(false)}>{t('← Back to the quick check')}</button>
        {lang === 'es' && <p className="action">El formulario detallado está en inglés por ahora.</p>}
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
        ambulance_con: a.ambulance === 'ground' ? a.con || null : null, ambulance_level: a.level ?? 'unknown',
        ambulance_miles: a.miles ?? null, transported: a.ambulance === 'ground' ? a.transported ?? null : null,
        gfe_received: !insured && a.gfe != null, lang,
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
        <div className="progress" aria-label={t('Step {n} of {total}', { n: step + 1, total })}>
          {Array.from({ length: total }, (_, i) => <span key={i} className={i <= step ? 'on' : ''} />)}
        </div>
      )}

      {step === 0 && (
        <section className="stack">
          <h1>{t('What did you get?')}</h1>
          <p className="muted">{t('An explanation of benefits (EOB) comes from your insurer and says "This is not a bill". The bill comes from the hospital or doctor.')}</p>
          <Choice onPick={(v) => { set({ docs: v as Docs, insured: v === 'bill' ? undefined : true }); next() }} options={[
            ['bill', t('A bill'), t('from a hospital, doctor or ambulance')],
            ['both', t('A bill and an EOB'), t('the best case: we can compare them')],
            ['eob', t('Only an EOB'), t('no bill yet')],
          ]} />
          {canRead && (
            <div className="card stack">
              <h2>{t('Or take a photo')}</h2>
              <p className="small muted">{t('We send the photo to an AI reading service (Groq) to copy the numbers, then you check them. ClearTab does not store the photo. Cover your name and member ID if you can.')}</p>
              <label className="check"><input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} />
                {t('I agree to send the photo for reading')}</label>
              <label className={`photo ${consent ? '' : 'disabled'}`}>
                <input type="file" accept="image/*" capture="environment" multiple disabled={!consent || reading}
                  onChange={(e) => onPhotos(e.target.files)} />
                {reading ? t('Reading your photo…') : t('Take or choose a photo (up to 3)')}
              </label>
              {error && <p className="error-box" role="alert">{error}</p>}
            </div>
          )}
        </section>
      )}

      {step === 1 && (
        <section className="stack">
          <h1>{a.docs === 'bill' ? t('Did you use insurance for this care?') : t('A few quick questions')}</h1>
          {a.docs === 'bill' && <Choice onPick={(v) => { set({ insured: v === 'yes' }); if (v === 'no') set({ network: 'unknown' }); next() }} options={[
            ['yes', t('Yes, I have insurance'), t('but I have no EOB yet')],
            ['no', t('No'), t("I'm uninsured or paid myself")],
          ]} />}
          {a.docs !== 'bill' && (
            <>
              <h2>{t('Was it emergency care?')}</h2>
              <Choice onPick={(v) => { set({ emergency: v === 'yes' }); next() }} options={[['yes', t('Yes, emergency')], ['no', t('No')]]} />
            </>
          )}
        </section>
      )}

      {step === 2 && (
        <section className="stack">
          <h1>{t('Enter the amounts')}</h1>
          {readNote ? <p className="action">{readNote}</p> : <p className="muted">{t("Copy them from your papers. Leave a box empty if you don't have it.")}</p>}
          {a.docs !== 'eob' && <Amount label={t('How much does the bill ask you to pay?')} hint={t("often called 'amount due' or 'balance'")}
            value={a.billDue} onChange={(v) => set({ billDue: v })} autoFocus />}
          {hasEob && <Amount label={t('How much does the EOB say you owe?')} hint={t("the last column, often 'what you owe' or 'patient responsibility'")}
            value={a.eobOwe} onChange={(v) => set({ eobOwe: v })} autoFocus={a.docs === 'eob'} />}
          {a.docs !== 'eob' && <Amount label={t('Did you already pay this provider anything?')} hint={t('for example a copay at check-in')}
            value={a.paid} onChange={(v) => set({ paid: v })} />}
          {a.insured === false && <Amount label={t('Did they give you a written estimate before the visit?')} hint={t("a 'good faith estimate'; leave empty if not")}
            value={a.gfe} onChange={(v) => set({ gfe: v })} />}
          <div><button type="button" onClick={next}>{t('Continue')}</button></div>
        </section>
      )}

      {step === 3 && (
        <section className="stack">
          <h1>{t('Last question')}</h1>
          {a.insured !== false && (
            <>
              <h2>{t('Was this provider in your insurance network?')}</h2>
              <Choice onPick={(v) => set({ network: v as Answers['network'] })} options={[['in', t('In network')], ['out', t('Out of network')], ['unknown', t("I don't know")]]} />
              {a.network && <p className="small muted">{t('Selected:')} {a.network === 'in' ? t('In network') : a.network === 'out' ? t('Out of network') : t("I don't know")}</p>}
            </>
          )}
          <h2>{t('Was an ambulance involved?')}</h2>
          <div className="seg">
            {([['none', t('No')], ['ground', t('Ground ambulance')], ['air', t('Air ambulance')]] as const).map(([v, l]) => (
              <button key={v} type="button" aria-pressed={(a.ambulance ?? 'none') === v} onClick={() => set({ ambulance: v })}>{l}</button>
            ))}
          </div>
          {a.ambulance === 'ground' && (
            <div className="card stack">
              <p className="small muted">{t('Arizona sets the most each ambulance service may charge (A.R.S. 36-2239). Tell us which one sent the bill and we’ll compare.')}</p>
              <label className="field">{t('Ambulance service (name on the bill)')}
                <select value={a.con ?? ''} onChange={(e) => set({ con: e.target.value })}>
                  <option value="">{t('Not sure / not listed')}</option>
                  {services.map((x) => <option key={x.con} value={x.con}>{x.entity.includes(' dba ') ? x.entity.split(' dba ').slice(-1)[0] : x.entity}</option>)}
                </select>
              </label>
              <div className="seg" role="group" aria-label={t('Level of care')}>
                {([['als', t('Advanced (ALS)')], ['bls', t('Basic (BLS)')], ['unknown', t("Don't know")]] as const).map(([v, l]) => (
                  <button key={v} type="button" aria-pressed={(a.level ?? 'unknown') === v} onClick={() => set({ level: v })}>{l}</button>
                ))}
              </div>
              <label className="field">{t('Miles driven, if the bill shows them')}
                <input type="number" inputMode="decimal" min="0" value={a.miles ?? ''} onChange={(e) => set({ miles: num(e.target.value) })} />
              </label>
              <div className="seg" role="group" aria-label={t('Were you taken to the hospital?')}>
                <button type="button" aria-pressed={a.transported !== false} onClick={() => set({ transported: true })}>{t('Taken to hospital')}</button>
                <button type="button" aria-pressed={a.transported === false} onClick={() => set({ transported: false })}>{t('Not taken / I refused')}</button>
              </div>
            </div>
          )}
          <div className="row">
            <button type="button" onClick={run} disabled={busy}>{busy ? t('Checking…') : t('Check my bill')}</button>
          </div>
          {error && <p className="error-box" role="alert">{error}</p>}
        </section>
      )}

      {step > 0 && step < total && (
        <div className="row"><button type="button" className="ghost" onClick={() => setStep((s) => s - 1)}>{t('← Back')}</button></div>
      )}

      {result && step === total && (
        <div className="stack-lg">
          <Results result={result} simple />
          <section className="card stack">
            <h2>{t('Want a deeper check?')}</h2>
            <p className="muted">{t('Enter each line of the bill and the EOB to find duplicate charges, coding problems and prices above what the hospital published.')}</p>
            <div className="row">
              <button type="button" className="secondary" onClick={() => setDetailed(true)}>{t('Enter the lines')}</button>
              <button type="button" className="ghost" onClick={restart}>{t('Check another bill')}</button>
            </div>
          </section>
        </div>
      )}

      {step === 0 && (
        <p className="small muted">{t('Prefer to see an example first?')} <button type="button" className="link" onClick={() => setDetailed(true)}>{t('Open the detailed check with sample bills')}</button>. {t('Example: you paid {a} at check-in and the bill still asks for {a}.', { a: money(35) })}</p>
      )}
    </div>
  )
}
