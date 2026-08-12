// 텍스트를 렌더링하면서 탐지 스팬은 색상 밑줄 오버레이로, 확정 라벨은 별도의
// 박스 스타일로 표시한다. 서로 다른 모듈의 겹치는 탐지는 여러 겹의 밑줄로 쌓인다.

import { useEffect, useRef, useState } from 'react'
import type { CSSProperties, MouseEvent as ReactMouseEvent } from 'react'
import { createPortal } from 'react-dom'
import type { Segment } from '../spans'
import { computeSegments, toCodepoints } from '../spans'
import { PII_TYPES } from '../api'
import type { DetectionSpan, Label, PiiType } from '../api'
import { selectionToTextRange } from '../selection'

interface Props {
  text: string
  spans: DetectionSpan[]
  labels: Label[]
  colorMap: Record<string, string>
  onAddLabel: (start: number, end: number, type: PiiType, text: string) => void
  onDeleteLabel: (label: Label) => void
  onUpdateLabelType: (label: Label, type: PiiType) => void
}

interface PendingSelection {
  start: number
  end: number
  text: string
  left: number
  top: number
}

interface LabelPopover {
  labels: Label[]
  left: number
  top: number
}

function segmentStyle(seg: Segment, colorMap: Record<string, string>): CSSProperties {
  const style: CSSProperties = {}
  // 겹친 밑줄: 덮고 있는 모듈마다 3px 막대 하나씩 위로 쌓는다.
  const moduleColors = [...new Set(seg.spans.map((s) => colorMap[s.module] ?? '#888'))]
  if (moduleColors.length > 0) {
    style.boxShadow = moduleColors
      .map((c, i) => `inset 0 -${(i + 1) * 3}px 0 -${i * 3}px ${c}`)
      .join(', ')
    style.cursor = 'pointer'
    style.paddingBottom = `${moduleColors.length * 3}px`
  }
  // 확정 라벨: 구분되는 실선 박스.
  if (seg.labels.length > 0) {
    style.backgroundColor = 'rgba(250, 204, 21, 0.22)'
    style.outline = '1.5px solid #facc15'
    style.borderRadius = '2px'
  }
  return style
}

function tooltip(seg: Segment): string {
  const parts: string[] = []
  for (const l of seg.labels) {
    parts.push(`확정 · ${l.type} · "${l.text}"`)
  }
  for (const s of seg.spans) {
    const score = s.score == null ? '' : ` (${s.score.toFixed(3)})`
    parts.push(`${s.module} · ${s.type}${score} · "${s.text}"`)
  }
  return parts.join('\n')
}

