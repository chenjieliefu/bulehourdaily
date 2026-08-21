"use client";

import { useCallback, useEffect, useState } from "react";
import { createSubscriptionOperations, listCreatorOperations, listSubscriptionsOperations, type CreatorOperations, type SubscriptionOperations } from "@/lib/api";
import { DataState, OperationsPageHeader, OperationsSection } from "@/app/components/operations/OperationsPage";

export default function SubscriptionsOperationsPage() {
  const [rows, setRows] = useState<SubscriptionOperations[]>([]);
  const [creators, setCreators] = useState<CreatorOperations[]>([]);
  const [userId, setUserId] = useState("");
  const [months, setMonths] = useState("1");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(async () => { setLoading(true); setError(null); try { const [subs, users] = await Promise.all([listSubscriptionsOperations(), listCreatorOperations()]); setRows(subs); setCreators(users); } catch (e) { setError(e instanceof Error ? e.message : "订阅数据加载失败"); } finally { setLoading(false); } }, []);
  useEffect(() => { // eslint-disable-next-line react-hooks/set-state-in-effect
    void load(); }, [load]);
  async function create() { if (!userId) return; setBusy(true); setError(null); try { await createSubscriptionOperations({ user_id: Number(userId), months: Number(months) }); setUserId(""); await load(); } catch (e) { setError(e instanceof Error ? e.message : "开通失败"); } finally { setBusy(false); } }
  return <><OperationsPageHeader eyebrow="Entitlements" title="订阅管理" description="人工开通订阅并核对有效期。金额进入历史记录后不在这里修改。" /><OperationsSection>
    <div className="paper-card mb-7 rounded-card p-5"><p className="font-medium text-cloud">人工开通订阅</p><div className="mt-4 grid gap-3 md:grid-cols-[minmax(0,1fr)_130px_auto]"><select className="input h-11" value={userId} onChange={(e) => setUserId(e.target.value)}><option value="">选择创作者</option>{creators.map((row) => <option key={row.id} value={row.id}>{row.email}</option>)}</select><select className="input h-11" value={months} onChange={(e) => setMonths(e.target.value)}><option value="1">1 个月</option><option value="3">3 个月</option><option value="6">6 个月</option><option value="12">12 个月</option></select><button disabled={!userId || busy} onClick={create} className="rounded-full bg-cyan px-6 py-2 text-sm text-white disabled:opacity-40">{busy ? "开通中…" : "确认开通"}</button></div></div>
    {(loading || error || !rows.length) ? <DataState loading={loading} error={error} empty="暂无订阅记录" onRetry={load} /> : <div className="overflow-hidden rounded-card border border-steel bg-white"><table className="w-full min-w-[820px] text-left text-sm"><thead className="bg-abyss/60 font-mono text-[10px] uppercase tracking-widest text-fog"><tr><th className="px-5 py-3 font-normal">创作者</th><th className="px-4 py-3 font-normal">价格</th><th className="px-4 py-3 font-normal">开始</th><th className="px-4 py-3 font-normal">到期</th><th className="px-5 py-3 font-normal">当前</th></tr></thead><tbody className="divide-y divide-steel">{rows.map((row) => <tr key={row.id}><td className="px-5 py-4 text-cloud">{row.user_email}</td><td className="px-4 py-4 text-silver">¥{row.monthly_price}/月 · {row.price_type === "founding" ? "创始" : "标准"}</td><td className="px-4 py-4 text-fog">{row.started_at.slice(0, 10)}</td><td className="px-4 py-4 text-fog">{row.expires_at.slice(0, 10)}</td><td className="px-5 py-4"><span className={`rounded-full border px-2.5 py-1 text-xs ${row.is_effective ? "border-emerald-200 bg-emerald-50 text-emerald-700" : "border-steel text-fog"}`}>{row.is_effective ? "有效" : "已失效"}</span></td></tr>)}</tbody></table></div>}
  </OperationsSection></>;
}
