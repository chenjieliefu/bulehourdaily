"use client";

import { useCallback, useEffect, useState } from "react";
import { listPublicationFeedbackOperations, type PublicationFeedbackOperations } from "@/lib/api";
import { DataState, OperationsPageHeader, OperationsSection } from "@/app/components/operations/OperationsPage";
import { fmtTime } from "@/lib/format";

const LABEL: Record<string, string> = { want: "想做", not_interested: "不感兴趣", published: "已发布" };
export default function PublicationFeedbackPage() {
  const [rows, setRows] = useState<PublicationFeedbackOperations[]>([]); const [loading, setLoading] = useState(true); const [error, setError] = useState<string | null>(null);
  const load = useCallback(async () => { setLoading(true); setError(null); try { setRows(await listPublicationFeedbackOperations()); } catch (e) { setError(e instanceof Error ? e.message : "发布反馈加载失败"); } finally { setLoading(false); } }, []);
  useEffect(() => { // eslint-disable-next-line react-hooks/set-state-in-effect
    void load(); }, [load]);
  return <><OperationsPageHeader eyebrow="Content Feedback" title="发布反馈" description="创作者对个性化选题的真实行动反馈，用于判断推荐是否有用。" /><OperationsSection>{(loading || error || !rows.length) ? <DataState loading={loading} error={error} empty="暂无发布反馈" onRetry={load} /> : <div className="space-y-3">{rows.map((row) => <article key={row.id} className="paper-card rounded-card p-5"><div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between"><div><p className="text-sm font-medium text-cloud">{row.topic_title}</p><p className="mt-1 text-xs text-fog">{row.user_email} · {row.report_date} · {fmtTime(row.updated_at)}</p></div><span className="self-start rounded-full border border-cyan/20 bg-pale-iris/40 px-3 py-1 text-xs text-cyan">{LABEL[row.status] || row.status}</span></div>{row.douyin_url && <a href={row.douyin_url} target="_blank" rel="noopener noreferrer" className="mt-4 inline-block text-xs text-cyan underline">查看已发布作品 ↗</a>}</article>)}</div>}</OperationsSection></>;
}
