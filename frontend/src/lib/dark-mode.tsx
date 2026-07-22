"use client"

import { createContext, useCallback, useContext, useEffect, useState } from "react"

type DarkModeContext = {
  isDark: boolean
  toggle: () => void
}

const Ctx = createContext<DarkModeContext>({ isDark: false, toggle: () => {} })

export function DarkModeProvider({ children }: { children: React.ReactNode }) {
  const [isDark, setIsDark] = useState(false)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    const stored = localStorage.getItem("screensorts_dark")
    const preferDark = window.matchMedia("(prefers-color-scheme: dark)").matches
    const dark = stored !== null ? stored === "true" : preferDark
    setIsDark(dark)
    document.documentElement.classList.toggle("dark", dark)
    setMounted(true)
  }, [])

  const toggle = useCallback(() => {
    setIsDark((prev) => {
      const next = !prev
      localStorage.setItem("screensorts_dark", String(next))
      document.documentElement.classList.toggle("dark", next)
      return next
    })
  }, [])

  if (!mounted) {
    return <>{children}</>
  }

  return <Ctx.Provider value={{ isDark, toggle }}>{children}</Ctx.Provider>
}

export function useDarkMode() {
  return useContext(Ctx)
}
