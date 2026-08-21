"use client";

import { useCallback, useEffect, useState } from "react";
import { listJobsOperations, type JobOperations } from "@/lib/api";
import { DataState, OperationsPageHeader, OperationsSection } from "@/app/components/operations/OperationsPage";
import { fmtTime } from "@/lib/format";

export default function JobsOperationsPage() {
  const [rows, setRows] = useState<JobOperations[]>([]); const [loading, setLoading] = useState(true); const [error, setError] = useState<string | null>(null);
  const load = useCallback(async () => { setLoading(true); setError(null); try { setRows(await listJobsOperations()); } catch (e) { setError(e instanceof Error ? e.message : "任务记录加载失败"); } finally { setLoading(false); } }, []);
  useEffect(() => { // eslint-disable-next-line react-hooks/set-state-in-effect
    void load(); }, [load]);
  return <><OperationsPageHeader eyebrow="Background Jobs" title="任务记录" description="集中追踪采集、事件提取、日报生成和个性化生成任务的结果与错误。" actions={<button onClick={load} className="rounded-full border border-steel px-4 py-2 text-xs text-fog">刷新</button>} /><OperationsSection>{(loading || error || !rows.length) ? <DataState loading={loading} error={error} empty="暂无任务记录" onRetry={load} /> : <div className="overflow-hidden rounded-card border border-steel bg-white"><table className="w-full min-w-[850px] text-left text-sm"><thead className="bg-abyss/60 font-mono text-[10px] uppercase tracking-widest text-fog"><tr><th className="px-5 py-3 font-normal">任务</th><th className="px-4 py-3 font-normal">状态</th><th className="px-4 py-3 font-normal">创建</th><th className="px-4 py-3 font-normal">完成</th><th className="px-5 py-3 font-normal">结果</th></tr></thead><tbody className="divide-y divide-steel">{rows.map((row) => <tr key={row.id}><td className="px-5 py-4 text-cloud">#{row.id} · {row.kind}</td><td className="px-4 py-4"><span className={`rounded-full border px-2.5 py-1 text-xs ${row.status === "success" ? "border-emerald-200 bg-emerald-50 text-emerald-700" : row.status === "failed" ? "border-red-200 bg-red-50 text-red-700" : "border-amber-200 bg-amber-50 text-amber-700"}`}>{row.status}</span></td><td className="px-4 py-4 text-fog">{fmtTime(row.created_at)}</td><td className="px-4 py-4 text-fog">{fmtTime(row.finished_at)}</td><td className="max-w-[340px] px-5 py-4 text-xs text-fog">{row.error_message || row.result_ref || "—"}</td></tr>)}</tbody></table></div>}</OperationsSection></>;
}
