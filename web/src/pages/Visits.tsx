import { useEffect, useMemo, useState } from 'react'
import { money, reader } from '../api'
import type { PlanBalance } from '../api'
import Icon from '../icons'
import { useT } from '../i18n'

// "My visits": every paper from one visit (bills, explanations of benefits, payment receipts) in one place, and one
// answer per provider: what to pay, what to wait for, what to question. Stored only in this browser (localStorage);
// nothing is sent to the server except photos the user chooses to have read.
type Kind = 'bill' | 'eob' | 'receipt'
interface Doc { id: string; kind: Kind; provider: string; amount: number | null; date: string; balances?: PlanBalance[] }
interface Visit { id: string; title: string; date: string; docs: Doc[] }

const KEY = 'cleartab-visits'
const uid = () => Math.random().toString(36).slice(2, 10)
const load = (): Visit[] => { try { return JSON.parse(localStorage.getItem(KEY) || '[]') } catch { return [] } }
const save = (v: Visit[]) => { try { localStorage.setItem(KEY, JSON.stringify(v)) } catch { /* storage blocked */ } }
const norm = (s: string) => s.trim().toLowerCase().replace(/\s+/g, ' ')

interface Line { provider: string; billed: number | null; eobOwe: number | null; paid: number; expected: number | null
  status: 'pay' | 'dispute' | 'wait_eob' | 'wait_bill' | 'paid'; extra: number }

// eslint-disable-next-line react-refresh/only-export-components
export function summarize(v: Visit): Line[] {
  const by = new Map<string, Doc[]>()
  v.docs.forEach((d) => { const k = norm(d.provider) || '?'; by.set(k, [...(by.get(k) ?? []), d]) })
  return [...by.values()].map((docs) => {
    const bills = docs.filter((d) => d.kind === 'bill' && d.amount != null).sort((a, b) => a.date.localeCompare(b.date))
    const billed = bills.length ? bills[bills.length - 1].amount : null           // the latest statement
    const eobs = docs.filter((d) => d.kind === 'eob' && d.amount != null)
    const eobOwe = eobs.length ? eobs.reduce((s, d) => s + (d.amount ?? 0), 0) : null
    const paid = docs.filter((d) => d.kind === 'receipt').reduce((s, d) => s + (d.amount ?? 0), 0)
    const expected = eobOwe == null ? null : Math.max(eobOwe - paid, 0)
    let status: Line['status'] = 'paid'; let extra = 0
    if (billed != null && expected != null) {
      if (billed > expected + 0.01) { status = 'dispute'; extra = billed - expected } else status = billed > 0 ? 'pay' : 'paid'
    } else if (billed != null) status = 'wait_eob'
    else if (expected != null && expected > 0) status = 'wait_bill'
    return { provider: docs[0].provider || '?', billed, eobOwe, paid, expected, status, extra }
  })
}

// Plan balances across every EOB on this device: the latest numbers, and any "used so far" that went down between
// two EOBs (it should only go up during a plan year).
interface BalanceView { label: string; left: number | null; used: number | null; limit: number | null; date: string }
interface BalanceDrop { label: string; from: number; to: number; fromDate: string; toDate: string }
// eslint-disable-next-line react-refresh/only-export-components
export function balances(visits: Visit[]): { latest: BalanceView[]; drops: BalanceDrop[] } {
  const rows = visits.flatMap((v) => v.docs.filter((d) => d.kind === 'eob' && d.balances?.length)
    .flatMap((d) => (d.balances ?? []).filter((b) => b.network !== 'out').map((b) => ({ b, date: d.date }))))
  const key = (b: PlanBalance) => `${b.kind}|${b.level}`
  const label = (b: PlanBalance) => (b.kind === 'deductible' ? 'Deductible' : 'Out-of-pocket limit') + (b.level === 'family' ? ' (family)' : '')
  const groups = new Map<string, { b: PlanBalance; date: string }[]>()
  rows.forEach((r) => groups.set(key(r.b), [...(groups.get(key(r.b)) ?? []), r]))
  const latest: BalanceView[] = []; const drops: BalanceDrop[] = []
  groups.forEach((list) => {
    list.sort((a, b) => a.date.localeCompare(b.date))
    const last = list[list.length - 1]
    const left = last.b.remaining ?? (last.b.limit != null && last.b.used != null ? Math.max(last.b.limit - last.b.used, 0) : null)
    latest.push({ label: label(last.b), left, used: last.b.used, limit: last.b.limit, date: last.date })
    for (let i = 1; i < list.length; i++) {
      const a = list[i - 1], c = list[i]
      if (a.b.used != null && c.b.used != null && c.b.used < a.b.used - 0.01 && c.date > a.date)
        drops.push({ label: label(c.b), from: a.b.used, to: c.b.used, fromDate: a.date, toDate: c.date })
    }
  })
  return { latest, drops }
}

