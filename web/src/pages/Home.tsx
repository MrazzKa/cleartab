import Icon from '../icons'
import type { IconName } from '../icons'
import { useEffect, useState } from 'react'
import { reader } from '../api'
import { useT } from '../i18n'

const DOORS: [string, IconName, string, string][] = [
  ['#/help', 'heart', 'I can’t afford it', 'See if the hospital must lower it or forgive it, and get your application ready. About 1 minute.'],
  ['#/bill', 'check', 'I think it’s wrong', 'Compare the bill with your insurance statement and the hospital’s own prices. Ambulance bills too. Get a letter to send.'],
  ['#/visits', 'layers', 'I have a pile of bills from one visit', 'Put every bill, EOB and receipt in one place and see whom you really owe. Saved only on your phone.'],
  ['#/prices', 'tag', 'I want a price before care', 'What Tucson and Phoenix hospitals published for 50 common procedures.'],
]

export default function Home() {
  const t = useT()
  const [scan, setScan] = useState(true)
  useEffect(() => { reader.status().then(setScan) }, [])
  return (
    <div className="stack-lg">
      <section className="hero-card">
        <p className="eyebrow">{t('Free help for Arizona patients')}</p>
        <h1>{t('Got a hospital bill?')}</h1>
        <p className="hero-sub">{scan
          ? t('Snap a photo or upload the PDF of your bill or insurance statement. In about a minute you’ll know what you really owe, what to question and what help you can get.')
          : t('Type three numbers from your bill and insurance statement. In about a minute you’ll know what you really owe, what to question and what help you can get.')}</p>
        <div className="hero-actions">
          {scan
            ? <a className="button-primary" href="#/bill"><Icon name="camera" />{t('Scan a bill or EOB')}</a>
            : <a className="button-primary" href="#/bill"><Icon name="check" />{t('Check a medical bill')}</a>}
          <a className="button-quiet" href="#/help">{t('I can’t afford it')} <Icon name="arrow" size={18} /></a>
        </div>
        <ul className="trust">
          <li><Icon name="shield" size={18} />{t('No account')}</li>
          <li><Icon name="layers" size={18} />{t('Saved only on your phone')}</li>
          <li><Icon name="globe" size={18} />English · Español</li>
        </ul>
      </section>

      <section className="stack">
        <h2>{t('What do you need?')}</h2>
        <div className="doors">
          {DOORS.map(([href, icon, title, text]) => (
            <a key={href} className="door" href={href}>
              <span className="door-icon"><Icon name={icon} size={24} /></span>
              <span className="door-text"><b>{t(title)}</b><small>{t(text)}</small></span>
              <span className="door-go" aria-hidden="true"><Icon name="arrow" size={18} /></span>
            </a>
          ))}
        </div>
      </section>

      <section className="card stack">
        <h2>{t('Why this matters')}</h2>
        <div className="stats">
          <div><b>41%</b><span>{t('of US adults have debt from medical or dental bills')}</span></div>
          <div><b>44%</b><span>{t('of them did not pay a bill in full because they were not sure it was correct')}</span></div>
        </div>
        <p className="muted">{t('Most people don’t know that nonprofit hospitals must offer financial assistance.')}</p>
        <p className="small muted">{t('Sources:')} <a href="https://www.kff.org/health-costs/kff-health-care-debt-survey/" target="_blank"
          rel="noreferrer">KFF Health Care Debt Survey (2022)</a>; <a href="https://www.irs.gov/charities-non-profits/billing-and-collections-section-501r6"
          target="_blank" rel="noreferrer">IRS section 501(r)</a>.</p>
      </section>
    </div>
  )
}
