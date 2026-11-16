import { useState } from 'react'
import { api } from '../api'
import type { CollectionItem, CollectionResponse } from '../api'
import { useLang, useT } from '../i18n'

// "I got a collection letter": who sent it, a few dates and numbers from the letter -> rights and next steps under
// federal and Arizona rules, and a dispute letter. The answers go to the API for one response and are never logged
// or stored; the letter's personal details stay in this browser tab.
const LEVEL: Record<CollectionItem['level'], string> = { urgent: 'error', warning: 'warning', info: 'info', ok: 'ok' }

function fmt(iso: string | null, lang: string) {
  if (!iso) return ''
  const [y, m, d] = iso.split('-').map(Number)
  return new Date(y, m - 1, d).toLocaleDateString(lang === 'es' ? 'es-US' : 'en-US', { year: 'numeric', month: 'long', day: 'numeric' })
}

function Letter({ template }: { template: string }) {
  const t = useT()
  const { lang } = useLang()
  const [v, setV] = useState({ name: '', address: '', agency: '', account: '', creditor: '', amount: '' })
  const [copied, setCopied] = useState(false)
  const fill: [string, keyof typeof v][] = [
    ['[Your name]', 'name'], ['[Your address]', 'address'], ['[Collection agency name and address]', 'agency'],
    ['[account number]', 'account'], ['[hospital or provider]', 'creditor'], ['[amount]', 'amount'],
  ]
  let text = template.replace('[Date]', new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' }))
  for (const [ph, k] of fill) if (v[k].trim()) text = text.split(ph).join(v[k].trim())
  const field = (k: keyof typeof v, label: string) => (
    <label className="field">{t(label)}<input value={v[k]} onChange={(e) => setV({ ...v, [k]: e.target.value })} /></label>
  )
  const copy = async () => {
    try { await navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 2000) } catch {
      (document.getElementById('collector-letter') as HTMLTextAreaElement | null)?.select()
    }
  }
  return (
    <div className="stack">
      <p className="small muted">{t('Fill in your details to finish the letter. They stay on this page and are never sent anywhere.')}</p>
      {lang === 'es' && <p className="action">La carta está en inglés porque va dirigida a la agencia de cobranza.</p>}
      <div className="grid2">
        {field('name', 'Your name')}{field('address', 'Your address')}
        {field('agency', 'Collection agency name and address')}{field('account', 'Account number on the letter')}
        {field('creditor', 'Original hospital or provider')}{field('amount', 'Amount they say you owe')}
      </div>
      <textarea id="collector-letter" readOnly value={text} />
      <div><button type="button" onClick={copy}>{copied ? t('Copied') : t('Copy letter')}</button></div>
    </div>
  )
}

