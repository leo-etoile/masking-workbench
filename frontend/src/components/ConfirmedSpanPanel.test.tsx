import { act } from 'react'
import { createRoot } from 'react-dom/client'
import type { Root } from 'react-dom/client'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import ConfirmedSpanPanel from './ConfirmedSpanPanel'

(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true

describe('ConfirmedSpanPanel', () => {
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
  })

  it('shows detection and manual origins and can reverse confirmation', () => {
    const detectedLabel = { start: 0, end: 3, type: 'NAME', text: '홍길동' }
    const manualLabel = { start: 4, end: 7, type: 'ADDRESS', text: '서울시' }
    const onDelete = vi.fn()
    act(() => {
      root.render(
        <ConfirmedSpanPanel
          labels={[detectedLabel, manualLabel]}
          detections={[
            { ...detectedLabel, module: 'llm_prompt', score: 0.9 },
          ]}
          onDelete={onDelete}
          onUpdateType={vi.fn()}
        />,
      )
    })

    expect(host.textContent).toContain('확정 스팬 (2)')
    expect(host.textContent).toContain('탐지')
    expect(host.textContent).toContain('수동')

    const cancelButtons = [...host.querySelectorAll('button')].filter(
      (button) => button.textContent === '확정 취소',
    )
    act(() => cancelButtons[0].dispatchEvent(new MouseEvent('click', { bubbles: true })))
    expect(onDelete).toHaveBeenCalledWith(detectedLabel)
  })
})