export default function HighlightViewer({
  text,
  spans,
  labels,
  colorMap,
  onAddLabel,
  onDeleteLabel,
  onUpdateLabelType,
}: Props) {
  const viewerRef = useRef<HTMLDivElement>(null)
  const popoverRef = useRef<HTMLDivElement>(null)
  const suppressClickRef = useRef(false)
  const [pending, setPending] = useState<PendingSelection | null>(null)
  const [labelPopover, setLabelPopover] = useState<LabelPopover | null>(null)
  const [type, setType] = useState<PiiType>('NAME')

  function closeSelection() {
    setPending(null)
    setLabelPopover(null)
    window.getSelection()?.removeAllRanges()
  }

  useEffect(() => {
    setPending(null)
  }, [text])

  useEffect(() => {
    if (!pending && !labelPopover) return

    const focusTimer = window.setTimeout(() => {
      popoverRef.current?.querySelector('select')?.focus()
    }, 0)

    function handlePointerDown(event: PointerEvent) {
      const target = event.target as Node
      if (popoverRef.current?.contains(target) || viewerRef.current?.contains(target)) return
      closeSelection()
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') closeSelection()
    }

    function handleViewportChange() {
      closeSelection()
    }

    document.addEventListener('pointerdown', handlePointerDown, true)
    document.addEventListener('keydown', handleKeyDown)
    window.addEventListener('resize', handleViewportChange)
    window.addEventListener('scroll', handleViewportChange, true)
    return () => {
      window.clearTimeout(focusTimer)
      document.removeEventListener('pointerdown', handlePointerDown, true)
      document.removeEventListener('keydown', handleKeyDown)
      window.removeEventListener('resize', handleViewportChange)
      window.removeEventListener('scroll', handleViewportChange, true)
    }
  }, [pending, labelPopover])

  function handleMouseUp() {
    const root = viewerRef.current
    const selection = window.getSelection()
    if (!root || !selection) return
    const selected = selectionToTextRange(root, selection, text)
    if (!selected) return

    const rect = selection.getRangeAt(0).getBoundingClientRect()
    const popoverWidth = Math.min(320, window.innerWidth - 24)
    const left = Math.max(
      12,
      Math.min(rect.left + rect.width / 2 - popoverWidth / 2, window.innerWidth - popoverWidth - 12),
    )
    const top = Math.max(12, Math.min(rect.bottom + 8, window.innerHeight - 90))
    suppressClickRef.current = true
    setLabelPopover(null)
    setPending({ ...selected, left, top })
  }

  function handleSegmentClick(event: ReactMouseEvent, segment: Segment) {
    if (suppressClickRef.current) {
      suppressClickRef.current = false
      event.preventDefault()
      return
    }
    if (segment.labels.length === 0) return
    const rect = event.currentTarget.getBoundingClientRect()
    const popoverWidth = Math.min(320, window.innerWidth - 24)
    const left = Math.max(
      12,
      Math.min(rect.left + rect.width / 2 - popoverWidth / 2, window.innerWidth - popoverWidth - 12),
    )
    const top = Math.max(12, Math.min(rect.bottom + 8, window.innerHeight - 120))
    setPending(null)
    setLabelPopover({ labels: segment.labels, left, top })
  }

  function confirmSelection() {
    if (!pending) return
    onAddLabel(pending.start, pending.end, type, pending.text)
    closeSelection()
  }

  if (!text) {
    return <div className="empty">텍스트를 입력하거나 샘플을 선택하세요.</div>
  }

  const cps = toCodepoints(text)
  const segments = computeSegments(cps, spans, labels)

  return (
    <>
      <div
        className="viewer viewer-selectable"
        aria-label="탐지 및 라벨링 뷰어"
        ref={viewerRef}
        onMouseDown={() => (pending || labelPopover) && closeSelection()}
        onMouseUp={handleMouseUp}
      >
        {segments.map((seg, i) => {
          const active = seg.spans.length > 0 || seg.labels.length > 0
          return (
          <span
            key={i}
            className={active ? 'seg' : undefined}
            style={active ? segmentStyle(seg, colorMap) : undefined}
            title={active ? tooltip(seg) : undefined}
            data-segment-start={seg.start}
            data-segment-end={seg.end}
            onClick={(event) => handleSegmentClick(event, seg)}
          >
            {seg.text}
          </span>
          )
        })}
      </div>
      <div className="hint">드래그하여 라벨 추가 · 노란 확정 라벨을 클릭하여 수정 또는 삭제</div>
      {pending &&
        createPortal(
          <div
            className="selection-popover"
            ref={popoverRef}
            role="dialog"
            aria-label="선택 영역 라벨 추가"
            style={{ left: pending.left, top: pending.top }}
          >
            <span className="pending-text" title={pending.text}>
              “{pending.text}” [{pending.start}, {pending.end})
            </span>
            <div className="selection-popover-actions">
              <select
                value={type}
                aria-label="개인정보 유형"
                onChange={(event) => setType(event.target.value as PiiType)}
              >
                {PII_TYPES.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
              <button className="primary sm" onClick={confirmSelection}>
                확정 추가
              </button>
              <button className="sm" onClick={closeSelection}>
                취소
              </button>
            </div>
          </div>,
          document.body,
        )}
      {labelPopover &&
        createPortal(
          <div
            className="selection-popover"
            ref={popoverRef}
            role="dialog"
            aria-label="확정 라벨 관리"
            style={{ left: labelPopover.left, top: labelPopover.top }}
          >
            <strong>확정 라벨</strong>
            <ul className="label-popover-list">
              {labelPopover.labels.map((label) => (
                <li key={`${label.start}-${label.end}-${label.type}`}>
                  <span className="pending-text" title={label.text}>“{label.text}”</span>
                  <select
                    value={label.type}
                    aria-label={`${label.text} 개인정보 유형`}
                    onChange={(event) => {
                      onUpdateLabelType(label, event.target.value as PiiType)
                      closeSelection()
                    }}
                  >
                    {PII_TYPES.map((item) => (
                      <option key={item} value={item}>{item}</option>
                    ))}
                  </select>
                  <button
                    className="danger sm"
                    onClick={() => {
                      onDeleteLabel(label)
                      closeSelection()
                    }}
                  >
                    삭제
                  </button>
                </li>
              ))}
            </ul>
          </div>,
          document.body,
        )}
    </>
  )
}