function ics(title: string, date: Date, text: string) {
  const d = date.toISOString().slice(0, 10).replace(/-/g, '')
  const body = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//ClearTab//EN', 'BEGIN:VEVENT', `UID:${uid()}@cleartab`,
    `DTSTAMP:${new Date().toISOString().replace(/[-:]/g, '').slice(0, 15)}Z`, `DTSTART;VALUE=DATE:${d}`,
    `SUMMARY:${title}`, `DESCRIPTION:${text.replace(/\n/g, '\\n')}`, 'END:VEVENT', 'END:VCALENDAR'].join('\r\n')
  const a = document.createElement('a')
  a.href = URL.createObjectURL(new Blob([body], { type: 'text/calendar' }))
  a.download = 'cleartab-reminder.ics'
  a.click()
}

function collectorLetter(provider: string, amount: number | null) {
  return ['[Your name]', '[Your address]', '[Date]', '', 'To: [Collection agency name and address]',
    `Re: Account [Account number], original creditor ${provider}${amount != null ? `, amount ${money(amount)}` : ''}`, '',
    'I am responding to your contact about this debt. I dispute this debt and request verification. Until you provide',
    'it, please stop collection, including any credit reporting. Please send me:', '',
    '1. The name and address of the original creditor and the date of service.',
    '2. An itemized statement of the amount you are trying to collect, including any interest or fees.',
    '3. Proof that my health insurance was billed, and the explanation of benefits for this claim.',
    '4. Whether the hospital screened this account for its financial assistance policy before sending it to you.',
    '5. A copy of any document that shows I agreed to pay this amount.', '',
    'I have records of payments and of my explanation of benefits for this visit and can provide them.', '',
    'Sincerely,', '[Your name]'].join('\n')
}

