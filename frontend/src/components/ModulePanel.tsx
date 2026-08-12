// 모듈 선택: 탐지 모듈마다 체크박스를 두고, 외부 네트워크가 필요한 모듈에는
// 배지를 붙인다. "실행" 버튼 포함.

import type { ModuleInfo } from '../api'

interface Props {
  modules: ModuleInfo[]
  selected: Set<string>
  colorMap: Record<string, string>
  running: boolean
  onToggle: (id: string) => void
  onRun: () => void
}

export default function ModulePanel({
  modules,
  selected,
  colorMap,
  running,
  onToggle,
  onRun,
}: Props) {
  return (
    <div className="panel">
      <div className="panel-head">
        <h2>탐지 모듈</h2>
        <button
          className="primary"
          onClick={onRun}
          disabled={running || selected.size === 0}
        >
          {running ? '실행 중…' : '실행'}
        </button>
      </div>
      {modules.length === 0 ? (
        <div className="empty">모듈을 불러오는 중…</div>
      ) : (
        <ul className="module-list">
          {modules.map((m) => (
            <li key={m.id}>
              <label title={m.description}>
                <input
                  type="checkbox"
                  checked={selected.has(m.id)}
                  onChange={() => onToggle(m.id)}
                />
                <span
                  className="swatch"
                  style={{ backgroundColor: colorMap[m.id] ?? '#888' }}
                />
                <span className="module-name">{m.display_name}</span>
                {m.requires_external_network && (
                  <span className="badge" title="외부 네트워크 필요">
                    외부망
                  </span>
                )}
              </label>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
