// API 계층: 마스킹 워크벤치 백엔드용 타입 및 fetch 헬퍼.
// 백엔드는 http://localhost:8000 에서 동작하며, vite dev 프록시가 /api/* 를 그쪽으로 전달한다.

export const PII_TYPES = [
  'RRN',
  'PHONE',
  'DATE',
  'NAME',
  'ADDRESS',
  'EMAIL',
  'HOSPITAL',
] as const

export type PiiType = (typeof PII_TYPES)[number]

export interface ModuleInfo {
  id: string
  display_name: string
  requires_external_network: boolean
  description: string
}

// 탐지 스팬은 [start, end) 에 대해 Python codepoint 인덱스를 사용한다.
export interface DetectionSpan {
  start: number
  end: number
  type: string
  module: string
  text: string
  score: number | null
}

// 사람이 확정한 라벨. module/score 없음.
export interface Label {
  start: number
  end: number
  type: string
  text: string
}

export interface Sample {
  id: string
  text: string
  synthetic: true
}

export interface DetectResponse {
  results: Record<string, DetectionSpan[]>
  module_errors: Record<string, string>
  blocked: string[]
}

export interface ModuleMetrics {
  precision: number
  recall: number
  f1: number
  tp: number
  fp: number
  fn: number
}

export interface EvaluateResponse {
  metrics: Record<string, ModuleMetrics>
}

export interface SavedDocument {
  doc_id: string
  updated_at: string
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
  })
  if (!res.ok) {
    let detail = ''
    try {
      detail = await res.text()
    } catch {
      // 응답 본문 읽기 실패는 무시
    }
    throw new Error(`${res.status} ${res.statusText}${detail ? `: ${detail}` : ''}`)
  }
  return (await res.json()) as T
}

export function getModules(): Promise<{ modules: ModuleInfo[] }> {
  return request('/api/modules')
}

export function detect(body: {
  text: string
  module_ids: string[]
  synthetic: boolean
}): Promise<DetectResponse> {
  return request('/api/detect', { method: 'POST', body: JSON.stringify(body) })
}

export function getSamples(): Promise<{ samples: Sample[] }> {
  return request('/api/samples')
}

export function saveLabels(body: {
  doc_id: string
  text: string
  labels: Label[]
}): Promise<{ ok: true }> {
  return request('/api/labels', { method: 'POST', body: JSON.stringify(body) })
}

export function listDocuments(): Promise<{ documents: SavedDocument[] }> {
  return request('/api/labels')
}

export function getDocument(
  docId: string,
): Promise<{ doc_id: string; text: string; labels: Label[]; updated_at: string }> {
  return request(`/api/labels/${encodeURIComponent(docId)}`)
}

export function evaluate(body: {
  labels: Label[]
  detections: Record<string, DetectionSpan[]>
}): Promise<EvaluateResponse> {
  return request('/api/evaluate', { method: 'POST', body: JSON.stringify(body) })
}
