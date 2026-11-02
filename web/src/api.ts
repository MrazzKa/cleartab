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

export interface Context {
  coverage: 'insured' | 'self_pay'
  hospital_ccn?: string | null
  insurer?: string | null
  network: 'in' | 'out' | 'unknown'
  emergency: boolean
  ambulance: 'none' | 'ground' | 'air'
  good_faith_estimate?: number | null
  gfe_received: boolean
  today?: string | null
}

export interface CheckRequest {
  context: Context
  eob?: { claim_number?: string | null; lines: EobLine[]; you_owe_total?: number | null } | null
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
}

export interface AssistanceResponse {
  fpl_percent: number; poverty_line: number; guidelines: { year: number; source_url: string }
  results: AssistanceResult[]; note: string
}

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(BASE + path, init)
  if (!r.ok) {
    let detail = `${r.status}`
    try { detail = JSON.stringify((await r.json()).detail ?? detail) } catch { /* not JSON */ }
    throw new Error(`The server could not answer (${detail}).`)
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
  assistance: (household_size: number, annual_income: number, coverage: string, hospital_system?: string) =>
    call<AssistanceResponse>('/assistance', post({ household_size, annual_income, coverage, hospital_system })),
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  search: (q: string, plan: string, zip: string) => call<any>(`/search?${new URLSearchParams({ q, plan, zip })}`),
}

export interface ReadResult {
  document_type: 'eob' | 'bill' | 'other'; provider_type: string; statement_date: string | null
  claim_number: string | null; balance_due: number | null; patient_payments: number | null
  you_owe_total: number | null; unreadable: string[]; note: string
}

export const reader = {
  status: () => call<{ available: boolean }>('/bill/read/status').then((x) => x.available).catch(() => false),
  read: (images: { data: string; type: string }[]) => call<ReadResult>('/bill/read', post({ images, consent: true })),
}

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

export const money = (x: number | null | undefined) =>
  x == null ? '-' : x.toLocaleString('en-US', { style: 'currency', currency: 'USD' })
