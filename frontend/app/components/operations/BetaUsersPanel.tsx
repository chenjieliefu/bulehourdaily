"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { createInviteCodes, listCreatorOperations, listInviteCodes, type CreatorOperations, type InviteCode } from "@/lib/api";
import { fmtTime } from "@/lib/format";

export default function BetaUsersPanel() {
  const [creators, setCreators] = useState<CreatorOperations[]>([]);
  const [invites, setInvites] = useState<InviteCode[]>([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [creatorRows, inviteRows] = await Promise.all([listCreatorOperations(), listInviteCodes()]);
      setCreators(creatorRows);
      setInvites(inviteRows);
    } catch (e) {
      setError(e instanceof Error ? e.message : "内测用户加载失败");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load();
  }, [load]);

  async function createInvites() {
    setBusy(true);
    setError(null);
    try {
      await createInviteCodes(5);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "邀请码生成失败");
    } finally {
      setBusy(false);
    }
  }

  const filtered = useMemo(
    () => creators.filter((creator) => !query || creator.email.toLowerCase().includes(query.toLowerCase()) || creator.profile_positioning?.includes(query)),
    [creators, query],
  );
  const completedProfiles = creators.filter((creator) => creator.has_profile).length;
  const unusedInvites = invites.filter((invite) => !invite.used).length;

  if (loading) return <div className="paper-card rounded-card p-10 text-center text-sm text-fog">正在加载内测用户…</div>;

  return (
    <div className="space-y-10">
      {error && <div className="rounded-card border border-red-200 bg-red-50 p-5 text-sm text-red-700"><p>{error}</p><button onClick={load} className="mt-3 rounded-full border border-red-300 px-4 py-1.5 text-xs">重新加载</button></div>}

      <section>
        <div className="grid gap-4 sm:grid-cols-3">
          <Metric label="已注册内测用户" value={String(creators.length)} note="不包含运营账号" />
          <Metric label="已完成画像" value={`${completedProfiles}/${creators.length}`} note="用于后续个性化" />
          <Metric label="可用邀请码" value={String(unusedInvites)} note={`累计已使用 ${invites.length - unusedInvites} 个`} />
        </div>
      </section>

      <section>
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="eyebrow">Beta Users</p>
            <h2 className="mt-2 font-serif text-2xl text-cloud">受邀用户</h2>
            <p className="mt-2 text-sm text-fog">当前阶段只看账号、画像和反馈，不显示付费与邮件数据。</p>
          </div>
          <button onClick={load} className="self-start rounded-full border border-steel px-4 py-2 text-xs text-fog hover:border-cyan hover:text-cyan">刷新</button>
        </div>
        <input value={query} onChange={(event) => setQuery(event.target.value)} className="input mt-5 h-11 max-w-xl" placeholder="搜索用户邮箱或画像定位" />
        <div className="mt-5 overflow-hidden rounded-card border border-steel bg-white shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead className="border-b border-steel bg-abyss/60 font-mono text-[10px] uppercase tracking-widest text-fog">
                <tr><th className="px-5 py-3 font-normal">用户</th><th className="px-4 py-3 font-normal">注册时间</th><th className="px-4 py-3 font-normal">画像</th><th className="px-4 py-3 font-normal">提交反馈</th></tr>
              </thead>
              <tbody className="divide-y divide-steel/80">
                {filtered.map((creator) => (
                  <tr key={creator.id} className="hover:bg-abyss/25">
                    <td className="px-5 py-4"><p className="font-medium text-cloud">{creator.email}</p><p className="mt-1 max-w-[300px] truncate text-xs text-fog">{creator.profile_positioning || "尚未填写创作者画像"}</p></td>
                    <td className="px-4 py-4 text-xs text-fog">{fmtTime(creator.created_at)}</td>
                    <td className="px-4 py-4"><span className={`rounded-full border px-2.5 py-1 text-xs ${creator.has_profile ? "border-emerald-200 bg-emerald-50 text-emerald-700" : "border-amber-200 bg-amber-50 text-amber-700"}`}>{creator.has_profile ? "已完成" : "待填写"}</span></td>
                    <td className="px-4 py-4 text-xs text-silver">{creator.product_feedback_count} 条</td>
                  </tr>
                ))}
                {!filtered.length && <tr><td colSpan={4} className="px-5 py-12 text-center text-sm text-fog">没有符合条件的内测用户。</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section>
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div><p className="eyebrow">Invitations</p><h2 className="mt-2 font-serif text-2xl text-cloud">邀请码</h2><p className="mt-2 text-sm text-fog">仅在需要邀请新用户时生成，已使用的邀请码保留记录。</p></div>
          <button onClick={createInvites} disabled={busy} className="self-start rounded-full bg-cyan px-5 py-2.5 text-sm text-white disabled:opacity-45">{busy ? "生成中…" : "生成 5 个"}</button>
        </div>
        <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {invites.map((invite) => (
            <article key={invite.id} className={`rounded-card border p-5 ${invite.used ? "border-steel bg-abyss/35" : "border-cyan/20 bg-white shadow-sm"}`}>
              <p className={`font-mono text-base ${invite.used ? "text-fog line-through" : "text-cloud"}`}>{invite.code}</p>
              <p className="mt-2 text-xs text-fog">{invite.used ? `已使用${invite.used_at ? ` · ${invite.used_at.slice(0, 10)}` : ""}` : "未使用"}</p>
            </article>
          ))}
          {!invites.length && <div className="paper-card rounded-card p-8 text-sm text-fog sm:col-span-2">目前还没有邀请码。</div>}
        </div>
      </section>
    </div>
  );
}

function Metric({ label, value, note }: { label: string; value: string; note: string }) {
  return <article className="paper-card rounded-card p-5"><p className="font-mono text-[10px] uppercase tracking-widest text-fog">{label}</p><p className="mt-3 font-serif text-3xl text-cloud">{value}</p><p className="mt-2 text-xs text-fog">{note}</p></article>;
}
