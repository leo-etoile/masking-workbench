import type { DetectionSpan, Label, ModuleInfo } from '../api'

interface Props {
  spans: DetectionSpan[]
  labels: Label[]
  modules: ModuleInfo[]
  colorMap: Record<string, string>
  onConfirm: (start: number, end: number, type: string, text: string) => void
}

export default function DetectionPanel({
  spans,
  labels,
  modules,
  colorMap,
  onConfirm,
}: Props) {
  const unconfirmedSpans = spans.filter(
    (span) =>
      !labels.some(
        (label) =>
          label.start === span.start &&
          label.end === span.end &&
          label.type === span.type,
      ),
  )
  const grouped = modules
    .map((module) => ({
      module,
      spans: unconfirmedSpans
        .filter((span) => span.module === module.id)
        .sort((a, b) => a.start - b.start || a.end - b.end),
    }))
    .filter((group) => group.spans.length > 0)

  return (
    <div className="panel detection-panel">
      <div className="panel-head">
        <h2>탐지 스팬 ({unconfirmedSpans.length})</h2>
      </div>
      {grouped.length === 0 ? (
        <div className="empty">탐지를 실행하면 결과가 여기에 표시됩니다.</div>
      ) : (
        <div className="detection-groups">
          {grouped.map(({ module, spans: moduleSpans }) => (
            <section className="detection-group" key={module.id}>
              <div className="detection-group-head">
                <span className="swatch" style={{ backgroundColor: colorMap[module.id] ?? '#888' }} />
                <strong>{module.display_name}</strong>
                <span className="detection-count">{moduleSpans.length}</span>
              </div>
              <ul className="detection-list">
                {moduleSpans.map((span, index) => (
                    <li key={`${span.start}-${span.end}-${span.type}-${index}`}>
                      <div className="detection-main">
                        <span className="label-type">{span.type}</span>
                        <span className="detection-text" title={span.text}>“{span.text}”</span>
                        {span.score != null && (
                          <span className="detection-score">{span.score.toFixed(3)}</span>
                        )}
                      </div>
                      <div className="detection-meta">
                        <span>[{span.start}, {span.end})</span>
                        <button
                          className="primary sm"
                          onClick={() => onConfirm(span.start, span.end, span.type, span.text)}
                        >
                          확정
                        </button>
                      </div>
                    </li>
                ))}
              </ul>
            </section>
          ))}
        </div>
      )}
    </div>
  )
}
