"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { listEventsOperations, type EventOperations } from "@/lib/api";
import { DataState, OperationsPageHeader, OperationsSection } from "@/app/components/operations/OperationsPage";
import { fmtTime } from "@/lib/format";

const CREDIBILITY: Record<string, string> = { official: "官方确认", multi_source: "多方报道", early_signal: "早期信号" };

export default function EventsOperationsPage() {
  const [rows, setRows] = useState<EventOperations[]>([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(async () => { setLoading(true); setError(null); try { setRows(await listEventsOperations()); } catch (e) { setError(e instanceof Error ? e.message : "候选事件加载失败"); } finally { setLoading(false); } }, []);
  useEffect(() => { // eslint-disable-next-line react-hooks/set-state-in-effect
    void load(); }, [load]);
  const filtered = useMemo(() => rows.filter((row) => !query || `${row.title}${row.summary}`.toLowerCase().includes(query.toLowerCase())), [query, rows]);
  return <>
    <OperationsPageHeader eyebrow="Content Pipeline" title="候选事件" description="查看进入选题池的全部热点、证据数量与评分；选入今日日报的动作在“今日日报”中完成。" actions={<button onClick={load} className="rounded-full border border-steel px-4 py-2 text-xs text-fog">刷新</button>} />
    <OperationsSection>
      <input className="input mb-5 h-11 max-w-xl" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="搜索事件标题或摘要" />
      {(loading || error || !filtered.length) ? <DataState loading={loading} error={error} empty="暂无候选事件" onRetry={load} /> : <div className="grid gap-4 lg:grid-cols-2">{filtered.map((row) => <article key={row.id} className="paper-card rounded-card p-5">
        <div className="flex items-start justify-between gap-4"><span className="rounded-full border border-cyan/20 bg-pale-iris/40 px-2.5 py-1 text-xs text-cyan">{CREDIBILITY[row.credibility_label]}</span><span className="font-mono text-xs text-fog">{row.sort_score.toFixed(1)} 分</span></div>
        <h2 className="mt-4 font-serif text-lg text-cloud">{row.title}</h2><p className="mt-2 line-clamp-3 text-sm leading-6 text-silver">{row.summary}</p>
        <div className="mt-4 flex flex-wrap gap-x-4 gap-y-2 border-t border-steel pt-4 font-mono text-[10px] text-fog"><span>证据 {row.evidence_count}</span><span>相关 {row.relevance_score}</span><span>可行动 {row.actionability_score}</span><span>{fmtTime(row.first_seen_at)}</span></div>
      </article>)}</div>}
    </OperationsSection>
  </>;
}
