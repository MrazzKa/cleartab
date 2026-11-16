import { useEffect, useState } from 'react'
import { api } from '../api'
import type { DenialReason, DenialResponse } from '../api'
import { useLang, useT } from '../i18n'

// "My insurer said no": the printed reason (or a reason picked by hand), the plan type and the notice date ->
// what the denial means, the first thing to do, deadlines, an appeal letter and a call script. The text goes to the
// API for one answer and is never logged or stored; the letter's personal details stay in this browser tab.
const PLANS: [string, string, string][] = [
  ['job', 'Through a job', 'Mine or a family member’s employer'],
  ['marketplace', 'HealthCare.gov / Marketplace', 'A plan I bought myself'],
  ['student', 'Student health plan', 'For example the UA student plan'],
  ['ahcccs', 'AHCCCS (Arizona Medicaid)', 'Including Mercy Care, Banner University Family Care and others'],
  ['medicare', 'Medicare', 'Original Medicare or a Medicare Advantage plan'],
  ['unknown', 'I’m not sure', ''],
]

function fmt(iso: string | null, lang: string) {
  if (!iso) return ''
  const [y, m, d] = iso.split('-').map(Number)
  return new Date(y, m - 1, d).toLocaleDateString(lang === 'es' ? 'es-US' : 'en-US', { year: 'numeric', month: 'long', day: 'numeric' })
}

function Letter({ template }: { template: string }) {
  const t = useT()
  const { lang } = useLang()
  const [v, setV] = useState({ name: '', plan: '', member: '', claim: '', date: '', provider: '', reason: '', contact: '' })
  const [copied, setCopied] = useState(false)
  const fill: [string, keyof typeof v][] = [
    ['[Your name]', 'name'], ['[Health plan name]', 'plan'], ['[AHCCCS health plan name]', 'plan'], ['[member ID]', 'member'],
    ['[claim number]', 'claim'], ['[date]', 'date'], ['[provider name]', 'provider'],
    ['[reason printed on the EOB or letter]', 'reason'], ['[Phone or email]', 'contact'],
  ]
  let text = template.replace('[Date]', new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' }))
  for (const [ph, k] of fill) if (v[k].trim()) text = text.split(ph).join(v[k].trim())
  const field = (k: keyof typeof v, label: string) => (
    <label className="field">{t(label)}<input value={v[k]} onChange={(e) => setV({ ...v, [k]: e.target.value })} /></label>
  )
  const copy = async () => {
    try { await navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 2000) } catch {
      (document.getElementById('appeal-letter') as HTMLTextAreaElement | null)?.select()
    }
  }
  return (
    <div className="stack">
      <p className="small muted">{t('Fill in your details to finish the letter. They stay on this page and are never sent anywhere.')}</p>
      {lang === 'es' && <p className="action">La carta está en inglés porque va dirigida a su aseguradora.</p>}
      <div className="grid2">
        {field('name', 'Your name')}{field('plan', 'Health plan name')}
        {field('member', 'Member ID (on your insurance card)')}{field('claim', 'Claim number (on the EOB)')}
        {field('date', 'Date of service')}{field('provider', 'Provider (doctor or hospital)')}
        {field('reason', 'Reason printed on the EOB or letter')}{field('contact', 'Phone or email')}
      </div>
      <textarea id="appeal-letter" readOnly value={text} />
      <div><button type="button" onClick={copy}>{copied ? t('Copied') : t('Copy letter')}</button></div>
    </div>
  )
}

function ReasonCard({ r, main }: { r: DenialReason; main: boolean }) {
  const t = useT()
  return (
    <section className={main ? 'card stack' : 'stack'}>
      {!main && <h2>{t(r.title)}</h2>}
      <p>{t(r.means)}</p>
      <p className="action"><b>{t(r.appeal_first ? 'First step:' : 'Fastest fix (usually no appeal needed):')}</b> {t(r.first_step)}</p>
      <ul>{r.steps.map((s) => <li key={s}>{t(s)}</li>)}</ul>
    </section>
  )
}