export default function Visits() {
  const t = useT()
  const [visits, setVisits] = useState<Visit[]>(load)
  const [open, setOpen] = useState<string | null>(visits[0]?.id ?? null)
  const [form, setForm] = useState<{ kind: Kind; provider: string; amount: string; date: string }>({ kind: 'bill', provider: '', amount: '', date: '' })
  const [consent, setConsent] = useState(false)
  const [canRead, setCanRead] = useState(false)
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState('')
  const [letter, setLetter] = useState('')
  useEffect(() => { save(visits) }, [visits])
  const [readService, setReadService] = useState('')
  const [readLocal, setReadLocal] = useState(false)
  useEffect(() => {
    reader.info().then((x) => {
      setCanRead(x.available && (x.mode === 'on' || x.mode === 'local')); setReadService(x.service ?? ''); setReadLocal(x.mode === 'local')
    })
  }, [])

  const visit = visits.find((v) => v.id === open) ?? null
  const lines = useMemo(() => (visit ? summarize(visit) : []), [visit])
  const plan = useMemo(() => balances(visits), [visits])
  const totals = useMemo(() => ({
    billed: lines.reduce((s, l) => s + (l.billed ?? 0), 0),
    payNow: lines.filter((l) => l.status === 'pay' || l.status === 'dispute').reduce((s, l) => s + Math.min(l.billed ?? 0, l.expected ?? l.billed ?? 0), 0),
    question: lines.reduce((s, l) => s + l.extra, 0),
    waiting: lines.filter((l) => l.status === 'wait_eob').reduce((s, l) => s + (l.billed ?? 0), 0),
  }), [lines])

  const update = (fn: (v: Visit) => Visit) => setVisits((vs) => vs.map((v) => (v.id === open ? fn(v) : v)))
  const newVisit = () => {
    const v: Visit = { id: uid(), title: t('New visit'), date: new Date().toISOString().slice(0, 10), docs: [] }
    setVisits((vs) => [v, ...vs]); setOpen(v.id)
  }
  const example = () => {
    const date = new Date().toISOString().slice(0, 10)
    const docs: Omit<Doc, 'id'>[] = [
      { kind: 'bill', provider: 'Banner UMC Tucson', amount: 1222.30, date },
      { kind: 'eob', provider: 'Banner UMC Tucson', amount: 1154.80, date },
      { kind: 'bill', provider: 'Emergency physicians group', amount: 652, date },
      { kind: 'eob', provider: 'Emergency physicians group', amount: 82, date },
      { kind: 'bill', provider: 'Radiology Ltd', amount: 95, date },
      { kind: 'bill', provider: 'Tucson Fire Department', amount: 1950, date },
    ]
    const v: Visit = { id: uid(), title: t('Example: ER visit'), date, docs: docs.map((d) => ({ ...d, id: uid() })) }
    setVisits((vs) => [v, ...vs]); setOpen(v.id)
  }
  const addDoc = (d: Omit<Doc, 'id'>) => update((v) => ({ ...v, docs: [...v.docs, { ...d, id: uid() }] }))
  const addManual = () => {
    if (!form.provider.trim() || form.amount === '') return
    addDoc({ kind: form.kind, provider: form.provider.trim(), amount: Number(form.amount), date: form.date || visit?.date || '' })
    setForm({ ...form, amount: '' })
  }
  const onPhotos = async (files: FileList | null) => {
    if (!files?.length) return
    setBusy(true); setMsg('')
    try {
      const r = await reader.read(files)
      const provider = r.provider_name || t('Unknown provider')
      const date = r.statement_date || visit?.date || ''
      if (r.balance_due != null) addDoc({ kind: 'bill', provider, amount: r.balance_due, date })
      if (r.you_owe_total != null) addDoc({ kind: 'eob', provider, amount: r.you_owe_total, date, balances: r.plan_balances ?? [] })
      if (r.patient_payments) addDoc({ kind: 'receipt', provider, amount: r.patient_payments, date })
      setMsg(t('Added from your document. Check the numbers against your paper.'))
    } catch (e) { setMsg((e as Error).message) } finally { setBusy(false) }
  }
  const share = async () => {
    if (!visit) return
    const text = [`${visit.title} (${visit.date})`, ...lines.map((l) => `${l.provider}: ${t(STATUS[l.status])}`
      + (l.status === 'dispute' ? ` (${money(l.extra)})` : l.status === 'pay' ? ` ${money(l.billed)}` : ''))].join('\n')
    try {
      if (navigator.share) await navigator.share({ title: 'ClearTab', text })
      else { await navigator.clipboard.writeText(text); setMsg(t('Summary copied. Paste it in a message to your family.')) }
    } catch { /* cancelled */ }
  }

  return (
    <div className="stack-lg">
      <section className="hero">
        <h1>{t('My visits')}</h1>
        <p>{t('Keep every bill, explanation of benefits and receipt from one visit together. See whom you really owe and how much. Saved only on this device.')}</p>
      </section>

      <div className="row">
        <button type="button" onClick={newVisit}>{t('+ New visit')}</button>
        {visits.length === 0 && <button type="button" className="secondary" onClick={example}>{t('See an example')}</button>}
        {visits.length > 1 && (
          <select value={open ?? ''} onChange={(e) => setOpen(e.target.value)} aria-label={t('Choose a visit')} style={{ maxWidth: 320 }}>
            {visits.map((v) => <option key={v.id} value={v.id}>{v.title} ({v.date})</option>)}
          </select>
        )}
      </div>

      {!visit && <p className="muted">{t('Start a visit, then add each paper as it arrives.')}</p>}

      {visit && (
        <>
          <section className="card stack">
            <div className="grid2">
              <label className="field">{t('Visit name')}<input value={visit.title} onChange={(e) => update((v) => ({ ...v, title: e.target.value }))} /></label>
              <label className="field">{t('Date of care')}<input type="date" value={visit.date} onChange={(e) => update((v) => ({ ...v, date: e.target.value }))} /></label>
            </div>
          </section>

          {lines.length > 0 && (
            <section className={`verdict ${totals.question > 0 ? 'likely_errors' : totals.waiting > 0 ? 'questions' : 'looks_right'}`}>
              <h2>{totals.question > 0 ? t('Don’t pay {q} of it yet', { q: money(totals.question) })
                : totals.waiting > 0 ? t('Wait before paying {w}', { w: money(totals.waiting) }) : t('Everything matches')}</h2>
              <div className="figures">
                <div className="figure"><span className="small muted">{t('Bills ask for')}</span><b>{money(totals.billed)}</b></div>
                <div className="figure"><span className="small muted">{t('You really owe now')}</span><b>{money(totals.payNow)}</b></div>
                {totals.question > 0 && <div className="figure"><span className="small muted">{t('In question')}</span><b>{money(totals.question)}</b></div>}
              </div>
            </section>
          )}

          {plan.latest.length > 0 && (
            <section className="card stack">
              <h2>{t('Your plan year so far')}</h2>
              {plan.latest.map((b) => (
                <p key={b.label}><b>{t(b.label)}:</b> {b.left != null ? t('{left} left', { left: money(b.left) }) : ''}
                  {b.used != null && b.limit != null && <span className="muted"> · {t('{used} of {limit} used', { used: money(b.used), limit: money(b.limit) })}</span>}
                  <span className="small muted"> ({t('EOB of {d}', { d: b.date })})</span></p>
              ))}
              {plan.drops.map((d, i) => (
                <p key={i} className="error-box">{t('{label}: the amount used went down from {a} ({da}) to {b} ({db}). It should only go up during a plan year: ask your insurer why.',
                  { label: t(d.label), a: money(d.from), da: d.fromDate, b: money(d.to), db: d.toDate })}</p>
              ))}
            </section>
          )}

          {lines.map((l) => (
            <article key={l.provider} className={`card finding ${l.status === 'dispute' ? 'error' : l.status.startsWith('wait') ? 'warning' : 'ok'}`}>
              <h3>{l.provider}</h3>
              <p><b>{t(STATUS[l.status])}</b>{l.status === 'pay' && ` ${money(l.billed)}`}{l.status === 'dispute' && ` · ${t('pay {p}, not {b}', { p: money(l.expected), b: money(l.billed) })}`}</p>
              <p className="small muted">{t('Bill')}: {money(l.billed)} · {t('EOB says you owe')}: {money(l.eobOwe)} · {t('Paid')}: {money(l.paid)}</p>
              {l.status === 'dispute' && <div className="row">
                <a className="button-link" href="#/bill">{t('Check this bill in detail')}</a>
              </div>}
              <div className="row">
                <button type="button" className="ghost" onClick={() => setLetter(collectorLetter(l.provider, l.billed))}>{t('A collector contacted me about this')}</button>
              </div>
            </article>
          ))}

          {letter && (
            <section className="card stack">
              <h2>{t('Letter to the collector')}</h2>
              <p className="small muted">{t('Send it in writing within 30 days of the collector’s first notice. Until it verifies the debt, it must stop collecting. Based on the CFPB sample letter.')} <a href="https://www.consumerfinance.gov/ask-cfpb/what-information-does-a-debt-collector-have-to-give-me-about-the-debt-en-331/" target="_blank" rel="noreferrer">CFPB</a></p>
              <textarea readOnly value={letter} />
              <div className="row"><button type="button" onClick={() => navigator.clipboard?.writeText(letter)}>{t('Copy letter')}</button>
                <button type="button" className="ghost" onClick={() => setLetter('')}>{t('Close')}</button></div>
            </section>
          )}

          <section className="card stack">
            <h2>{t('Add a paper')}</h2>
            {canRead && (
              <>
                <label className="check small"><input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} />
                  <span>{readLocal ? t('I agree to let ClearTab read it on its own server. It is not sent to any AI service and not stored.') : t('I agree to send it to an AI reading service ({service}) that copies the numbers. ClearTab does not store it. Cover your name and member ID if you can.', { service: readService })}</span></label>
                <div className="scan-buttons">
                  <label className={`scan-btn ${consent && !busy ? '' : 'disabled'}`}>
                    <input type="file" accept="image/*" capture="environment" multiple disabled={!consent || busy}
                      onChange={(e) => onPhotos(e.target.files)} aria-label={t('Take a photo')} />
                    <Icon name="camera" size={26} />{t('Take a photo')}
                  </label>
                  <label className={`scan-btn alt ${consent && !busy ? '' : 'disabled'}`}>
                    <input type="file" accept="image/*,application/pdf,.pdf" multiple disabled={!consent || busy}
                      onChange={(e) => onPhotos(e.target.files)} aria-label={t('Upload a photo or PDF')} />
                    <Icon name="file" size={26} />{t('Upload a photo or PDF')}
                  </label>
                </div>
                {busy && <p className="row small" role="status"><span className="spinner" aria-hidden="true" />{t('Reading your document…')}</p>}
                <p className="small muted">{t('Or type it:')}</p>
              </>
            )}
            <div className="seg" role="group" aria-label={t('Type of paper')}>
              {([['bill', t('Bill')], ['eob', t('EOB')], ['receipt', t('Payment receipt')]] as const).map(([k, l]) => (
                <button key={k} type="button" aria-pressed={form.kind === k} onClick={() => setForm({ ...form, kind: k })}>{l}</button>
              ))}
            </div>
            <div className="grid2">
              <label className="field">{t('From (hospital, doctor group, ambulance)')}<input list="providers" value={form.provider} onChange={(e) => setForm({ ...form, provider: e.target.value })} /></label>
              <label className="field">{form.kind === 'bill' ? t('Amount due') : form.kind === 'eob' ? t('What you owe') : t('Amount paid')}
                <input type="number" inputMode="decimal" min="0" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} /></label>
              <label className="field">{t('Date on the paper')}<input type="date" value={form.date} onChange={(e) => setForm({ ...form, date: e.target.value })} /></label>
            </div>
            <datalist id="providers">{[...new Set(visit.docs.map((d) => d.provider))].map((p) => <option key={p} value={p} />)}</datalist>
            <div><button type="button" onClick={addManual}>{t('Add')}</button></div>
            {msg && <p className="action">{msg}</p>}
          </section>

          {visit.docs.length > 0 && (
            <details className="card">
              <summary>{t('Papers in this visit')} ({visit.docs.length})</summary>
              <ul>
                {visit.docs.map((d) => (
                  <li key={d.id}>{d.date} · {t(KIND[d.kind])} · {d.provider} · {money(d.amount)}{' '}
                    <button type="button" className="ghost" onClick={() => update((v) => ({ ...v, docs: v.docs.filter((x) => x.id !== d.id) }))}>{t('Remove')}</button></li>
                ))}
              </ul>
            </details>
          )}

          <section className="card stack">
            <h2>{t('Reminders and sharing')}</h2>
            <div className="row">
              <button type="button" className="secondary" onClick={() => ics(t('Has my EOB arrived?'), new Date(Date.parse(visit.date || new Date().toISOString()) + 30 * 864e5), t('Check your insurer’s app for the explanation of benefits before paying any bill.'))}>{t('Remind me in 30 days to check the EOB')}</button>
              <button type="button" className="secondary" onClick={() => ics(t('Hospital financial assistance deadline'), new Date(Date.parse(visit.date || new Date().toISOString()) + 230 * 864e5), t('Nonprofit hospitals accept applications for at least 240 days after the first bill.'))}>{t('Remind me before the assistance deadline')}</button>
              <button type="button" className="secondary" onClick={share}>{t('Share summary with family')}</button>
            </div>
            <button type="button" className="ghost" onClick={() => { setVisits((vs) => vs.filter((v) => v.id !== open)); setOpen(null) }}>{t('Delete this visit from this device')}</button>
          </section>
        </>
      )}
    </div>
  )
}

const STATUS: Record<Line['status'], string> = {
  pay: 'Pay', dispute: 'Don’t pay the extra yet: the bill is higher than your EOB',
  wait_eob: 'Wait: your insurer has not sent the EOB yet', wait_bill: 'No bill yet', paid: 'Nothing to pay',
}
const KIND: Record<Kind, string> = { bill: 'Bill', eob: 'EOB', receipt: 'Payment receipt' }
