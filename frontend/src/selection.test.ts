import { afterEach, describe, expect, it } from 'vitest'
import { selectionPointToCodepoint, selectionToTextRange } from './selection'

function makeViewer(parts: Array<{ start: number; text: string }>): HTMLDivElement {
  const root = document.createElement('div')
  for (const part of parts) {
    const segment = document.createElement('span')
    segment.dataset.segmentStart = String(part.start)
    segment.dataset.segmentEnd = String(part.start + Array.from(part.text).length)
    segment.textContent = part.text
    root.append(segment)
  }
  document.body.append(root)
  return root
}

function mockSelection(
  anchorNode: Node,
  anchorOffset: number,
  focusNode: Node,
  focusOffset: number,
  collapsed = false,
): Selection {
  return {
    anchorNode,
    anchorOffset,
    focusNode,
    focusOffset,
    isCollapsed: collapsed,
    rangeCount: collapsed ? 0 : 1,
  } as Selection
}

afterEach(() => {
  document.body.replaceChildren()
})

describe('selectionPointToCodepoint', () => {
  it('converts a UTF-16 offset inside a segment to a source codepoint offset', () => {
    const root = makeViewer([{ start: 4, text: 'A😀한' }])
    const textNode = root.firstChild?.firstChild as Text

    expect(selectionPointToCodepoint(root, textNode, 3)).toBe(6)
  })

  it('maps root-level boundary points to adjacent segment boundaries', () => {
    const root = makeViewer([
      { start: 0, text: '앞' },
      { start: 1, text: '뒤' },
    ])

    expect(selectionPointToCodepoint(root, root, 1)).toBe(1)
    expect(selectionPointToCodepoint(root, root, 2)).toBe(2)
  })
})

describe('selectionToTextRange', () => {
  it('normalizes a forward selection across highlighted segments', () => {
    const root = makeViewer([
      { start: 0, text: '환자 ' },
      { start: 3, text: '홍길동' },
      { start: 6, text: ' 내원' },
    ])
    const first = root.children[0].firstChild as Text
    const last = root.children[2].firstChild as Text

    const result = selectionToTextRange(root, mockSelection(first, 2, last, 2), '환자 홍길동 내원')

    expect(result).toEqual({ start: 2, end: 8, text: ' 홍길동 내' })
  })

  it('normalizes a reverse selection and preserves emoji codepoints', () => {
    const root = makeViewer([
      { start: 0, text: 'A😀' },
      { start: 2, text: '한글' },
    ])
    const first = root.children[0].firstChild as Text
    const last = root.children[1].firstChild as Text

    const result = selectionToTextRange(root, mockSelection(last, 1, first, 1), 'A😀한글')

    expect(result).toEqual({ start: 1, end: 3, text: '😀한' })
  })

  it('ignores collapsed and out-of-viewer selections', () => {
    const root = makeViewer([{ start: 0, text: '본문' }])
    const textNode = root.firstChild?.firstChild as Text
    const outside = document.createTextNode('외부')
    document.body.append(outside)

    expect(selectionToTextRange(root, mockSelection(textNode, 0, textNode, 0, true), '본문')).toBeNull()
    expect(selectionToTextRange(root, mockSelection(textNode, 0, outside, 1), '본문')).toBeNull()
  })
})
