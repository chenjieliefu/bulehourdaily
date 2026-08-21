"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { getSiteContentOperations, publishSiteContentOperations, rollbackSiteContentOperations, saveSiteContentDraft, type SiteContentKey, type SiteContentOperations } from "@/lib/api";
import { DataState, OperationsPageHeader, OperationsSection } from "./OperationsPage";

const CONFIG = {
  product_intro: {
    eyebrow: "Site Content",
    title: "产品介绍",
    description: "维护公开产品页的核心定位、主标题、说明和价值点。草稿与公开版本相互独立。",
    fields: [
      ["eyebrow", "眉题", false], ["title", "主标题", false], ["subtitle", "副标题", true], ["section_title", "产品说明标题", true],
    ] as const,
  },
  membership: {
    eyebrow: "Membership Content",
    title: "会员页面",
    description: "维护会员页的价值表达和说明。具体价格仍由订阅规则控制，不在文案配置中修改。",
    fields: [
      ["title", "页面标题", false], ["subtitle", "页面副标题", true], ["hero_title", "会员主张", true], ["hero_detail", "会员说明", true], ["trial_title", "体验标题", false], ["trial_detail", "体验说明", true],
    ] as const,
  },
};

export default function SiteContentEditor({ contentKey }: { contentKey: SiteContentKey }) {
  const config = CONFIG[contentKey];
  const [data, setData] = useState<SiteContentOperations | null>(null);
  const [form, setForm] = useState<Record<string, unknown>>({});
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const features = Array.isArray(form.features) ? form.features as Array<{ title?: string; detail?: string }> : [];
  const dirty = useMemo(() => data ? JSON.stringify(form) !== JSON.stringify(data.draft) : false, [data, form]);
  const load = useCallback(async () => { setLoading(true); setError(null); try { const row = await getSiteContentOperations(contentKey); setData(row); setForm(row.draft); } catch (e) { setError(e instanceof Error ? e.message : "站点内容加载失败"); } finally { setLoading(false); } }, [contentKey]);
  useEffect(() => { // eslint-disable-next-line react-hooks/set-state-in-effect
    void load(); }, [load]);
  async function act(kind: "save" | "publish" | "rollback") { setBusy(true); setError(null); setNotice(null); try { let row: SiteContentOperations; if (kind === "save") row = await saveSiteContentDraft(contentKey, form); else if (kind === "publish") { if (dirty) await saveSiteContentDraft(contentKey, form); row = await publishSiteContentOperations(contentKey); } else row = await rollbackSiteContentOperations(contentKey); setData(row); setForm(row.draft); setNotice(kind === "save" ? "草稿已保存" : kind === "publish" ? "已发布到公开页面" : "已回滚到上一个公开版本"); } catch (e) { setError(e instanceof Error ? e.message : "操作失败"); } finally { setBusy(false); } }
  return <><OperationsPageHeader eyebrow={config.eyebrow} title={config.title} description={config.description} actions={<a href={contentKey === "product_intro" ? "/landing" : "/upgrade"} target="_blank" className="rounded-full border border-steel px-4 py-2 text-xs text-fog">查看公开页面 ↗</a>} /><OperationsSection>
    {(loading || error || !data) ? <DataState loading={loading} error={error} onRetry={load} /> : <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
      <section className="paper-card rounded-card p-6"><div className="grid gap-5">{config.fields.map(([key, label, multiline]) => <label key={key}><span className="font-mono text-[10px] uppercase tracking-widest text-fog">{label}</span>{multiline ? <textarea rows={4} className="input mt-1.5 resize-y" value={String(form[key] || "")} onChange={(e) => setForm({ ...form, [key]: e.target.value })} /> : <input className="input mt-1.5 h-11" value={String(form[key] || "")} onChange={(e) => setForm({ ...form, [key]: e.target.value })} />}</label>)}</div>
      {contentKey === "product_intro" && <div className="mt-7 border-t border-steel pt-6"><p className="font-mono text-[10px] uppercase tracking-widest text-fog">三项产品价值</p><div className="mt-4 grid gap-4 lg:grid-cols-3">{features.map((feature, index) => <div key={index} className="rounded-card border border-steel bg-abyss/30 p-4"><input aria-label={`价值点 ${index + 1} 标题`} className="input h-10" value={feature.title || ""} onChange={(e) => { const next = features.map((item, itemIndex) => itemIndex === index ? { ...item, title: e.target.value } : item); setForm({ ...form, features: next }); }} /><textarea aria-label={`价值点 ${index + 1} 说明`} rows={4} className="input mt-3 resize-y" value={feature.detail || ""} onChange={(e) => { const next = features.map((item, itemIndex) => itemIndex === index ? { ...item, detail: e.target.value } : item); setForm({ ...form, features: next }); }} /></div>)}</div></div>}
      <div className="mt-6 flex flex-wrap gap-3 border-t border-steel pt-5"><button disabled={busy || !dirty} onClick={() => act("save")} className="rounded-full border border-cyan/30 px-5 py-2 text-sm text-cyan disabled:opacity-40">保存草稿</button><button disabled={busy} onClick={() => act("publish")} className="rounded-full bg-cyan px-5 py-2 text-sm text-white disabled:opacity-40">保存并发布</button><button disabled={busy || !data.previous_published} onClick={() => act("rollback")} className="rounded-full border border-steel px-5 py-2 text-sm text-fog disabled:opacity-40">回滚公开版</button></div>{notice && <p className="mt-4 text-sm text-emerald-700">{notice}</p>}</section>
      <aside className="rounded-card border border-steel bg-abyss/45 p-6"><p className="eyebrow">发布状态</p><dl className="mt-5 space-y-4 text-sm"><div><dt className="text-xs text-fog">草稿最后保存</dt><dd className="mt-1 text-cloud">{new Date(data.updated_at).toLocaleString("zh-CN")}</dd></div><div><dt className="text-xs text-fog">公开版本发布时间</dt><dd className="mt-1 text-cloud">{data.published_at ? new Date(data.published_at).toLocaleString("zh-CN") : "使用系统初始文案"}</dd></div><div><dt className="text-xs text-fog">当前状态</dt><dd className="mt-1 text-cloud">{dirty ? "有未保存改动" : JSON.stringify(data.draft) === JSON.stringify(data.published) ? "草稿与公开版一致" : "草稿尚未发布"}</dd></div></dl><p className="mt-6 border-t border-steel pt-5 text-xs leading-6 text-fog">发布只影响对应公开页面的文案，不改变会员价格、用户权限或日报数据。</p></aside>
    </div>}
  </OperationsSection></>;
}
