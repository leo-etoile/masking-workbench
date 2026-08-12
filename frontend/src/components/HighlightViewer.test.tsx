import { act } from 'react'
import { createRoot } from 'react-dom/client'
import type { Root } from 'react-dom/client'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { DetectionSpan } from '../api'
import HighlightViewer from './HighlightViewer'

(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true

const detection: DetectionSpan = {
  start: 0,
  end: 3,
  type: 'NAME',
  module: 'rule_test',
  text: '홍길동',
  score: null,
}

function selectionFor(node: Node, start: number, end: number): Selection {
  return {
    anchorNode: node,
    anchorOffset: start,
    focusNode: node,
    focusOffset: end,
    isCollapsed: false,
    rangeCount: 1,
    getRangeAt: () => ({
      getBoundingClientRect: () => new DOMRect(20, 30, 60, 18),
    }),
    removeAllRanges: vi.fn(),
  } as unknown as Selection
}

describe('HighlightViewer selection interaction', () => {
  let host: HTMLDivElement
  let root: Root

  beforeEach(() => {
    host = document.createElement('div')
    document.body.append(host)
    root = createRoot(host)
  })

  afterEach(() => {
    act(() => root.unmount())
    document.body.replaceChildren()
    vi.restoreAllMocks()
  })

  it('opens a selection popover, suppresses the drag click, and confirms a label', () => {
    const onAddLabel = vi.fn()
    act(() => {
      root.render(
        <HighlightViewer
          text="홍길동 내원"
          spans={[detection]}
          labels={[]}
          colorMap={{ rule_test: '#38bdf8' }}
          onAddLabel={onAddLabel}
          onDeleteLabel={vi.fn()}
          onUpdateLabelType={vi.fn()}
        />,
      )
    })

    const detectedSegment = host.querySelector<HTMLElement>('[data-segment-start="0"]')!
    const textNode = detectedSegment.firstChild as Text
    vi.spyOn(window, 'getSelection').mockReturnValue(selectionFor(textNode, 0, 2))

    act(() => detectedSegment.dispatchEvent(new MouseEvent('mouseup', { bubbles: true })))
    act(() => detectedSegment.dispatchEvent(new MouseEvent('click', { bubbles: true })))

    expect(document.querySelector('[role="dialog"]')).not.toBeNull()

    const confirm = [...document.querySelectorAll('button')].find(
      (button) => button.textContent === '확정 추가',
    )!
    act(() => confirm.dispatchEvent(new MouseEvent('click', { bubbles: true })))

    expect(onAddLabel).toHaveBeenCalledWith(0, 2, 'NAME', '홍길')
    expect(document.querySelector('[role="dialog"]')).toBeNull()
  })

  it('opens confirmed-label management on click and closes it with Escape', () => {
    const confirmedLabel = { start: 0, end: 3, type: 'NAME', text: '홍길동' }
    act(() => {
      root.render(
        <HighlightViewer
          text="홍길동 내원"
          spans={[detection]}
          labels={[confirmedLabel]}
          colorMap={{ rule_test: '#38bdf8' }}
          onAddLabel={vi.fn()}
          onDeleteLabel={vi.fn()}
          onUpdateLabelType={vi.fn()}
        />,
      )
    })

    const detectedSegment = host.querySelector<HTMLElement>('[data-segment-start="0"]')!
    act(() => detectedSegment.dispatchEvent(new MouseEvent('click', { bubbles: true })))
    expect(document.querySelector('[role="dialog"]')).not.toBeNull()
    expect(document.querySelector('[role="dialog"]')?.getAttribute('aria-label')).toBe(
      '확정 라벨 관리',
    )

    act(() => document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' })))
    expect(document.querySelector('[role="dialog"]')).toBeNull()
  })
})
