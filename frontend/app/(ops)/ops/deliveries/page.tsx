"use client";

import { useCallback, useEffect, useState } from "react";
import { listMailDeliveriesOperations, type MailDeliveryOperations } from "@/lib/api";
import { DataState, OperationsPageHeader, OperationsSection } from "@/app/components/operations/OperationsPage";
import { fmtTime } from "@/lib/format";

export default function DeliveriesOperationsPage() {
  const [rows, setRows] = useState<MailDeliveryOperations[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(async () => { setLoading(true); setError(null); try { setRows(await listMailDeliveriesOperations()); } catch (e) { setError(e instanceof Error ? e.message : "邮件记录加载失败"); } finally { setLoading(false); } }, []);
  useEffect(() => { // eslint-disable-next-line react-hooks/set-state-in-effect
    void load(); }, [load]);
  return <><OperationsPageHeader eyebrow="Delivery" title="邮件送达" description="逐封查看个性化日报是否进入发送链路、何时送达以及失败原因。" actions={<button onClick={load} className="rounded-full border border-steel px-4 py-2 text-xs text-fog">刷新</button>} /><OperationsSection>{(loading || error || !rows.length) ? <DataState loading={loading} error={error} empty="暂无邮件送达记录" onRetry={load} /> : <div className="space-y-3">{rows.map((row) => <article key={row.id} className="paper-card flex flex-col gap-4 rounded-card p-5 md:flex-row md:items-center"><div className="min-w-0 flex-1"><p className="text-sm font-medium text-cloud">{row.user_email}</p><p className="mt-1 truncate text-xs text-fog">{row.subject}</p><p className="mt-2 font-mono text-[10px] text-fog">日报 {row.report_date || "—"} · 创建 {fmtTime(row.created_at)} · 发送 {fmtTime(row.sent_at)}</p>{row.error && <p className="mt-2 text-xs text-red-600">{row.error}</p>}</div><span className={`self-start rounded-full border px-3 py-1 text-xs ${row.status === "sent" ? "border-emerald-200 bg-emerald-50 text-emerald-700" : row.status === "failed" ? "border-red-200 bg-red-50 text-red-700" : "border-amber-200 bg-amber-50 text-amber-700"}`}>{row.status === "sent" ? "已发送" : row.status === "failed" ? "失败" : "待发送"}</span></article>)}</div>}</OperationsSection></>;
}
