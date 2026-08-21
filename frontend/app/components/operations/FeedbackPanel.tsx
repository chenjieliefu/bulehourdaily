"use client";

import { useCallback, useEffect, useState } from "react";
import { listProductFeedbackOperations, updateProductFeedbackOperations, type ProductFeedbackOperations } from "@/lib/api";
import { fmtTime } from "@/lib/format";

const CATEGORY: Record<string, string> = { bug: "功能问题", content: "内容质量", experience: "使用体验", membership: "会员与付费", suggestion: "功能建议", other: "其他" };
const STATUS: Record<ProductFeedbackOperations["status"], string> = { new: "待处理", in_progress: "处理中", resolved: "已解决" };

export default function FeedbackPanel() {
  const [rows, setRows] = useState<ProductFeedbackOperations[]>([]);
  const [filter, setFilter] = useState<ProductFeedbackOperations["status"] | "all">("all");
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try { setRows(await listProductFeedbackOperations(filter === "all" ? undefined : filter)); }
    catch (e) { setError(e instanceof Error ? e.message : "产品反馈加载失败"); }
    finally { setLoading(false); }
  }, [filter]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load();
  }, [load]);

  async function advance(id: number, status: ProductFeedbackOperations["status"]) {
    setBusyId(id);
    setError(null);
    try {
      const updated = await updateProductFeedbackOperations(id, status);
      if (filter !== "all" && filter !== status) setRows((current) => current.filter((row) => row.id !== id));
      else setRows((current) => current.map((row) => row.id === id ? updated : row));
    } catch (e) { setError(e instanceof Error ? e.message : "状态更新失败"); }
    finally { setBusyId(null); }
  }

  return (
    <section>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="eyebrow">Product Feedback</p>
          <h2 className="mt-2 font-serif text-2xl text-cloud">用户意见收件箱</h2>
          <p className="mt-2 text-sm text-fog">这里处理产品意见；“想做 / 不感兴趣 / 已发布”仍属于内容发布反馈。</p>
        </div>
        <select value={filter} onChange={(e) => setFilter(e.target.value as typeof filter)} className="input h-11 w-full sm:w-44">
          <option value="all">全部状态</option>{Object.entries(STATUS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
        </select>
      </div>

      {error && <p className="mt-5 rounded-card border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</p>}
      {loading ? <p className="mt-8 text-sm text-fog">加载中…</p> : (
        <div className="mt-6 space-y-4">
          {rows.map((row) => (
            <article key={row.id} className="paper-card rounded-card p-5 sm:p-6">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="rounded-full border border-cyan/20 bg-pale-iris/35 px-2.5 py-1 text-xs text-cyan">{CATEGORY[row.category] || row.category}</span>
                    <span className="font-mono text-[10px] text-fog">#{row.id} · {fmtTime(row.created_at)}</span>
                  </div>
                  <p className="mt-4 whitespace-pre-wrap text-sm leading-7 text-ash">{row.content}</p>
                  <p className="mt-4 text-xs text-fog">提交人：{row.user_email || row.contact_email || "匿名访客"}{row.page_url && <> · <a href={row.page_url} target="_blank" rel="noopener noreferrer" className="text-cyan hover:underline">来源页面 ↗</a></>}</p>
                </div>
                <div className="flex shrink-0 flex-wrap gap-2">
                  {(["new", "in_progress", "resolved"] as const).map((status) => (
                    <button key={status} disabled={busyId === row.id || row.status === status} onClick={() => advance(row.id, status)} className={`rounded-full border px-3 py-1.5 text-xs disabled:cursor-default ${row.status === status ? "border-cyan bg-cyan text-white" : "border-steel text-fog hover:border-cyan hover:text-cyan"}`}>
                      {STATUS[status]}
                    </button>
                  ))}
                </div>
              </div>
            </article>
          ))}
          {!rows.length && <div className="paper-card rounded-feature p-12 text-center text-sm text-fog">当前没有符合条件的产品反馈。</div>}
        </div>
      )}
    </section>
  );
}
