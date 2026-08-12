import { useEffect, useMemo, useState } from 'react'
import './App.css'
import {
  detect,
  evaluate,
  getDocument,
  getModules,
  getSamples,
  listDocuments,
  saveLabels,
} from './api'
import type {
  DetectResponse,
  DetectionSpan,
  EvaluateResponse,
  Label,
  ModuleInfo,
  Sample,
  SavedDocument,
} from './api'
import { buildColorMap } from './colors'
import ModulePanel from './components/ModulePanel'
import HighlightViewer from './components/HighlightViewer'
import DetectionPanel from './components/DetectionPanel'
import ConfirmedSpanPanel from './components/ConfirmedSpanPanel'
import EvalPanel from './components/EvalPanel'

function App() {
  const [modules, setModules] = useState<ModuleInfo[]>([])
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [text, setText] = useState('')
  const [docId, setDocId] = useState('')
  const [synthetic, setSynthetic] = useState(true)

  const [samples, setSamples] = useState<Sample[]>([])
  const [savedDocs, setSavedDocs] = useState<SavedDocument[]>([])

  const [detectResult, setDetectResult] = useState<DetectResponse | null>(null)
  const [labels, setLabels] = useState<Label[]>([])
  const [metrics, setMetrics] = useState<EvaluateResponse['metrics'] | null>(null)

  const [detecting, setDetecting] = useState(false)
  const [evaluating, setEvaluating] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const colorMap = useMemo(
    () => buildColorMap(modules.map((m) => m.id)),
    [modules],
  )

  // 뷰어용으로 모든 모듈의 탐지 스팬을 하나로 펼친다.
  const allSpans = useMemo<DetectionSpan[]>(() => {
    if (!detectResult) return []
    return Object.values(detectResult.results).flat()
  }, [detectResult])

  useEffect(() => {
    getModules()
      .then((r) => setModules(r.modules))
      .catch((e) => setError(`모듈 목록 로드 실패: ${e.message}`))
    getSamples()
      .then((r) => setSamples(r.samples))
      .catch((e) => setError(`샘플 로드 실패: ${e.message}`))
    refreshDocs()
  }, [])

  function refreshDocs() {
    listDocuments()
      .then((r) => setSavedDocs(r.documents))
      .catch(() => {
        /* 저장 문서 목록은 선택 사항 */
      })
  }

  function toggleModule(id: string) {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  async function onPickSample(id: string) {
    if (!id) return
    const s = samples.find((x) => x.id === id)
    if (!s) return
    setText(s.text)
    setDocId(s.id)
    setSynthetic(true)
    setDetectResult(null)
    setMetrics(null)
    // 이 doc id에 대해 이전에 저장된 라벨이 있으면 복원한다.
    try {
      const doc = await getDocument(s.id)
      setLabels(doc.labels)
    } catch {
      setLabels([])
    }
  }

  async function onPickSavedDoc(id: string) {
    if (!id) return
    try {
      const doc = await getDocument(id)
      setText(doc.text)
      setDocId(doc.doc_id)
      setLabels(doc.labels)
      setDetectResult(null)
      setMetrics(null)
    } catch (e) {
      setError(`문서 로드 실패: ${(e as Error).message}`)
    }
  }

  async function runDetect() {
    if (!text.trim() || selected.size === 0) return
    setDetecting(true)
    setError(null)
    try {
      const res = await detect({
        text,
        module_ids: [...selected],
        synthetic,
      })
      setDetectResult(res)
    } catch (e) {
      setError(`탐지 실패: ${(e as Error).message}`)
    } finally {
      setDetecting(false)
    }
  }

  function addLabel(start: number, end: number, type: string, labelText: string) {
    setLabels((prev) => {
      if (prev.some((l) => l.start === start && l.end === end && l.type === type)) {
        return prev
      }
      return [...prev, { start, end, type, text: labelText }].sort(
        (a, b) => a.start - b.start || a.end - b.end,
      )
    })
  }

  function deleteLabel(target: Label) {
    setLabels((prev) =>
      prev.filter(
        (label) =>
          label.start !== target.start ||
          label.end !== target.end ||
          label.type !== target.type,
      ),
    )
  }

  function updateLabelType(target: Label, type: string) {
    setLabels((prev) => {
      const updated = prev.map((label) =>
        label.start === target.start && label.end === target.end && label.type === target.type
          ? { ...label, type }
          : label,
      )
      return updated.filter(
        (label, index) =>
          updated.findIndex(
            (candidate) =>
              candidate.start === label.start &&
              candidate.end === label.end &&
              candidate.type === label.type,
          ) === index,
      )
    })
  }

  async function save() {
    if (!text.trim()) {
      setError('저장할 텍스트가 없습니다.')
      return
    }
    const id = docId.trim() || `doc-${Date.now()}`
    if (!docId.trim()) setDocId(id)
    setSaving(true)
    setError(null)
    try {
      await saveLabels({ doc_id: id, text, labels })
      refreshDocs()
    } catch (e) {
      setError(`저장 실패: ${(e as Error).message}`)
    } finally {
      setSaving(false)
    }
  }

  async function runEvaluate() {
    if (!detectResult || labels.length === 0) return
    setEvaluating(true)
    setError(null)
    try {
      const res = await evaluate({ labels, detections: detectResult.results })
      setMetrics(res.metrics)
    } catch (e) {
      setError(`평가 실패: ${(e as Error).message}`)
    } finally {
      setEvaluating(false)
    }
  }

  const moduleErrors = detectResult?.module_errors ?? {}
  const blocked = detectResult?.blocked ?? []

  return (
    <div className="app">
      <header className="app-header">
        <h1>EMR 개인정보 마스킹 워크벤치</h1>
      </header>

      {error && (
        <div className="error-banner" onClick={() => setError(null)}>
          {error} <span className="dismiss">(클릭하여 닫기)</span>
        </div>
      )}

      <div className="layout">
        {/* 왼쪽 열: 입력 + 모듈 */}
        <div className="col col-left">
          <div className="panel">
            <div className="panel-head">
              <h2>입력</h2>
            </div>
            <div className="input-controls">
              <label className="ctl">
                샘플:
                <select
                  defaultValue=""
                  onChange={(e) => {
                    onPickSample(e.target.value)
                    e.target.value = ''
                  }}
                >
                  <option value="">— 샘플 선택 —</option>
                  {samples.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.id}
                    </option>
                  ))}
                </select>
              </label>
              <label className="ctl">
                저장 문서:
                <select
                  defaultValue=""
                  onChange={(e) => {
                    onPickSavedDoc(e.target.value)
                    e.target.value = ''
                  }}
                >
                  <option value="">— 문서 선택 —</option>
                  {savedDocs.map((d) => (
                    <option key={d.doc_id} value={d.doc_id}>
                      {d.doc_id}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <textarea
              className="text-input"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="진료기록 등 자유서술 텍스트를 입력하세요…"
              rows={8}
            />
            <div className="input-controls">
              <label className="ctl">
                doc_id:
                <input
                  type="text"
                  value={docId}
                  onChange={(e) => setDocId(e.target.value)}
                  placeholder="자동 생성됨"
                />
              </label>
              <label className="ctl checkbox">
                <input
                  type="checkbox"
                  checked={synthetic}
                  onChange={(e) => setSynthetic(e.target.checked)}
                />
                synthetic (합성 데이터)
              </label>
              <button className="primary" onClick={save} disabled={saving}>
                {saving ? '저장 중…' : '저장'}
              </button>
            </div>
          </div>

          <ModulePanel
            modules={modules}
            selected={selected}
            colorMap={colorMap}
            running={detecting}
            onToggle={toggleModule}
            onRun={runDetect}
          />
        </div>

        {/* 가운데 열: 뷰어 */}
        <div className="col col-center">
          <div className="panel">
            <div className="panel-head">
              <h2>탐지 및 라벨링</h2>
            </div>

            {(Object.keys(moduleErrors).length > 0 || blocked.length > 0) && (
              <div className="notices">
                {blocked.map((id) => (
                  <div key={`b-${id}`} className="notice blocked">
                    차단됨: {id} (합성 데이터가 아니어서 외부망 모듈 호출이 차단됨)
                  </div>
                ))}
                {Object.entries(moduleErrors).map(([id, msg]) => (
                  <div key={`e-${id}`} className="notice failed">
                    오류: {id} — {msg}
                  </div>
                ))}
              </div>
            )}

            {detectResult && (
              <div className="legend">
                {[...new Set(allSpans.map((s) => s.module))].map((mid) => (
                  <span key={mid} className="legend-item">
                    <span
                      className="swatch"
                      style={{ backgroundColor: colorMap[mid] ?? '#888' }}
                    />
                    {modules.find((m) => m.id === mid)?.display_name ?? mid}
                  </span>
                ))}
                <span className="legend-item">
                  <span className="swatch label-swatch" />
                  확정 라벨
                </span>
              </div>
            )}

            <HighlightViewer
              text={text}
              spans={allSpans}
              labels={labels}
              colorMap={colorMap}
              onAddLabel={addLabel}
              onDeleteLabel={deleteLabel}
              onUpdateLabelType={updateLabelType}
            />
          </div>
        </div>

        {/* 오른쪽 열: 탐지 목록 + 평가 */}
        <div className="col col-right">
          <DetectionPanel
            spans={allSpans}
            labels={labels}
            modules={modules}
            colorMap={colorMap}
            onConfirm={addLabel}
          />
          <ConfirmedSpanPanel
            labels={labels}
            detections={allSpans}
            onDelete={deleteLabel}
            onUpdateType={updateLabelType}
          />
          <EvalPanel
            metrics={metrics}
            modules={modules}
            canEvaluate={!!detectResult && labels.length > 0}
            running={evaluating}
            onEvaluate={runEvaluate}
          />
        </div>
      </div>
    </div>
  )
}

export default App
