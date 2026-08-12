import { act } from 'react'
import { createRoot } from 'react-dom/client'
import type { Root } from 'react-dom/client'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import DetectionPanel from './DetectionPanel'

(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true

describe('DetectionPanel', () => {
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

  it('groups detected spans and confirms unconfirmed items in place', () => {
    const onConfirm = vi.fn()
    act(() => {
      root.render(
        <DetectionPanel
          spans={[
            {
              start: 4,
              end: 7,
              type: 'NAME',
              module: 'rule_test',
              text: '홍길동',
              score: 0.9,
            },
          ]}
          labels={[]}
          modules={[
            { id: 'rule_test', display_name: '테스트 탐지기', requires_external_network: false },
          ]}
          colorMap={{ rule_test: '#38bdf8' }}
          onConfirm={onConfirm}
        />,
      )
    })

    expect(host.textContent).toContain('테스트 탐지기')
    expect(host.textContent).toContain('0.900')
    const confirm = [...host.querySelectorAll('button')].find(
      (button) => button.textContent === '확정',
    )!
    act(() => confirm.dispatchEvent(new MouseEvent('click', { bubbles: true })))
    expect(onConfirm).toHaveBeenCalledWith(4, 7, 'NAME', '홍길동')
  })

  it('removes an item from the pending list when it is already confirmed', () => {
    const confirmedLabel = { start: 0, end: 3, type: 'NAME', text: '홍길동' }
    act(() => {
      root.render(
        <DetectionPanel
          spans={[
            { start: 0, end: 3, type: 'NAME', module: 'rule_test', text: '홍길동', score: null },
          ]}
          labels={[confirmedLabel]}
          modules={[
            { id: 'rule_test', display_name: '테스트 탐지기', requires_external_network: false },
          ]}
          colorMap={{ rule_test: '#38bdf8' }}
          onConfirm={vi.fn()}
        />,
      )
    })

    expect(host.textContent).toContain('탐지 스팬 (0)')
    expect(host.querySelector('button')).toBeNull()
  })
})
