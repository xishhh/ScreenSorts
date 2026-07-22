"use client"

import { useRef, useState } from "react"

interface UploadButtonProps {
  onFilesSelected: (files: FileList) => void
  uploading: boolean
}

export function UploadButton({ onFilesSelected, uploading }: UploadButtonProps) {
  const [open, setOpen] = useState(false)
  const imageRef = useRef<HTMLInputElement>(null)
  const folderRef = useRef<HTMLInputElement>(null)

  function handleImage() {
    setOpen(false)
    imageRef.current?.click()
  }

  function handleFolder() {
    setOpen(false)
    folderRef.current?.click()
  }

  return (
    <>
      <input
        ref={imageRef}
        type="file"
        accept="image/png,image/jpeg,image/jpg,image/webp"
        multiple
        className="hidden"
        onChange={(e) => e.target.files && onFilesSelected(e.target.files)}
      />
      <input
        ref={folderRef}
        type="file"
        // @ts-expect-error webkitdirectory is not in the TS types
        webkitdirectory=""
        multiple
        className="hidden"
        onChange={(e) => e.target.files && onFilesSelected(e.target.files)}
      />

      <div className="relative">
        <button
          type="button"
          onClick={() => setOpen(!open)}
          disabled={uploading}
          className="inline-flex size-8 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-violet-500 text-white shadow-sm transition-all hover:scale-105 hover:shadow-md active:scale-95 disabled:opacity-50"
          aria-label="Upload"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="size-4">
            <path d="M5 12h14" />
            <path d="M12 5v14" />
          </svg>
        </button>

        {open && (
          <>
            <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
            <div className="absolute right-0 top-10 z-50 min-w-44 overflow-hidden rounded-xl border bg-popover p-1 shadow-lg">
              <button
                onClick={handleImage}
                className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm transition-colors hover:bg-muted"
              >
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="size-4">
                  <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                  <circle cx="8.5" cy="8.5" r="1.5" />
                  <polyline points="21 15 16 10 5 21" />
                </svg>
                Upload Image
              </button>
              <button
                onClick={handleFolder}
                className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm transition-colors hover:bg-muted"
              >
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="size-4">
                  <path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z" />
                </svg>
                Upload Folder
              </button>
            </div>
          </>
        )}
      </div>
    </>
  )
}
