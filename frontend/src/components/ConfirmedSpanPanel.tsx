import { PII_TYPES } from '../api'
import type { DetectionSpan, Label, PiiType } from '../api'

interface Props {
  labels: Label[]
  detections: DetectionSpan[]
  onDelete: (label: Label) => void
  onUpdateType: (label: Label, type: PiiType) => void
}

export default function ConfirmedSpanPanel({
  labels,
  detections,
  onDelete,
  onUpdateType,
}: Props) {
  const sortedLabels = [...labels].sort((a, b) => a.start - b.start || a.end - b.end)

  return (
    <div className="panel confirmed-panel">
      <div className="panel-head">
        <h2>확정 스팬 ({labels.length})</h2>
      </div>
      {sortedLabels.length === 0 ? (
        <div className="empty">탐지 스팬을 확정하거나 텍스트를 드래그해 추가하세요.</div>
      ) : (
        <ul className="confirmed-list">
          {sortedLabels.map((label) => {
            const fromDetection = detections.some(
              (span) =>
                span.start === label.start &&
                span.end === label.end &&
                span.type === label.type,
            )
            return (
              <li key={`${label.start}-${label.end}-${label.type}`}>
                <div className="confirmed-main">
                  <select
                    value={label.type}
                    aria-label={`${label.text} 개인정보 유형`}
                    onChange={(event) => onUpdateType(label, event.target.value as PiiType)}
                  >
                    {PII_TYPES.map((type) => (
                      <option key={type} value={type}>{type}</option>
                    ))}
                  </select>
                  <span className="confirmed-text" title={label.text}>“{label.text}”</span>
                  <span className={fromDetection ? 'source-badge detected' : 'source-badge manual'}>
                    {fromDetection ? '탐지' : '수동'}
                  </span>
                </div>
                <div className="confirmed-meta">
                  <span>[{label.start}, {label.end})</span>
                  <button className="danger sm" onClick={() => onDelete(label)}>확정 취소</button>
                </div>
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
