"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { listReports, type Report } from "@/lib/api";
import { fmtDate } from "@/lib/format";

export default function ArchivePage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        setReports(await listReports());
      } catch (e) {
        setError(e instanceof Error ? e.message : "加载失败");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <div className="mx-auto max-w-[880px]">
      <div className="border-b border-steel pb-8 pt-10">
        <p className="font-mono text-xs uppercase tracking-widest text-fog">Archive</p>
        <h1 className="mt-3 font-serif text-2xl text-cloud md:text-3xl">最近 7 天日报</h1>
      </div>

      {loading && <p className="mt-10 text-fog">加载中…</p>}

      {!loading && error && <p className="mt-10 text-red-400">加载失败：{error}</p>}

      {!loading && !error && reports.length === 0 && (
        <p className="mt-10 text-fog">还没有历史日报。</p>
      )}

      {!loading && !error && reports.length > 0 && (
        <ul className="mt-8 divide-y divide-steel rounded-card border border-steel bg-graphite px-6">
          {reports.map((r) => (
            <li key={r.id}>
              <Link href={`/reports/${r.id}`} className="flex items-baseline gap-4 py-4 transition-colors hover:text-cyan">
                <span className="shrink-0 font-mono text-xs text-deep-iris">{fmtDate(r.report_date)}</span>
                <span className="flex-1 truncate text-sm text-ash">{r.summary || "（无摘要）"}</span>
                <span className="shrink-0 font-mono text-xs text-fog">查看 ↗</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
