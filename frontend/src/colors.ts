// module id 기준으로 안정적인 색상 팔레트를 부여한다.
// 색상은 처음 등장한 순서대로 배정되므로, 한 세션 내 재렌더링에도 각 모듈은
// 동일한 색상을 유지한다.

const PALETTE = [
  '#38bdf8', // 하늘색
  '#fb7185', // 장미색
  '#4ade80', // 초록
  '#fbbf24', // 호박색
  '#c084fc', // 보라
  '#22d3ee', // 청록
  '#f472b6', // 분홍
  '#a3e635', // 라임
  '#818cf8', // 남색
  '#fb923c', // 주황
]

export function buildColorMap(moduleIds: string[]): Record<string, string> {
  const map: Record<string, string> = {}
  moduleIds.forEach((id, i) => {
    map[id] = PALETTE[i % PALETTE.length]
  })
  return map
}
