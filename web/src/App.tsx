import { useEffect, useState } from 'react'
import Assistance from './pages/Assistance'
import BillCheck from './pages/BillCheck'
import Home from './pages/Home'
import Prices from './pages/Prices'

type Route = 'home' | 'bill' | 'help' | 'prices'

const routeFromHash = (): Route => {
  const h = window.location.hash.replace('#/', '')
  return h === 'bill' || h === 'help' || h === 'prices' ? h : 'home'
}

export default function App() {
  const [route, setRoute] = useState<Route>(routeFromHash)
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
          {link('help', 'Lower my bill')}
          {link('bill', 'Check my bill')}
          {link('prices', 'Prices')}
        </nav>
      </header>
      <main>
        {route === 'home' && <Home />}
        {route === 'bill' && <BillCheck />}
        {route === 'help' && <Assistance />}
        {route === 'prices' && <Prices />}
      </main>
      <footer>
        <p>ClearTab compares what you enter with published rules and prices. It is not legal or medical advice.
          Nothing you enter is stored, and there are no accounts.</p>
        <p>Free and open source. University of Arizona ISTA 498 capstone, Team Trace, 2026.</p>
      </footer>
    </div>
  )
}
