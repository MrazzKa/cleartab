import { useEffect, useState } from 'react'
import Assistance from './pages/Assistance'
import BillCheck from './pages/BillCheck'
import Home from './pages/Home'
import Prices from './pages/Prices'
import { useLang, useT } from './i18n'

type Route = 'home' | 'bill' | 'help' | 'prices'

const routeFromHash = (): Route => {
  const h = window.location.hash.replace('#/', '')
  return h === 'bill' || h === 'help' || h === 'prices' ? h : 'home'
}

export default function App() {
  const [route, setRoute] = useState<Route>(routeFromHash)
  const t = useT()
  const { lang, setLang } = useLang()
  useEffect(() => {
    const on = () => { setRoute(routeFromHash()); window.scrollTo(0, 0) }
    window.addEventListener('hashchange', on)
    return () => window.removeEventListener('hashchange', on)
  }, [])

  const link = (r: Route, label: string) => (
    <a href={r === 'home' ? '#/' : `#/${r}`} aria-current={route === r ? 'page' : undefined}>{label}</a>
  )

  return (
    <div className="shell">
      <header className="topbar">
        <a className="brand" href="#/">Clear<span>Tab</span></a>
        <nav aria-label="Main">
          {link('help', t('Lower my bill'))}
          {link('bill', t('Check my bill'))}
          {link('prices', t('Prices'))}
          <button type="button" className="lang" onClick={() => setLang(lang === 'en' ? 'es' : 'en')}
            aria-label={lang === 'en' ? 'Ver en español' : 'View in English'}>{lang === 'en' ? 'Español' : 'English'}</button>
        </nav>
      </header>
      <main>
        {route === 'home' && <Home />}
        {route === 'bill' && <BillCheck />}
        {route === 'help' && <Assistance />}
        {route === 'prices' && <Prices />}
      </main>
      <footer>
        <p>{t('ClearTab compares what you enter with published rules and prices. It is not legal or medical advice. Nothing you enter is stored, and there are no accounts.')}</p>
        <p>{t('Free and open source. University of Arizona ISTA 498 capstone, Team Trace, 2026.')}</p>
      </footer>
    </div>
  )
}
