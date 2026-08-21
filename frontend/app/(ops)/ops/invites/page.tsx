"use client";

import { useCallback, useEffect, useState } from "react";
import { createInviteCodes, listInviteCodes, type InviteCode } from "@/lib/api";
import { DataState, OperationsPageHeader, OperationsSection } from "@/app/components/operations/OperationsPage";

export default function InvitesOperationsPage() {
  const [rows, setRows] = useState<InviteCode[]>([]); const [busy, setBusy] = useState(false); const [loading, setLoading] = useState(true); const [error, setError] = useState<string | null>(null);
  const load = useCallback(async () => { setLoading(true); setError(null); try { setRows(await listInviteCodes()); } catch (e) { setError(e instanceof Error ? e.message : "邀请码加载失败"); } finally { setLoading(false); } }, []);
  useEffect(() => { // eslint-disable-next-line react-hooks/set-state-in-effect
    void load(); }, [load]);
  async function create() { setBusy(true); try { await createInviteCodes(5); await load(); } catch (e) { setError(e instanceof Error ? e.message : "生成失败"); } finally { setBusy(false); } }
  return <><OperationsPageHeader eyebrow="Invitations" title="邀请码" description="邀请创作者注册的独立入口，避免与日报质检混在同一条任务流里。" actions={<button onClick={create} disabled={busy} className="rounded-full bg-cyan px-5 py-2.5 text-sm text-white disabled:opacity-45">{busy ? "生成中…" : "生成 5 个"}</button>} /><OperationsSection>{(loading || error || !rows.length) ? <DataState loading={loading} error={error} empty="暂无邀请码" onRetry={load} /> : <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">{rows.map((row) => <div key={row.id} className="paper-card rounded-card p-5"><p className={`font-mono text-lg ${row.used ? "text-fog line-through" : "text-cloud"}`}>{row.code}</p><p className="mt-2 text-xs text-fog">{row.used ? `已使用${row.used_at ? ` · ${row.used_at.slice(0, 10)}` : ""}` : "未使用"}</p></div>)}</div>}</OperationsSection></>;
}