export default function Denied() {
  const t = useT()
  const { lang } = useLang()
  const [step, setStep] = useState(0)
  const [text, setText] = useState('')
  const [reason, setReason] = useState<string | null>(null)
  const [all, setAll] = useState<DenialReason[]>([])
  const [plan, setPlan] = useState('unknown')
  const [notice, setNotice] = useState('')
  const [emergency, setEmergency] = useState(false)
  const [res, setRes] = useState<DenialResponse | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => { api.denialReasons().then(setAll).catch(() => setAll([])) }, [])

  const go = async () => {
    setError(''); setBusy(true)
    try {
      setRes(await api.denial({ text, reason, plan, notice_date: notice || null, emergency }))
      setStep(3)
    } catch (e) { setError((e as Error).message) } finally { setBusy(false) }
  }

  return (
    <div className="stack-lg wizard">
      {step < 3 && <div className="progress">{[0, 1, 2].map((i) => <span key={i} className={i <= step ? 'on' : ''} />)}</div>}

      {step === 0 && (
        <section className="stack">
          <h1>{t('What did your insurer say?')}</h1>
          <p className="muted">{t('Copy the reason printed on your Explanation of Benefits (EOB) or denial letter, with any code like CO-197. Or pick the closest reason below.')}</p>
          <label className="field big">{t('Reason on the EOB or letter')}
            <textarea rows={3} maxLength={2000} value={text} placeholder={t('e.g. CO-50: These are non-covered services because this is not deemed a medical necessity')}
              onChange={(e) => { setText(e.target.value); setReason(null) }} />
          </label>
          <details>
            <summary>{t('Or pick the closest reason')}</summary>
            <div className="choices" style={{ marginTop: 12 }}>
              {all.map((r) => (
                <button key={r.key} type="button" className="choice" aria-pressed={reason === r.key}
                  onClick={() => { setReason(r.key); setStep(1) }}>
                  <span>{t(r.title)}</span>
                </button>
              ))}
            </div>
          </details>
          <div><button type="button" disabled={!text.trim() && !reason} onClick={() => setStep(1)}>{t('Continue')}</button></div>
        </section>
      )}

      {step === 1 && (
        <section className="stack">
          <h1>{t('What kind of insurance is it?')}</h1>
          <p className="muted">{t('The appeal rules and deadlines depend on it. It is usually printed on your card.')}</p>
          <div className="choices">
            {PLANS.map(([v, label, hint]) => (
              <button key={v} type="button" className="choice" onClick={() => { setPlan(v); setStep(2) }}>
                <span>{t(label)}</span>{hint && <small>{t(hint)}</small>}
              </button>
            ))}
          </div>
        </section>
      )}

      {step === 2 && (
        <section className="stack">
          <h1>{t('When did you get the denial?')}</h1>
          <p className="muted">{t('Use the date on the EOB or letter. We use it to work out your deadline. You can skip it.')}</p>
          <label className="field big">{t('Date on the notice')}
            <input type="date" value={notice} onChange={(e) => setNotice(e.target.value)} />
          </label>
          <label className="check"><input type="checkbox" checked={emergency} onChange={(e) => setEmergency(e.target.checked)} /> {t('This was emergency care')}</label>
          <div><button type="button" disabled={busy} onClick={go}>{t('Show what to do')}</button></div>
          {busy && <p className="muted">{t('Checking…')}</p>}
          {error && <p className="error-box" role="alert">{error}</p>}
        </section>
      )}

      {step > 0 && step < 3 && <div><button type="button" className="ghost" onClick={() => setStep((s) => s - 1)}>{t('← Back')}</button></div>}

      {step === 3 && res && (
        <div className="stack-lg">
          {res.reasons.length === 0 ? (
            <section className="verdict questions">
              <h1>{t('We could not tell the reason from that text')}</h1>
              <p className="lead">{t('Call your insurer and ask for the reason in plain words, then pick it here. You still have the right to appeal, and the deadlines below still apply.')}</p>
            </section>
          ) : (
            <section className="verdict info">
              <p className="small muted">{t('What the denial means')}</p>
              <h1>{t(res.reasons[0].title)}</h1>
              <p className="lead">{t('A denial is not the final word. People who appeal often win, and many denials are fixed with one phone call.')}</p>
              <p className="small">{t('In Arizona HealthCare.gov plans in 2025, insurers denied 1 in 6 in-network claims. Fewer than 1 in 100 denials were appealed, and 40% of appeals won.')}{' '}
                <a href="https://www.cms.gov/marketplace/resources/data/public-use-files" target="_blank" rel="noreferrer">{t('CMS data')}</a></p>
            </section>
          )}
          {res.reasons[0] && <ReasonCard r={res.reasons[0]} main />}
          {res.emergency_note && (
            <p className="action">{t('Emergency care: your plan may not require prior approval for it, and an out-of-network emergency room must be covered at your in-network cost share (No Surprises Act).')}</p>
          )}

          <section className="card stack">
            <h2>{t('Your deadlines')}</h2>
            <ol className="steps">
              {res.deadlines.map((d) => (
                <li key={d.label}><b>{t(d.label)}{d.date && <>: {fmt(d.date, lang)}</>}</b> {t(d.note)}</li>
              ))}
            </ol>
          </section>

          <section className="card stack">
            <h2>{t('Call first')}</h2>
            <ol className="steps">{res.call_script.map((s) => <li key={s}>{t(s)}</li>)}</ol>
          </section>

          <details className="card">
            <summary>{t('Appeal letter')}</summary>
            <div style={{ marginTop: 12 }}><Letter template={res.letter} /></div>
          </details>

          {res.reasons.length > 1 && (
            <details className="card">
              <summary>{t('Other reasons the text may mean')} ({res.reasons.length - 1})</summary>
              <div className="stack" style={{ marginTop: 12 }}>{res.reasons.slice(1).map((r) => <ReasonCard key={r.key} r={r} main={false} />)}</div>
            </details>
          )}

          <p className="small muted">{t('Sources:')} {res.sources.map((s, i) => (
            <span key={s.url}>{i > 0 && '; '}<a href={s.url} target="_blank" rel="noreferrer">{s.title}</a></span>
          ))}. {t('This is general information, not legal advice. You send every letter yourself.')}</p>
          <div className="row">
            <a className="button-link" href="#/help">{t('Can’t afford what’s left? See hospital financial help →')}</a>
            <button type="button" className="ghost" onClick={() => { setStep(0); setRes(null); setText(''); setReason(null) }}>{t('Start over')}</button>
          </div>
        </div>
      )}
    </div>
  )
}
