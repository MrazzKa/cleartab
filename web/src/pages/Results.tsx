import { useMemo, useState } from 'react'
import { money } from '../api'
import type { CheckResult, Severity } from '../api'
import { useLang, useT } from '../i18n'

const LABEL: Record<Severity, string> = { error: 'Likely error', warning: 'Ask about this', info: 'Good to know', ok: 'Checked' }
const ICON: Record<Severity, string> = { error: '✕', warning: '!', info: 'i', ok: '✓' }
const CHECK_NAMES: Record<string, string> = {
  eob_arithmetic: 'EOB math', bill_vs_eob: 'Bill against EOB', duplicates: 'Duplicate charges',
  mue_units: 'Medicare unit limits (MUE)', ncci_ptp: 'Code pairs (NCCI)', published_prices: 'Hospital published prices', er_rates: 'Hospital published ER visit rates', plan_balances: 'Deductible and out-of-pocket balances', medicare: 'Medicare price in Arizona', global_period: 'Visits inside a surgery global period',
  no_surprises_act: 'No Surprises Act', paperwork: 'Paperwork', az_ambulance_rate: 'Arizona ambulance rates',
}

// Placeholders the dispute letter uses; values typed here stay in this browser tab.
const FIELDS: [string, string][] = [
  ['[Your name]', 'Your name'], ['[Your address]', 'Your address'], ['[Date]', "Today's date"],
  ['[Account number]', 'Account number on the bill'], ['[Provider name]', 'Provider name'],
  ['[Insurance company]', 'Insurance company'], ['[Date of service]', 'Date of service'],
  ['[Claim number]', 'Claim number'], ['[Phone or email]', 'Phone or email'],
]

function DisputeKit({ letter, script }: { letter: string; script: string[] }) {
  const t = useT()
  const { lang } = useLang()
  const used = FIELDS.filter(([p]) => letter.includes(p))
  const [vals, setVals] = useState<Record<string, string>>({})
  const [copied, setCopied] = useState(false)
  const filled = useMemo(() => used.reduce((t, [p]) => (vals[p] ? t.split(p).join(vals[p]) : t), letter), [letter, used, vals])

  const copy = async () => {
    try { await navigator.clipboard.writeText(filled); setCopied(true); setTimeout(() => setCopied(false), 2000) } catch {
      const el = document.getElementById('letter') as HTMLTextAreaElement | null
      el?.select()
    }
  }

  return (
    <section className="card stack">
      <h2>{t('Your dispute kit')}</h2>
      <p className="small muted">{t('Fill in your details to complete the letter. They stay on this page and are never sent anywhere.')}</p>
      {lang === 'es' && <p className="action">La carta y el guion están en inglés porque van dirigidos a la oficina de facturación en EE. UU.</p>}
      <div className="grid2">
        {used.map(([p, label]) => (
          <label className="field" key={p}>{t(label)}
            <input value={vals[p] ?? ''} onChange={(e) => setVals((v) => ({ ...v, [p]: e.target.value }))} />
          </label>
        ))}
      </div>
      <label className="field">{t('Letter')}
        <textarea id="letter" readOnly value={filled} />
      </label>
      <div className="row"><button type="button" onClick={copy}>{copied ? t('Copied') : t('Copy letter')}</button></div>
      <h3>{t('Phone script')}</h3>
      <ol className="script">{script.map((s, i) => <li key={i}>{s}</li>)}</ol>
    </section>
  )
}

function FindingCard({ f }: { f: CheckResult['findings'][number] }) {
  const t = useT()
  return (
    <article className={`card finding ${f.severity}`}>
      <span className={`badge ${f.severity}`}><span aria-hidden="true">{ICON[f.severity]}</span>{t(LABEL[f.severity])}</span>
      <h3>{f.title}</h3>
      <p>{f.explanation}</p>
      {f.action && <p className="action"><b>{t('What to do:')} </b>{f.action}</p>}
      {f.sources.length > 0 && (
        <p className="sources">{t('Source:')} {f.sources.map((src, j) => (
          <span key={j}>{j > 0 && '; '}{src.url ? <a href={src.url} target="_blank" rel="noreferrer">{src.name}</a> : src.name}
            {src.as_of && ` (${src.as_of.slice(0, 10)})`}</span>
        ))}</p>
      )}
    </article>
  )
}

