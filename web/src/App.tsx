import { useEffect, useState } from 'react'
import Icon from './icons'
import type { IconName } from './icons'
import Assistance from './pages/Assistance'
import BillCheck from './pages/BillCheck'
import Home from './pages/Home'
import Prices from './pages/Prices'
import Visits from './pages/Visits'
import { useLang, useT } from './i18n'

type Route = 'home' | 'bill' | 'help' | 'prices' | 'visits'

const routeFromHash = (): Route => {
  const h = window.location.hash.replace('#/', '')
  return h === 'bill' || h === 'help' || h === 'prices' || h === 'visits' ? h : 'home'
}

const TABS: [Route, IconName, string][] = [
  ['home', 'home', 'Home'], ['bill', 'check', 'Check my bill'], ['help', 'heart', 'Lower my bill'],
  ['visits', 'layers', 'My visits'], ['prices', 'tag', 'Prices'],
]

export default function App() {
  const [route, setRoute] = useState<Route>(routeFromHash)
  const t = useT()
  const { lang, setLang } = useLang()
  useEffect(() => {
    const on = () => { setRoute(routeFromHash()); window.scrollTo(0, 0) }
    window.addEventListener('hashchange', on)
    return () => window.removeEventListener('hashchange', on)
  }, [])

  const tabs = (cls: string) => (
    <nav className={cls} aria-label={t('Main')}>
      {TABS.map(([r, icon, label]) => (
        <a key={r} href={r === 'home' ? '#/' : `#/${r}`} aria-current={route === r ? 'page' : undefined}>
          <Icon name={icon} /><span>{t(label)}</span>
        </a>
      ))}
    </nav>
  )

  return (
    <>
      <header className="topbar">
        <div className="topbar-in">
          <a className="brand" href="#/"><span className="logo" aria-hidden="true"><Icon name="receipt" size={18} /></span>Clear<span>Tab</span></a>
          {tabs('nav-top')}
          <button type="button" className="lang" onClick={() => setLang(lang === 'en' ? 'es' : 'en')}
            aria-label={lang === 'en' ? 'Ver en español' : 'View in English'}>
            <Icon name="globe" size={18} />{lang === 'en' ? 'Español' : 'English'}
          </button>
        </div>
      </header>
      <div className="shell">
        <main>
          {route === 'home' && <Home />}
          {route === 'bill' && <BillCheck />}
          {route === 'help' && <Assistance />}
          {route === 'prices' && <Prices />}
          {route === 'visits' && <Visits />}
        </main>
        <footer>
          <p>{t('ClearTab compares what you enter with published rules and prices. It is not legal or medical advice. Nothing you enter is stored, and there are no accounts.')}</p>
          <p>{t('Free and open source. University of Arizona ISTA 498 capstone, Team Trace, 2026.')}</p>
        </footer>
      </div>
      {tabs('nav-bottom')}
    </>
  )
}
