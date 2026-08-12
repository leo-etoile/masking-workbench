// codepoint 기준 스팬 유틸리티.
//
// 백엔드는 [start, end) 에 Python codepoint 인덱스를 사용한다. astral(비 BMP)
// 문자가 있어도 하이라이트 렌더링 정렬이 어긋나지 않도록, 원시 JS 문자열(UTF-16)
// 인덱스가 아니라 codepoint 배열(Array.from(text)) 위에서 연산한다.

import type { DetectionSpan, Label } from './api'

export function toCodepoints(text: string): string[] {
  return Array.from(text)
}

export function sliceCodepoints(cps: string[], start: number, end: number): string {
  return cps.slice(start, end).join('')
}

// (DOM Selection API가 반환하는) UTF-16 코드 유닛 오프셋을 `text` 내 codepoint
// 오프셋으로 변환한다.
export function utf16ToCodepoint(text: string, utf16Offset: number): number {
  return Array.from(text.slice(0, utf16Offset)).length
}

export interface Segment {
  start: number
  end: number
  text: string
  spans: DetectionSpan[] // 이 세그먼트를 덮는 탐지 스팬들
  labels: Label[] // 이 세그먼트를 덮는 확정 라벨들
}

// 모든 스팬/라벨 경계에서 전체 텍스트를 연속된 세그먼트로 분할한다.
// 각 세그먼트는 자신을 덮는 탐지 스팬과 확정 라벨을 기록하므로, 서로 다른 모듈의
// 겹치는 탐지 결과가 별개의 조각으로 렌더링된다.
export function computeSegments(
  cps: string[],
  spans: DetectionSpan[],
  labels: Label[],
): Segment[] {
  const len = cps.length
  const boundarySet = new Set<number>([0, len])
  for (const s of spans) {
    if (s.start >= 0 && s.start <= len) boundarySet.add(s.start)
    if (s.end >= 0 && s.end <= len) boundarySet.add(s.end)
  }
  for (const l of labels) {
    if (l.start >= 0 && l.start <= len) boundarySet.add(l.start)
    if (l.end >= 0 && l.end <= len) boundarySet.add(l.end)
  }
  const boundaries = [...boundarySet].sort((a, b) => a - b)

  const segments: Segment[] = []
  for (let i = 0; i < boundaries.length - 1; i++) {
    const start = boundaries[i]
    const end = boundaries[i + 1]
    if (end <= start) continue
    const coveringSpans = spans.filter((s) => s.start <= start && s.end >= end)
    const coveringLabels = labels.filter((l) => l.start <= start && l.end >= end)
    segments.push({
      start,
      end,
      text: sliceCodepoints(cps, start, end),
      spans: coveringSpans,
      labels: coveringLabels,
    })
  }
  return segments
}
