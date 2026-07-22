"use client"

import { useState } from "react"
import { imageUrl } from "@/lib/api"
import type { SearchResultItem, ExplainItem } from "@/lib/types"

interface ResultCardProps {
  result: SearchResultItem
  explanation?: ExplainItem | null
  onExplain: (imageId: string) => void
  explaining: boolean
}

export function ResultCard({
  result,
  explanation,
  onExplain,
  explaining,
}: ResultCardProps) {
  const [expanded, setExpanded] = useState(false)
  const scorePct = Math.round(result.score * 100)
  const [loaded, setLoaded] = useState(false)

  return (
    <div className="group/card relative overflow-hidden rounded-xl bg-card shadow-sm ring-1 ring-foreground/5 transition-all hover:shadow-md">
      <div className="relative aspect-[4/3] bg-muted">
        {!loaded && (
          <div className="absolute inset-0 animate-pulse bg-muted" />
        )}
        <img
          src={imageUrl(result.image_path)}
          alt={result.image_id}
          className={`h-full w-full object-contain transition-opacity duration-300 ${loaded ? "opacity-100" : "opacity-0"}`}
          loading="lazy"
          onLoad={() => setLoaded(true)}
        />

        <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent p-3 pt-8 opacity-0 transition-opacity group-hover/card:opacity-100">
          <div className="flex items-center justify-between gap-2">
            <span className="truncate text-xs font-mono text-white/90">
              {result.image_id}
            </span>
            <div className="flex items-center gap-2">
              <span className="rounded-full border border-white/20 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-white/80">
                {result.source_dataset}
              </span>
              <span className="text-xs font-semibold text-white">
                {scorePct}%
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-2 p-3">
        <p className="line-clamp-2 text-xs leading-relaxed text-muted-foreground">
          {result.text || "(no OCR text)"}
        </p>

        {explanation && (
          <div className="rounded-lg bg-muted/60 p-2.5 text-xs leading-relaxed text-foreground">
            <div className="mb-1 flex items-center gap-1.5">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="size-3.5 text-indigo-500"
              >
                <path d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09Z M18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 0 0-2.455 2.456Z" />
              </svg>
              <span className="font-medium text-foreground">AI Explanation</span>
              {explanation.cache_hit && (
                <span className="rounded bg-indigo-100 px-1.5 py-0.5 text-[10px] font-medium text-indigo-700 dark:bg-indigo-900 dark:text-indigo-300">
                  cached
                </span>
              )}
            </div>
            <p>
              {expanded
                ? explanation.explanation
                : explanation.explanation.length > 180
                  ? explanation.explanation.slice(0, 180) + "…"
                  : explanation.explanation}
            </p>
            {explanation.explanation.length > 180 && (
              <button
                onClick={() => setExpanded(!expanded)}
                className="mt-1 text-indigo-600 hover:underline dark:text-indigo-400"
              >
                {expanded ? "Show less" : "Show more"}
              </button>
            )}
          </div>
        )}

        <button
          onClick={() => onExplain(result.image_id)}
          disabled={explaining}
          className="flex w-full items-center justify-center gap-1.5 rounded-lg border py-1.5 text-xs font-medium transition-colors hover:bg-muted disabled:opacity-50"
        >
          {explaining ? (
            <>
              <svg className="size-3.5 animate-spin" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Explaining…
            </>
          ) : (
            <>
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="size-3.5"
              >
                <path d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09Z M18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 0 0-2.455 2.456Z" />
              </svg>
              Explain
            </>
          )}
        </button>
      </div>
    </div>
  )
}
