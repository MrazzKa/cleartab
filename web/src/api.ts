// Typed client for the ClearTab API. Bill and income data are sent only to compute an answer; the API never logs
// or stores request bodies.
const BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? '/api'

export type Severity = 'error' | 'warning' | 'info' | 'ok'

export interface EobLine {
  line?: number | null
  service_date?: string | null
  description: string
  code?: string | null
  units: number
  billed?: number | null
  discount?: number | null
  allowed?: number | null
  copay: number
  deductible: number
  coinsurance: number
  not_covered: number
  plan_paid?: number | null
  you_owe?: number | null
  status: 'paid' | 'denied' | 'pending' | 'adjusted' | 'unknown'
  remark: string
}

export interface BillLine {
  service_date?: string | null
  description: string
  code?: string | null
  revenue_code?: string | null
  units: number
  amount: number
}

export interface PlanBalance {
  kind: 'deductible' | 'out_of_pocket'; network: 'in' | 'out' | 'unknown'; level: 'individual' | 'family' | 'unknown'
  limit: number | null; used: number | null; remaining: number | null
}

export interface Context {
  coverage: 'insured' | 'self_pay'
  hospital_ccn?: string | null
  insurer?: string | null
  provider_name?: string | null
  insurer_name?: string | null
  network: 'in' | 'out' | 'unknown'
  emergency: boolean
  ambulance: 'none' | 'ground' | 'air'
  ambulance_con?: string | null
  ambulance_level?: 'als' | 'bls' | 'ccs' | 'unknown'
  ambulance_miles?: number | null
  transported?: boolean | null
  lang?: 'en' | 'es'
  good_faith_estimate?: number | null
  gfe_received: boolean
  today?: string | null
}

export interface CheckRequest {
  context: Context
  eob?: {
    claim_number?: string | null; lines: EobLine[]; you_owe_total?: number | null; oop_max_met?: boolean
    balances?: PlanBalance[]
  } | null
  bill?: {
    provider_type: 'facility' | 'professional' | 'ambulance' | 'unknown'
    statement_date?: string | null
    lines: BillLine[]
    insurance_paid: number
    adjustments: number
    patient_payments: number
    balance_due?: number | null
  } | null
}

export interface Source { name: string; url?: string | null; as_of?: string | null }

export interface Finding {
  rule: string
  severity: Severity
  title: string
  explanation: string
  action: string
  lines: number[]
  evidence: Record<string, unknown>
  amount_at_stake?: number | null
  sources: Source[]
}

export interface CheckResult {
  summary: {
    verdict: 'looks_right' | 'questions' | 'likely_errors' | 'not_enough_data'
    headline: string
    eob_you_owe?: number | null
    bill_balance?: number | null
    difference?: number | null
    amount_at_stake: number
    counts: Partial<Record<Severity, number>>
  }
  findings: Finding[]
  checks_run: string[]
  checks_skipped: Record<string, string>
  letter: string
  call_script: string[]
  disclaimer: string
}

export interface DemoCase { id: string; title: string; story: string; request: CheckRequest }

export interface Hospital {
  ccn: string; name: string; city: string; metro: string; health_system: string; phone: string | null
  status: string; has_prices: boolean
}

export interface AssistanceResult {
  system: string; registry_systems: string[]
  status: 'free' | 'discount' | 'above' | 'unknown' | 'not_eligible'
  result: string; nonprofit_501r: boolean; covers: string; window: string; how_to_apply: string
  phone: string | null; assets_test: string; notes: string; source_url: string; page_url: string; retrieved_at: string
  application_url: string | null; documents: string[]; send_to: string; policy: string
}

export interface AssistanceResponse {
  fpl_percent: number; poverty_line: number; guidelines: { year: number; source_url: string }
  results: AssistanceResult[]; note: string
}

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(BASE + path, init)
  if (!r.ok) {
    let detail: unknown = `${r.status}`
    try { detail = (await r.json()).detail ?? detail } catch { /* not JSON */ }
    // Plain sentences from the API (limits, consent) are shown as they are.
    if (typeof detail === 'string' && detail.includes(' ')) throw new Error(detail)
    throw new Error(`The server could not answer (${JSON.stringify(detail)}).`)
  }
  return r.json() as Promise<T>
}

const post = (body: unknown): RequestInit => ({
  method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
})

export const api = {
  check: (req: CheckRequest) => call<CheckResult>('/bill/check', post(req)),
  cases: () => call<{ cases: DemoCase[] }>('/bill/cases').then((x) => x.cases),
  hospitals: () => call<{ hospitals: Hospital[] }>('/hospitals').then((x) => x.hospitals),
  plans: () => call<{ plans: string[] }>('/plans').then((x) => x.plans.filter((p) => p !== 'cash')),
  assistance: (household_size: number, annual_income: number, coverage: string, hospital_system?: string, lang = 'en') =>
    call<AssistanceResponse>('/assistance', post({ household_size, annual_income, coverage, hospital_system, lang })),
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  search: (q: string, plan: string, zip: string) => call<any>(`/search?${new URLSearchParams({ q, plan, zip })}`),
}

