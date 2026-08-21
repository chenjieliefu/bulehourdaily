"use client";

import { useCallback, useEffect, useState } from "react";
import { listSourcesOperations, updateSourceOperations, type SourceOperations } from "@/lib/api";
import { DataState, OperationsPageHeader, OperationsSection } from "@/app/components/operations/OperationsPage";

export default function SourcesOperationsPage() {
  const [rows, setRows] = useState<SourceOperations[]>([]); const [loading, setLoading] = useState(true); const [error, setError] = useState<string | null>(null); const [busy, setBusy] = useState<number | null>(null);
  const load = useCallback(async () => { setLoading(true); setError(null); try { setRows(await listSourcesOperations()); } catch (e) { setError(e instanceof Error ? e.message : "信息源加载失败"); } finally { setLoading(false); } }, []);
  useEffect(() => { // eslint-disable-next-line react-hooks/set-state-in-effect
    void load(); }, [load]);
  async function toggle(row: SourceOperations) { setBusy(row.id); try { await updateSourceOperations(row.id, { enabled: !row.enabled }); await load(); } catch (e) { setError(e instanceof Error ? e.message : "更新失败"); } finally { setBusy(null); } }
  return <><OperationsPageHeader eyebrow="Sources" title="信息源" description="管理采集入口、可信度等级和单日条目上限。停用只影响后续采集，不删除历史内容。" /><OperationsSection>{(loading || error || !rows.length) ? <DataState loading={loading} error={error} empty="暂无信息源" onRetry={load} /> : <div className="grid gap-4 lg:grid-cols-2">{rows.map((row) => <article key={row.id} className={`rounded-card border p-5 ${row.enabled ? "border-steel bg-white" : "border-steel bg-abyss/30 opacity-70"}`}><div className="flex items-start justify-between gap-4"><div className="min-w-0"><h2 className="font-medium text-cloud">{row.name}</h2><a href={row.url} target="_blank" rel="noopener noreferrer" className="mt-1 block truncate text-xs text-cyan">{row.url}</a></div><button disabled={busy === row.id} onClick={() => toggle(row)} className={`rounded-full border px-3 py-1 text-xs ${row.enabled ? "border-emerald-200 text-emerald-700" : "border-steel text-fog"}`}>{row.enabled ? "已启用" : "已停用"}</button></div><div className="mt-4 flex flex-wrap gap-2 font-mono text-[10px] text-fog"><span>{row.type}</span><span>· {row.credibility_level}</span><span>· 每日最多 {row.max_items_per_day} 条</span></div></article>)}</div>}</OperationsSection></>;
}
