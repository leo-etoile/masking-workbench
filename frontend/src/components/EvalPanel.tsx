// 평가 패널: /api/evaluate 를 호출하고 모듈별 P/R/F1 및 TP/FP/FN 을 렌더링한다.

import type { ModuleInfo, EvaluateResponse } from '../api'

interface Props {
  metrics: EvaluateResponse['metrics'] | null
  modules: ModuleInfo[]
  canEvaluate: boolean
  running: boolean
  onEvaluate: () => void
}

function displayName(modules: ModuleInfo[], id: string): string {
  return modules.find((m) => m.id === id)?.display_name ?? id
}

export default function EvalPanel({
  metrics,
  modules,
  canEvaluate,
  running,
  onEvaluate,
}: Props) {
  const rows = metrics ? Object.entries(metrics) : []
  return (
    <div className="panel">
      <div className="panel-head">
        <h2>평가</h2>
        <button
          className="primary"
          onClick={onEvaluate}
          disabled={!canEvaluate || running}
          title={canEvaluate ? '' : '확정 라벨과 탐지 결과가 모두 필요합니다.'}
        >
          {running ? '평가 중…' : '평가'}
        </button>
      </div>
      {rows.length === 0 ? (
        <div className="empty">
          확정 라벨과 탐지 결과를 준비한 뒤 평가를 실행하세요.
        </div>
      ) : (
        <div className="table-wrap">
          <table className="metrics">
            <thead>
              <tr>
                <th>모듈</th>
                <th>P</th>
                <th>R</th>
                <th>F1</th>
                <th title="정확히 탐지한 해당 유형의 라벨 수">TP</th>
                <th title="해당 모듈이 잘못 탐지한 수">FP</th>
                <th title="해당 모듈이 지원하는 유형 중 놓친 라벨 수">FN</th>
              </tr>
            </thead>
            <tbody>
              {rows.map(([id, m]) => (
                <tr key={id}>
                  <td>{displayName(modules, id)}</td>
                  <td>{m.precision.toFixed(3)}</td>
                  <td>{m.recall.toFixed(3)}</td>
                  <td>{m.f1.toFixed(3)}</td>
                  <td>{m.tp}</td>
                  <td>{m.fp}</td>
                  <td>{m.fn}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
