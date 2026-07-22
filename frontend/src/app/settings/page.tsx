"use client"

import { type FormEvent, useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

const STORAGE_KEY = "screensorts_settings"

interface Settings {
  apiUrl: string
  topK: number
}

function load(): Settings {
  if (typeof window === "undefined") return { apiUrl: "http://localhost:8000", topK: 10 }
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) return JSON.parse(raw)
  } catch {
    /* ignore */
  }
  return { apiUrl: "http://localhost:8000", topK: 10 }
}

function save(s: Settings) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(s))
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<Settings>(load)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    setSettings(load())
  }, [])

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    save(settings)
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  return (
    <div className="mx-auto max-w-lg px-4 pt-12 sm:px-6">
      <div className="mb-6">
        <h1 className="text-xl font-bold tracking-tight">Settings</h1>
        <p className="text-sm text-muted-foreground">Configure your search preferences</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>Backend</CardTitle>
            <CardDescription>API server URL</CardDescription>
          </CardHeader>
          <CardContent>
            <input
              type="text"
              value={settings.apiUrl}
              onChange={(e) => setSettings((s) => ({ ...s, apiUrl: e.target.value }))}
              className="flex h-10 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Results</CardTitle>
            <CardDescription>Default number of results per search</CardDescription>
          </CardHeader>
          <CardContent>
            <input
              type="number"
              min={1}
              max={100}
              value={settings.topK}
              onChange={(e) =>
                setSettings((s) => ({
                  ...s,
                  topK: Math.max(1, Math.min(100, Number(e.target.value))),
                }))
              }
              className="flex h-10 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            />
          </CardContent>
        </Card>

        <Button type="submit">{saved ? "Saved!" : "Save Settings"}</Button>
      </form>
    </div>
  )
}
