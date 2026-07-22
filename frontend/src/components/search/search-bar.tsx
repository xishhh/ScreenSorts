"use client"

import { type FormEvent, useState } from "react"
import { UploadButton } from "./upload-button"

const EXAMPLES = [
  "login page",
  "python code editor",
  "dashboard chart",
  "settings menu",
  "data table",
]

interface SearchBarProps {
  onSearch: (query: string) => void
  loading: boolean
  compact?: boolean
  onFilesSelected: (files: FileList) => void
  uploadLoading: boolean
}

export function SearchBar({
  onSearch,
  loading,
  compact,
  onFilesSelected,
  uploadLoading,
}: SearchBarProps) {
  const [query, setQuery] = useState("")

  function handleSubmit(e?: FormEvent) {
    e?.preventDefault()
    const trimmed = query.trim()
    if (trimmed) onSearch(trimmed)
  }

  function handleExample(example: string) {
    setQuery(example)
    onSearch(example)
  }

  return (
    <div className={`flex w-full flex-col items-center gap-4 ${compact ? "" : "pt-20"}`}>
      <form
        onSubmit={handleSubmit}
        className={`relative flex w-full max-w-2xl items-center rounded-full border bg-background shadow-sm transition-all focus-within:border-indigo-400 focus-within:ring-2 focus-within:ring-indigo-400/20 ${
          compact ? "h-11" : "h-14"
        }`}
      >
        <span className="pl-4 text-muted-foreground">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={compact ? "size-4" : "size-5"}
          >
            <circle cx="11" cy="11" r="8" />
            <path d="m21 21-4.3-4.3" />
          </svg>
        </span>

        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Describe the screenshot you're looking for…"
          className={`flex-1 border-0 bg-transparent px-3 outline-none placeholder:text-muted-foreground/60 ${
            compact ? "text-sm" : "text-base"
          }`}
          disabled={loading}
          autoFocus={!compact}
          onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
        />

        <div className="pr-2">
          <UploadButton onFilesSelected={onFilesSelected} uploading={uploadLoading} />
        </div>
      </form>

      {!compact && (
        <div className="flex flex-wrap justify-center gap-2">
          {EXAMPLES.map((example) => (
            <button
              key={example}
              type="button"
              onClick={() => handleExample(example)}
              className="rounded-full border px-3 py-1 text-xs text-muted-foreground transition-colors hover:border-foreground/30 hover:text-foreground"
            >
              {example}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