export interface ReadLine {
  service_date: string | null; description: string; code: string | null
  billed: number | null; discount: number | null; allowed: number | null; copay: number | null; deductible: number | null
  coinsurance: number | null; not_covered: number | null; plan_paid: number | null; you_owe: number | null
  status: string; units: number | null; amount: number | null
}

export interface ReadResult {
  document_type: 'eob' | 'bill' | 'both' | 'other'; provider_type: string; provider_name: string | null; insurer_name?: string | null; statement_date: string | null
  claim_number: string | null; balance_due: number | null; patient_payments: number | null
  you_owe_total: number | null; oop_max_met: boolean; eob_lines: ReadLine[]; bill_lines: ReadLine[]
  plan_balances?: PlanBalance[]
  unreadable: string[]; note: string
}

const isPdf = (f: File) => f.type === 'application/pdf' || f.name.toLowerCase().endsWith('.pdf')

async function fileBase64(file: File): Promise<string> {
  const buf = new Uint8Array(await file.arrayBuffer())
  let bin = ''
  for (let i = 0; i < buf.length; i += 0x8000) bin += String.fromCharCode(...buf.subarray(i, i + 0x8000))
  return btoa(bin)
}

/** One PDF, or up to three photos (shrunk in the browser first). */
async function toUploads(files: FileList | File[]): Promise<{ data: string; type: string }[]> {
  const list = [...files]
  const pdf = list.find(isPdf)
  if (pdf) return [{ data: await fileBase64(pdf), type: 'application/pdf' }]
  return Promise.all(list.slice(0, 3).map(shrinkPhoto))
}

export interface ReaderInfo { available: boolean; mode: 'on' | 'local' | 'examples' | 'off'; service: string | null }
const noReader: ReaderInfo = { available: false, mode: 'off', service: null }

export const reader = {
  info: () => call<ReaderInfo>('/bill/read/status').catch(() => noReader),
  /** True when the user's own documents may be read (READ_MODE on or local). */
  status: () => reader.info().then((x) => x.available && (x.mode === 'on' || x.mode === 'local')),
  read: async (files: FileList | File[]) => call<ReadResult>('/bill/read', post({ images: await toUploads(files), consent: true })),
  /** Read a synthetic example document kept on the server (no upload). */
  example: (name: string) => call<ReadResult>(`/bill/read/example/${encodeURIComponent(name)}`, post({})),
}

/** Turn read EOB lines into check lines. Empty amounts stay empty: the rule engine skips what it cannot check. */
const isoDate = (d: string | null) => (d && /^\d{4}-\d{2}-\d{2}$/.test(d) ? d : null)
export const toEobLines = (lines: ReadLine[]): EobLine[] => lines.map((l) => ({
  service_date: isoDate(l.service_date), description: l.description, code: l.code, units: 1,
  billed: l.billed, discount: l.discount, allowed: l.allowed, plan_paid: l.plan_paid, you_owe: l.you_owe,
  copay: l.copay ?? 0, deductible: l.deductible ?? 0, coinsurance: l.coinsurance ?? 0, not_covered: l.not_covered ?? 0,
  status: (['paid', 'denied', 'pending', 'adjusted'].includes(l.status) ? l.status : 'unknown') as EobLine['status'], remark: '',
}))

/** Shrink a phone photo to at most 2000 px and re-encode as JPEG, returning base64 without the data: prefix. */
export async function shrinkPhoto(file: File): Promise<{ data: string; type: string }> {
  const bmp = await createImageBitmap(file)
  const scale = Math.min(1, 2000 / Math.max(bmp.width, bmp.height))
  const c = document.createElement('canvas')
  c.width = Math.round(bmp.width * scale); c.height = Math.round(bmp.height * scale)
  c.getContext('2d')!.drawImage(bmp, 0, 0, c.width, c.height)
  const url = c.toDataURL('image/jpeg', 0.85)
  return { data: url.split(',')[1], type: 'image/jpeg' }
}

export interface AmbulanceService { con: string; entity: string; rate_group: string; als: number; bls: number | null; mileage: number }
export const ambulanceServices = () =>
  call<{ services: AmbulanceService[] }>('/ambulance/services').then((x) => x.services).catch(() => [] as AmbulanceService[])

export const money = (x: number | null | undefined) =>
  x == null ? '-' : x.toLocaleString('en-US', { style: 'currency', currency: 'USD' })
