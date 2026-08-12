import { sliceCodepoints, utf16ToCodepoint } from './spans'

export interface TextRange {
  start: number
  end: number
  text: string
}

function segmentElement(root: HTMLElement, node: Node): HTMLElement | null {
  const element = node instanceof HTMLElement ? node : node.parentElement
  const segment = element?.closest<HTMLElement>('[data-segment-start]') ?? null
  return segment && root.contains(segment) ? segment : null
}

export function selectionPointToCodepoint(
  root: HTMLElement,
  node: Node,
  offset: number,
): number | null {
  if (!root.contains(node) && node !== root) return null

  if (node === root) {
    const children = root.querySelectorAll<HTMLElement>('[data-segment-start]')
    if (children.length === 0) return 0
    if (offset <= 0) return Number(children[0].dataset.segmentStart)
    if (offset >= root.childNodes.length) {
      return Number(children[children.length - 1].dataset.segmentEnd)
    }
    const nextNode = root.childNodes[offset]
    const nextSegment = nextNode ? segmentElement(root, nextNode) : null
    return nextSegment ? Number(nextSegment.dataset.segmentStart) : null
  }

  const segment = segmentElement(root, node)
  if (!segment) return null
  const segmentStart = Number(segment.dataset.segmentStart)
  if (!Number.isFinite(segmentStart)) return null

  const prefixRange = document.createRange()
  prefixRange.selectNodeContents(segment)
  try {
    prefixRange.setEnd(node, offset)
  } catch {
    return null
  }
  const utf16Offset = prefixRange.toString().length
  return segmentStart + utf16ToCodepoint(segment.textContent ?? '', utf16Offset)
}

export function selectionToTextRange(
  root: HTMLElement,
  selection: Selection,
  sourceText: string,
): TextRange | null {
  if (selection.isCollapsed || selection.rangeCount === 0) return null
  if (!selection.anchorNode || !selection.focusNode) return null

  const anchor = selectionPointToCodepoint(
    root,
    selection.anchorNode,
    selection.anchorOffset,
  )
  const focus = selectionPointToCodepoint(
    root,
    selection.focusNode,
    selection.focusOffset,
  )
  if (anchor == null || focus == null) return null

  const start = Math.min(anchor, focus)
  const end = Math.max(anchor, focus)
  if (end <= start) return null

  return {
    start,
    end,
    text: sliceCodepoints(Array.from(sourceText), start, end),
  }
}
