import { useMemo, useState } from 'react'
import { money } from '../api'
import type { CheckResult, Severity } from '../api'

const LABEL: Record<Severity, string> = { error: 'Likely error', warning: 'Ask about this', info: 'Good to know', ok: 'Checked' }
const ICON: Record<Severity, string> = { error: '✕', warning: '!', info: 'i', ok: '✓' }
const CHECK_NAMES: Record<string, string> = {
  eob_arithmetic: 'EOB math', bill_vs_eob: 'Bill against EOB', duplicates: 'Duplicate charges',
  mue_units: 'Medicare unit limits (MUE)', ncci_ptp: 'Code pairs (NCCI)', published_prices: 'Hospital published prices',
  no_surprises_act: 'No Surprises Act', paperwork: 'Paperwork',
}

// Placeholders the dispute letter uses; values typed here stay in this browser tab.
const FIELDS: [string, string][] = [
  ['[Your name]', 'Your name'], ['[Your address]', 'Your address'], ['[Date]', "Today's date"],
  ['[Account number]', 'Account number on the bill'], ['[Provider name]', 'Provider name'],
  ['[Insurance company]', 'Insurance company'], ['[Date of service]', 'Date of service'],
  ['[Claim number]', 'Claim number'], ['[Phone or email]', 'Phone or email'],
]

function DisputeKit({ letter, script }: { letter: string; script: string[] }) {
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
      <h2>Your dispute kit</h2>
      <p className="small muted">Fill in your details to complete the letter. They stay on this page and are never sent anywhere.</p>
      <div className="grid2">
        {used.map(([p, label]) => (
          <label className="field" key={p}>{label}
            <input value={vals[p] ?? ''} onChange={(e) => setVals((v) => ({ ...v, [p]: e.target.value }))} />
          </label>
        ))}
      </div>
      <label className="field">Letter
        <textarea id="letter" readOnly value={filled} />
      </label>
      <div className="row"><button type="button" onClick={copy}>{copied ? 'Copied' : 'Copy letter'}</button></div>
      <h3>Phone script</h3>
      <ol className="script">{script.map((s, i) => <li key={i}>{s}</li>)}</ol>
    </section>
  )
}

export default function Results({ result }: { result: CheckResult }) {
  const s = result.summary
  const problems = result.findings.filter((f) => f.severity !== 'ok')
  const passed = result.findings.filter((f) => f.severity === 'ok')
  return (
    <div className="stack-lg">
      <section className={`verdict ${s.verdict}`} aria-live="polite">
        <h2>{s.headline}</h2>
        <div className="figures">
          {s.eob_you_owe != null && <div className="figure"><span className="small muted">EOB says you owe</span><b>{money(s.eob_you_owe)}</b></div>}
          {s.bill_balance != null && <div className="figure"><span className="small muted">Bill asks for</span><b>{money(s.bill_balance)}</b></div>}
          {s.amount_at_stake > 0 && <div className="figure"><span className="small muted">Amount in question</span><b>{money(s.amount_at_stake)}</b></div>}
        </div>
      </section>

      <section className="stack">
        {problems.length === 0 && <p className="muted">No problems found in what you entered.</p>}
        {problems.map((f, i) => (
          <article key={i} className={`card finding ${f.severity}`}>
            <span className={`badge ${f.severity}`}><span aria-hidden="true">{ICON[f.severity]}</span>{LABEL[f.severity]}</span>
            <h3>{f.title}</h3>
            <p>{f.explanation}</p>
            {f.action && <p className="action"><b>What to do: </b>{f.action}</p>}
            {f.sources.length > 0 && (
              <p className="sources">Source: {f.sources.map((src, j) => (
                <span key={j}>{j > 0 && '; '}{src.url ? <a href={src.url} target="_blank" rel="noreferrer">{src.name}</a> : src.name}
                  {src.as_of && ` (${src.as_of.slice(0, 10)})`}</span>
              ))}</p>
            )}
          </article>
        ))}
      </section>

      {passed.length > 0 && (
        <section className="stack">
          <h3>Checks that passed</h3>
          {passed.map((f, i) => (
            <article key={i} className="card finding ok">
              <span className="badge ok"><span aria-hidden="true">✓</span>Checked</span>
              <p><b>{f.title}.</b> {f.explanation}</p>
            </article>
          ))}
        </section>
      )}

      {result.letter && <DisputeKit letter={result.letter} script={result.call_script} />}

      <details className="card">
        <summary>What we checked</summary>
        <ul>
          {result.checks_run.map((c) => <li key={c}>{CHECK_NAMES[c] ?? c}</li>)}
          {Object.entries(result.checks_skipped).map(([c, why]) => <li key={c} className="muted">{CHECK_NAMES[c] ?? c}: not checked ({why})</li>)}
        </ul>
        <p className="small muted">{result.disclaimer}</p>
      </details>
    </div>
  )
}