export default function Collections() {
  const t = useT()
  const { lang } = useLang()
  const [step, setStep] = useState(0)
  const [sender, setSender] = useState('collector')
  const [v, setV] = useState({ first: '', service: '', rate: '', amount: '' })
  const [nonprofit, setNonprofit] = useState('unknown')
  const [insured, setInsured] = useState('unknown')
  const [res, setRes] = useState<CollectionResponse | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const num = (s: string) => (s.trim() === '' ? null : Number(s))

  const go = async () => {
    setError(''); setBusy(true)
    try {
      setRes(await api.collections({
        sender, first_notice: v.first || null, service_date: v.service || null, interest_rate: num(v.rate),
        amount: num(v.amount), nonprofit, insured,
      }))
      setStep(3)
    } catch (e) { setError((e as Error).message) } finally { setBusy(false) }
  }
  const choice = (opts: [string, string, string?][], pick: (x: string) => void) => (
    <div className="choices">
      {opts.map(([val, label, hint]) => (
        <button key={val} type="button" className="choice" onClick={() => pick(val)}>
          <span>{t(label)}</span>{hint && <small>{t(hint)}</small>}
        </button>
      ))}
    </div>
  )
  const yn = (val: string, set: (x: string) => void, label: string) => (
    <fieldset className="stack">
      <legend><b>{t(label)}</b></legend>
      <div className="seg">
        {[['yes', 'Yes'], ['no', 'No'], ['unknown', 'Not sure']].map(([k, l]) => (
          <button key={k} type="button" aria-pressed={val === k} onClick={() => set(k)}>{t(l)}</button>
        ))}
      </div>
    </fieldset>
  )

  return (
    <div className="stack-lg wizard">
      {step < 3 && <div className="progress">{[0, 1, 2].map((i) => <span key={i} className={i <= step ? 'on' : ''} />)}</div>}

      {step === 0 && (
        <section className="stack">
          <h1>{t('Who is asking you to pay?')}</h1>
          <p className="muted">{t('Look at the top of the letter. A medical bill in collections still has rules, and you have rights.')}</p>
          {choice([
            ['collector', 'A collection agency', 'A company that is not the hospital or doctor'],
            ['hospital', 'The hospital or doctor’s office', 'An overdue or final notice from the provider itself'],
            ['court', 'Court papers or a lawyer', 'A summons, complaint or a letter from a law firm'],
          ], (x) => { setSender(x); setStep(1) })}
        </section>
      )}

      {step === 1 && (
        <section className="stack">
          <h1>{t('A few details from the letter')}</h1>
          <p className="muted">{t('All optional. Leave out anything you don’t have.')}</p>
          <div className="grid2">
            {sender !== 'hospital' && (
              <label className="field">{t('When did you get the collector’s first letter?')}
                <input type="date" value={v.first} onChange={(e) => setV({ ...v, first: e.target.value })} /></label>
            )}
            <label className="field">{t('Date of the medical care')}
              <input type="date" value={v.service} onChange={(e) => setV({ ...v, service: e.target.value })} /></label>
            <label className="field">{t('Amount they say you owe')}
              <span className="dollar"><span aria-hidden="true">$</span>
                <input type="number" inputMode="decimal" min="0" value={v.amount} onChange={(e) => setV({ ...v, amount: e.target.value })} /></span></label>
            <label className="field">{t('Interest rate on the letter (% per year)')}
              <input type="number" inputMode="decimal" min="0" max="100" step="0.1" value={v.rate} onChange={(e) => setV({ ...v, rate: e.target.value })} /></label>
          </div>
          <div><button type="button" onClick={() => setStep(2)}>{t('Continue')}</button></div>
        </section>
      )}

      {step === 2 && (
        <section className="stack">
          <h1>{t('About the original bill')}</h1>
          {yn(nonprofit, setNonprofit, 'Was it from a nonprofit hospital? (Many Arizona hospitals are, for example Banner, HonorHealth, Dignity Health and Tucson Medical Center.)')}
          {yn(insured, setInsured, 'Did you have health insurance when you got the care?')}
          <div><button type="button" disabled={busy} onClick={go}>{t('Show my rights and next steps')}</button></div>
          {busy && <p className="muted">{t('Checking…')}</p>}
          {error && <p className="error-box" role="alert">{error}</p>}
        </section>
      )}

      {step > 0 && step < 3 && <div><button type="button" className="ghost" onClick={() => setStep((s) => s - 1)}>{t('← Back')}</button></div>}

      {step === 3 && res && (
        <div className="stack-lg">
          <section className={`verdict ${res.items[0]?.level === 'urgent' ? 'questions' : 'info'}`}>
            <p className="small muted">{t('Medical debt in collections')}</p>
            <h1>{t(res.items[0]?.level === 'urgent' ? 'Act on the court papers first' : 'Don’t pay yet. Check it first.')}</h1>
            <p className="lead">{t('Medical debts in collections can be wrong or too high, and you have rights that pause collection while you check.')}</p>
          </section>
          {res.items.map((it) => (
            <section key={it.key} className={`card stack finding ${LEVEL[it.level]}`}>
              <h2>{t(it.title)}{it.date && <>: {t('by')} {fmt(it.date, lang)}</>}</h2>
              <p>{t(it.text)}</p>
              {it.action && <p className="action">{t(it.action)}</p>}
            </section>
          ))}
          <details className="card">
            <summary>{t('Letter to the collector')}</summary>
            <div style={{ marginTop: 12 }}><Letter template={res.letter} /></div>
          </details>
          <p className="small muted">{t('Sources:')} {res.sources.map((s, i) => (
            <span key={s.url}>{i > 0 && '; '}<a href={s.url} target="_blank" rel="noreferrer">{s.title}</a></span>
          ))}. {t('This is general information, not legal advice. You send every letter yourself.')}</p>
          <div className="row">
            <a className="button-link" href="#/help">{t('See if the hospital must lower or forgive it →')}</a>
            <button type="button" className="ghost" onClick={() => { setStep(0); setRes(null) }}>{t('Start over')}</button>
          </div>
        </div>
      )}
    </div>
  )
}
