import { createContext, useContext, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { ES } from './es'

// English text is the key; Spanish comes from es.ts. A missing translation falls back to English.
export type Lang = 'en' | 'es'
const Ctx = createContext<{ lang: Lang; setLang: (l: Lang) => void }>({ lang: 'en', setLang: () => {} })

function initial(): Lang {
  try {
    const saved = localStorage.getItem('cleartab-lang')
    if (saved === 'en' || saved === 'es') return saved
  } catch { /* storage blocked */ }
  return navigator.language?.toLowerCase().startsWith('es') ? 'es' : 'en'
}

export function LangProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(initial)
  useEffect(() => { document.documentElement.lang = lang }, [lang])
  const setLang = (l: Lang) => {
    setLangState(l)
    try { localStorage.setItem('cleartab-lang', l) } catch { /* storage blocked */ }
  }
  return <Ctx.Provider value={{ lang, setLang }}>{children}</Ctx.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export const useLang = () => useContext(Ctx)

// eslint-disable-next-line react-refresh/only-export-components
export function useT() {
  const { lang } = useContext(Ctx)
  return (s: string, vars?: Record<string, string | number>) => {
    let out = lang === 'es' ? (ES[s] ?? s) : s
    if (vars) for (const [k, v] of Object.entries(vars)) out = out.split(`{${k}}`).join(String(v))
    return out
  }
}