export default function Results({ result, simple = false }: { result: CheckResult; simple?: boolean }) {
  const t = useT()
  const s = result.summary
  const problems = result.findings.filter((f) => f.severity === 'error' || f.severity === 'warning')
  const info = result.findings.filter((f) => f.severity === 'info')
  const passed = result.findings.filter((f) => f.severity === 'ok')
  const [showKit, setShowKit] = useState(!simple)
  const owesZero = passed.some((f) => f.rule === 'eob_owe_zero')
  const steps = [...new Set((problems.length ? problems : passed.filter((f) => f.rule === 'eob_owe_zero'))
    .map((f) => f.action).filter(Boolean))].slice(0, 3)
  return (
    <div className="stack-lg">
      <section className={`verdict ${s.verdict}`} aria-live="polite">
        <h2>{s.verdict === 'looks_right' && simple && !owesZero ? t('Your bill looks right.') : s.headline}</h2>
        <div className="figures">
          {s.eob_you_owe != null && <div className="figure"><span className="small muted">{t('EOB says you owe')}</span><b>{money(s.eob_you_owe)}</b></div>}
          {s.bill_balance != null && <div className="figure"><span className="small muted">{t('Bill asks for')}</span><b>{money(s.bill_balance)}</b></div>}
          {s.amount_at_stake > 0 && <div className="figure"><span className="small muted">{t('Amount in question')}</span><b>{money(s.amount_at_stake)}</b></div>}
        </div>
      </section>

      {simple && steps.length > 0 && (
        <section className="card stack">
          <h2>{t('What to do now')}</h2>
          <ol className="script">{steps.map((x, i) => <li key={i}>{x}</li>)}</ol>
          {result.letter && !showKit && <div><button type="button" onClick={() => setShowKit(true)}>{t('Get a ready-to-send letter')}</button></div>}
        </section>
      )}

      {simple && problems.length === 0 && result.letter && (
        <section className="card stack">
          <h2>{t('First step: ask for an itemized bill')}</h2>
          <p>{t('We could not confirm this bill yet. Before you pay, ask the billing office for an itemized bill with a code for each charge. Asking is free, and you can ask them to hold the account while you wait.')}</p>
          {!showKit && <div><button type="button" onClick={() => setShowKit(true)}>{t('Get the letter and phone script')}</button></div>}
        </section>
      )}

      {problems.length > 0 && (
        <section className="stack">
          {simple && <h2>{t('Why')}</h2>}
          {problems.map((f, i) => <FindingCard key={i} f={f} />)}
        </section>
      )}
      {!simple && problems.length === 0 && <p className="muted">{t('No problems found in what you entered.')}</p>}

      {info.length > 0 && (simple ? (
        <details className="card" open={problems.length === 0}><summary>{t('Good to know')} ({info.length})</summary>
          <div className="stack" style={{ marginTop: 12 }}>{info.map((f, i) => <FindingCard key={i} f={f} />)}</div>
        </details>
      ) : <section className="stack">{info.map((f, i) => <FindingCard key={i} f={f} />)}</section>)}

      {passed.length > 0 && (
        <details className="card" open={!simple || passed.some((f) => f.rule === 'er_rate_matches')}>
          <summary>{t('Checks that passed')} ({passed.length})</summary>
          <div className="stack" style={{ marginTop: 12 }}>
            {passed.map((f, i) => <p key={i}><span className="badge ok">✓ {t('Checked')}</span> <b>{f.title}.</b> {f.explanation}</p>)}
          </div>
        </details>
      )}

      {result.letter && showKit && <DisputeKit letter={result.letter} script={result.call_script} />}

      <details className="card">
        <summary>{t('What we checked')}</summary>
        <ul>
          {result.checks_run.map((c) => <li key={c}>{t(CHECK_NAMES[c] ?? c)}</li>)}
          {Object.entries(result.checks_skipped).map(([c, why]) => <li key={c} className="muted">{t(CHECK_NAMES[c] ?? c)}: {t('not checked')} ({why})</li>)}
        </ul>
        <p className="small muted">{result.disclaimer}</p>
      </details>
    </div>
  )
}
