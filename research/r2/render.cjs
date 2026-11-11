// Render each synthetic case as two document images (EOB and hospital bill) for condition C of the R2 benchmark.
// Usage: node research/r2/render.cjs
// Needs playwright-core and a Chromium build: set PLAYWRIGHT_CORE (module path) and CHROMIUM (executable) if they
// are not at the defaults below. Output: research/r2/data/images/<id>_eob.png, <id>_bill.png
const fs = require('fs')
const path = require('path')
const home = process.env.HOME
const { chromium } = require(process.env.PLAYWRIGHT_CORE ||
  `${home}/.nvm/versions/node/v20.19.4/lib/node_modules/@playwright/cli/node_modules/playwright-core`)
const exe = process.env.CHROMIUM || `${home}/.cache/ms-playwright/chromium-1243/chrome-linux64/chrome`

const dir = path.join(__dirname, process.env.R2_DATA || 'data')   // data_confirm: confirmatory set
const out = path.join(dir, 'images')
fs.mkdirSync(out, { recursive: true })
const { cases } = JSON.parse(fs.readFileSync(path.join(dir, 'cases.json'), 'utf8'))
const m = (x) => `$${x.toFixed(2)}`
const css = `body{font-family:Arial,Helvetica,sans-serif;margin:28px;color:#111;width:1000px}h1{font-size:22px;margin:0}
table{border-collapse:collapse;width:100%;font-size:13px;margin-top:14px}th,td{border:1px solid #777;padding:6px;text-align:left}
td.n,th.n{text-align:right}.top{display:flex;justify-content:space-between;margin-bottom:10px}.tot{font-weight:bold;font-size:16px;margin-top:10px}`

function eob(c) {
  const e = c.request.eob
  const rows = e.lines.map((l) => `<tr><td>${l.line}</td><td>${l.service_date}</td><td>${l.description}</td><td>${l.code}</td>
    <td class=n>${m(l.billed)}</td><td class=n>${m(l.allowed)}</td><td class=n>${m(l.copay)}</td><td class=n>${m(l.deductible)}</td>
    <td class=n>${m(l.coinsurance)}</td><td class=n>${m(l.plan_paid)}</td><td class=n>${m(l.you_owe)}</td></tr>`).join('')
  return `<style>${css}</style><div class=top><div><h1>EXPLANATION OF BENEFITS</h1><b>THIS IS NOT A BILL</b></div>
  <div>Blue Cross Blue Shield of Arizona<br>Member: Alex Sample<br>Claim: ${e.claim_number}</div></div>
  <div>Provider: Banner - University Medical Center Tucson (in network)</div>
  <table><tr><th>Line</th><th>Date</th><th>Service</th><th>Code</th><th class=n>Provider charges</th><th class=n>Allowed</th>
  <th class=n>Copay</th><th class=n>Deductible</th><th class=n>Coinsurance</th><th class=n>Paid by insurer</th><th class=n>What you owe</th></tr>${rows}</table>
  <div class=tot>Total you owe: ${m(e.you_owe_total)}</div>`
}

function bill(c) {
  const b = c.request.bill
  const rows = b.lines.map((l) => `<tr><td>${l.service_date}</td><td>${l.description}</td><td>${l.code}</td><td class=n>${l.units}</td>
    <td class=n>${m(l.amount)}</td></tr>`).join('')
  return `<style>${css}</style><div class=top><div><h1>Banner - University Medical Center Tucson</h1>Patient statement</div>
  <div>Statement date: ${b.statement_date}<br>Guarantor: Alex Sample<br>Account: 0000000000</div></div>
  <table><tr><th>Date</th><th>Description</th><th>Code</th><th class=n>Units</th><th class=n>Charges</th></tr>${rows}
  <tr><td colspan=4>Insurance payments</td><td class=n>-${m(b.insurance_paid)}</td></tr>
  <tr><td colspan=4>Contractual adjustments</td><td class=n>-${m(b.adjustments)}</td></tr>
  <tr><td colspan=4>Patient payments received</td><td class=n>-${m(b.patient_payments)}</td></tr></table>
  <div class=tot>AMOUNT DUE: ${m(b.balance_due)}</div>`
}

;(async () => {
  const browser = await chromium.launch({ executablePath: exe })
  const page = await browser.newPage({ viewport: { width: 1060, height: 600 } })
  for (const c of cases) {
    for (const [kind, html] of [['eob', eob(c)], ['bill', bill(c)]]) {
      await page.setContent(html)
      await page.screenshot({ path: path.join(out, `${c.id}_${kind}.png`), fullPage: true })
    }
  }
  await browser.close()
  console.log(`rendered ${cases.length * 2} images`)
})().catch((e) => { console.error(e); process.exit(1) })
