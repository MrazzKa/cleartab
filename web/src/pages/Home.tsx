import { useT } from '../i18n'

export default function Home() {
  const t = useT()
  return (
    <div className="stack-lg">
      <section className="hero">
        <h1>{t('Got a hospital bill?')}</h1>
        <p>{t('Free help for Arizona patients. No account, nothing stored. Pick what fits you best.')}</p>
      </section>
      <div className="choices big-choices">
        <a className="choice" href="#/help">
          <span>{t('I can’t afford it')}</span>
          <small>{t('See if the hospital must lower it or forgive it, and get your application ready. About 1 minute.')}</small>
        </a>
        <a className="choice" href="#/bill">
          <span>{t('I think it’s wrong')}</span>
          <small>{t('Compare the bill with your insurance statement and the hospital’s own prices. Ambulance bills too. Get a letter to send.')}</small>
        </a>
        <a className="choice" href="#/visits">
          <span>{t('I have a pile of bills from one visit')}</span>
          <small>{t('Put every bill, EOB and receipt in one place and see whom you really owe. Saved only on your phone.')}</small>
        </a>
        <a className="choice" href="#/prices">
          <span>{t('I want a price before care')}</span>
          <small>{t('What Tucson and Phoenix hospitals published for 50 common procedures.')}</small>
        </a>
      </div>
      <section className="card stack">
        <h2>{t('Why this matters')}</h2>
        <p>{t('41% of US adults have debt from medical or dental bills, and 44% of them did not pay a bill in full because they were not sure it was correct (KFF, 2022). Most people don’t know that nonprofit hospitals must offer financial assistance.')}</p>
        <p className="small muted">{t('Sources:')} <a href="https://www.kff.org/health-costs/kff-health-care-debt-survey/" target="_blank"
          rel="noreferrer">KFF Health Care Debt Survey</a>; <a href="https://www.irs.gov/charities-non-profits/billing-and-collections-section-501r6"
          target="_blank" rel="noreferrer">IRS section 501(r)</a>.</p>
      </section>
    </div>
  )
}
