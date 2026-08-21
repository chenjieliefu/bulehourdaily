"use client";

import { useCallback, useEffect, useState } from "react";
import { getCollectionStatus, type CollectionStatus } from "@/lib/api";
import { DataState, OperationsPageHeader, OperationsSection } from "@/app/components/operations/OperationsPage";
import { fmtTime } from "@/lib/format";

export default function CollectionOperationsPage() {
  const [data, setData] = useState<CollectionStatus | null>(null); const [loading, setLoading] = useState(true); const [error, setError] = useState<string | null>(null);
  const load = useCallback(async () => { setLoading(true); setError(null); try { setData(await getCollectionStatus()); } catch (e) { setError(e instanceof Error ? e.message : "采集状态加载失败"); } finally { setLoading(false); } }, []);
  useEffect(() => { // eslint-disable-next-line react-hooks/set-state-in-effect
    void load(); }, [load]);
  return <><OperationsPageHeader eyebrow="Collection Health" title="采集状态" description="观察每个信息源最近一次运行结果。本页只监控，不在无人工确认的情况下触发外部采集。" actions={<button onClick={load} className="rounded-full border border-steel px-4 py-2 text-xs text-fog">刷新</button>} /><OperationsSection>{(loading || error || !data) ? <DataState loading={loading} error={error} onRetry={load} /> : <><div className="mb-7 grid gap-4 sm:grid-cols-3"><Metric label="最近采集" value={fmtTime(data.last_collect_at)} /><Metric label="启用信息源" value={`${data.enabled_sources}/${data.total_sources}`} /><Metric label="累计条目" value={String(data.total_items)} /></div><div className="space-y-3">{data.sources.map((row) => <article key={row.source_id} className="paper-card flex flex-col gap-3 rounded-card p-5 md:flex-row md:items-center"><div className="min-w-0 flex-1"><p className="font-medium text-cloud">{row.source_name}</p><p className="mt-1 text-xs text-fog">最近成功 {fmtTime(row.last_success_at)} · 每日上限 {row.max_items_per_day}</p>{row.last_error && <p className="mt-2 text-xs text-red-600">{row.last_error}</p>}</div><span className={`self-start rounded-full border px-3 py-1 text-xs ${row.last_status === "success" ? "border-emerald-200 bg-emerald-50 text-emerald-700" : row.last_status === "failed" ? "border-red-200 bg-red-50 text-red-700" : "border-steel text-fog"}`}>{row.last_status === "success" ? "正常" : row.last_status === "failed" ? "失败" : "暂无运行"}</span></article>)}</div></>}</OperationsSection></>;
}
function Metric({ label, value }: { label: string; value: string }) { return <div className="paper-card rounded-card p-5"><p className="font-mono text-[10px] uppercase tracking-widest text-fog">{label}</p><p className="mt-3 font-serif text-2xl text-cloud">{value}</p></div>; }
