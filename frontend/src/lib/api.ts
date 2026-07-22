import type { SearchResponse, ExplainResponse } from "@/lib/types"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

function imageUrl(imagePath: string): string {
  const idx = imagePath.indexOf("data\\")
  if (idx !== -1) {
    return imagePath.slice(idx).replace(/\\/g, "/")
  }
  const idx2 = imagePath.indexOf("data/")
  if (idx2 !== -1) {
    return imagePath.slice(idx2)
  }
  return imagePath
}

export { imageUrl }

export async function search(
  query: string,
  topK = 10,
  threshold = 0.0
): Promise<SearchResponse> {
  const res = await fetch(`${API_BASE}/api/v1/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, top_k: topK, threshold }),
  })
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(error.detail || `Search failed (${res.status})`)
  }
  return res.json()
}

export async function explain(
  query: string,
  topK = 10,
  threshold = 0.0
): Promise<ExplainResponse> {
  const res = await fetch(`${API_BASE}/api/v1/explain`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, top_k: topK, threshold }),
  })
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(error.detail || `Explain failed (${res.status})`)
  }
  return res.json()
}
