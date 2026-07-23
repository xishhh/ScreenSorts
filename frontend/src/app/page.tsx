"use client"

import { useCallback, useEffect, useState } from "react"
import { SearchBar } from "@/components/search/search-bar"
import { ResultCard } from "@/components/search/result-card"
import { search as searchApi, explain as explainApi, fetchDemoStatus } from "@/lib/api"
import type { SearchResultItem, ExplainItem, DemoStatusResponse } from "@/lib/types"

export default function HomePage() {
  const [query, setQuery] = useState("")
  const [results, setResults] = useState<SearchResultItem[]>([])
  const [totalResults, setTotalResults] = useState(0)
  const [searchTiming, setSearchTiming] = useState<number | null>(null)
  const [searching, setSearching] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [searched, setSearched] = useState(false)

  const [explanations, setExplanations] = useState<Map<string, ExplainItem>>(new Map())
  const [explainingIds, setExplainingIds] = useState<Set<string>>(new Set())
  const [uploadLoading, setUploadLoading] = useState(false)

  const [demoStatus, setDemoStatus] = useState<DemoStatusResponse | null>(null)

  useEffect(() => {
    fetchDemoStatus()
      .then(setDemoStatus)
      .catch(() => {})
  }, [])

  const handleSearch = useCallback(async (q: string) => {
    setQuery(q)
    setSearching(true)
    setError(null)
    setExplanations(new Map())
    setSearched(true)
    try {
      const data = await searchApi(q, 10, 0)
      setResults(data.results)
      setTotalResults(data.total_results)
      setSearchTiming(data.timing.total_ms)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Search failed")
      setResults([])
      setTotalResults(0)
    } finally {
      setSearching(false)
    }
  }, [])

  const handleExplain = useCallback(
    async (imageId: string) => {
      if (!query) return
      setExplainingIds((prev) => new Set(prev).add(imageId))
      try {
        const data = await explainApi(query, results.length, 0)
        const item = data.explanations.find((e) => e.image_id === imageId)
        if (item) {
          setExplanations((prev) => {
            const next = new Map(prev)
            next.set(imageId, item)
            return next
          })
        }
      } catch {
        /* silent */
      } finally {
        setExplainingIds((prev) => {
          const next = new Set(prev)
          next.delete(imageId)
          return next
        })
      }
    },
    [query, results.length]
  )

  const handleUpload = useCallback(async (files: FileList) => {
    setUploadLoading(true)
    // Future: upload to backend, then refresh search
    console.log(`Received ${files.length} file(s)`)
    setUploadLoading(false)
  }, [])

  const hasResults = results.length > 0
  const compact = hasResults || searched

  return (
    <div className="mx-auto flex max-w-7xl flex-col px-4 pb-12 sm:px-6">
      <SearchBar
        onSearch={handleSearch}
        loading={searching}
        compact={compact && !error}
        onFilesSelected={handleUpload}
        uploadLoading={uploadLoading}
      />

      {error && (
        <div className="mx-auto mt-6 max-w-2xl rounded-lg border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
          {error}
        </div>
      )}

      {searching && (
        <div className="mt-8 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="animate-pulse space-y-3 rounded-xl border p-3">
              <div className="aspect-[4/3] rounded-lg bg-muted" />
              <div className="h-3 w-3/4 rounded bg-muted" />
              <div className="h-2 w-full rounded bg-muted" />
              <div className="h-8 w-full rounded-lg bg-muted" />
            </div>
          ))}
        </div>
      )}

      {searched && !searching && results.length === 0 && !error && (
        <div className="mt-16 flex flex-col items-center gap-2 text-center">
          <p className="text-lg font-medium">No results found</p>
          <p className="text-sm text-muted-foreground">
            Try a different search query or upload your own screenshots.
          </p>
        </div>
      )}

      {hasResults && !searching && (
        <div className="mt-6 space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              {totalResults} result{totalResults !== 1 ? "s" : ""}
              {searchTiming !== null && ` in ${searchTiming}ms`}
            </p>
          </div>
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {results.map((result) => (
              <ResultCard
                key={result.image_id}
                result={result}
                explanation={explanations.get(result.image_id) || null}
                onExplain={handleExplain}
                explaining={explainingIds.has(result.image_id)}
              />
            ))}
          </div>
        </div>
      )}

      {!searched && !searching && !error && (
        <div className="mt-12 flex flex-col items-center gap-2 text-center text-muted-foreground">
          <p className="text-sm">
            Search across thousands of pre-indexed demo screenshots
          </p>
          {demoStatus && (
            <div className="mt-3 flex flex-wrap items-center justify-center gap-2">
              <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium ${
                demoStatus.ready
                  ? "bg-green-500/10 text-green-600 dark:text-green-400"
                  : "bg-yellow-500/10 text-yellow-600 dark:text-yellow-400"
              }`}>
                <span className={`inline-block size-1.5 rounded-full ${
                  demoStatus.ready ? "bg-green-500" : "bg-yellow-500"
                }`} />
                {demoStatus.ready ? "Demo Ready" : "Incomplete"}
              </span>
              {demoStatus.ready && (
                <>
                  <span className="text-xs text-muted-foreground">
                    {demoStatus.screenshot_count} screenshots
                  </span>
                  <span className="text-xs text-muted-foreground">·</span>
                  <span className="text-xs text-muted-foreground">
                    {demoStatus.dataset_count} datasets
                  </span>
                </>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
