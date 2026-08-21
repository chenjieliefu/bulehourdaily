"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { listCreatorOperations, type CreatorOperations } from "@/lib/api";
import { fmtTime } from "@/lib/format";

const STATUS_LABEL: Record<CreatorOperations["entitlement_status"], string> = {
  subscriber: "订阅中",
  trial: "体验中",
  trial_exhausted: "体验已用完",
  expired: "订阅已到期",
};

export default function CreatorsPanel({ onInspect }: { onInspect: (userId: number) => void }) {
  const [rows, setRows] = useState<CreatorOperations[]>([]);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<CreatorOperations["entitlement_status"] | "all">("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setRows(await listCreatorOperations());
    } catch (e) {
      setError(e instanceof Error ? e.message : "创作者数据加载失败");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load();
  }, [load]);

  const filtered = useMemo(() => rows.filter((row) => {
    const matchesQuery = !query || row.email.toLowerCase().includes(query.toLowerCase()) || row.profile_positioning?.includes(query);
    return matchesQuery && (status === "all" || row.entitlement_status === status);
  }), [query, rows, status]);

  return (
    <section>
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="eyebrow">Creators</p>
          <h2 className="mt-2 font-serif text-2xl text-cloud">创作者当前情况</h2>
          <p className="mt-2 text-sm text-fog">体验和订阅分开显示，避免用“会员”掩盖真实资格状态。</p>
        </div>
        <button onClick={load} className="self-start rounded-full border border-steel px-4 py-2 text-xs text-fog hover:border-cyan hover:text-cyan">刷新</button>
      </div>

      <div className="mt-6 grid gap-3 sm:grid-cols-[minmax(0,1fr)_210px]">
        <input value={query} onChange={(e) => setQuery(e.target.value)} className="input h-11" placeholder="搜索邮箱或账号定位" />
        <select value={status} onChange={(e) => setStatus(e.target.value as typeof status)} className="input h-11">
          <option value="all">全部资格状态</option>
          {Object.entries(STATUS_LABEL).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
        </select>
      </div>

      {error && <p className="mt-5 rounded-card border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</p>}
      {loading ? <p className="mt-8 text-sm text-fog">加载中…</p> : (
        <div className="mt-5 overflow-hidden rounded-card border border-steel bg-white/90 shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[980px] text-left text-sm">
              <thead className="border-b border-steel bg-abyss/60 font-mono text-[10px] uppercase tracking-widest text-fog">
                <tr>
                  <th className="px-5 py-3 font-normal">创作者</th><th className="px-4 py-3 font-normal">资格</th>
                  <th className="px-4 py-3 font-normal">内容产出</th><th className="px-4 py-3 font-normal">发布反馈</th>
                  <th className="px-4 py-3 font-normal">最近内容互动</th><th className="px-5 py-3 font-normal"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-steel/80">
                {filtered.map((row) => (
                  <tr key={row.id} className="align-top hover:bg-abyss/25">
                    <td className="px-5 py-4">
                      <p className="font-medium text-cloud">{row.email}</p>
                      <p className="mt-1 max-w-[240px] truncate text-xs text-fog">{row.profile_positioning || "尚未填写创作者画像"}</p>
                    </td>
                    <td className="px-4 py-4">
                      <StatusPill status={row.entitlement_status} />
                      <p className="mt-2 text-xs text-fog">{entitlementNote(row)}</p>
                    </td>
                    <td className="px-4 py-4 text-xs leading-6 text-silver">
                      <p>{row.personalized_report_count} 份日报 · {row.creation_plan_count} 份方案</p>
                      <p>最近日报 {row.last_report_date || "—"} · 邮件 {mailLabel(row.latest_mail_status)}</p>
                    </td>
                    <td className="px-4 py-4 text-xs leading-6 text-silver">
                      想做 {row.feedback_want} · 不感兴趣 {row.feedback_not_interested} · 已发布 {row.feedback_published}
                    </td>
                    <td className="px-4 py-4 text-xs text-fog">{fmtTime(row.latest_interaction_at)}</td>
                    <td className="px-5 py-4 text-right">
                      <button onClick={() => onInspect(row.id)} className="rounded-full border border-cyan/30 px-4 py-1.5 text-xs text-cyan hover:bg-pale-iris/50">查看个性化内容</button>
                    </td>
                  </tr>
                ))}
                {!filtered.length && <tr><td colSpan={6} className="px-5 py-12 text-center text-sm text-fog">没有符合条件的创作者。</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </section>
  );
}

function StatusPill({ status }: { status: CreatorOperations["entitlement_status"] }) {
  const tone = status === "subscriber" ? "border-emerald-200 bg-emerald-50 text-emerald-700" : status === "trial" ? "border-cyan/20 bg-pale-iris/45 text-cyan" : "border-amber-200 bg-amber-50 text-amber-700";
  return <span className={`inline-flex rounded-full border px-2.5 py-1 text-xs ${tone}`}>{STATUS_LABEL[status]}</span>;
}

function entitlementNote(row: CreatorOperations) {
  if (row.entitlement_status === "subscriber") return `¥${row.subscription_monthly_price}/月 · ${row.subscription_expires_at?.slice(0, 10)} 到期`;
  if (row.entitlement_status === "trial") return `剩余 ${row.trial_remaining} 份体验`;
  return "当前不能生成新个性化日报";
}

function mailLabel(status: string | null) {
  if (status === "sent") return "已发送";
  if (status === "failed") return "失败";
  if (status === "pending") return "待发送";
  return "暂无";
}
