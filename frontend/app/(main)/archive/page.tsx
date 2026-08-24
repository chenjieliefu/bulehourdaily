"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import ReportView from "@/app/components/ReportView";
import LoginDialog from "@/app/components/LoginDialog";
import RegisterDialog from "@/app/components/RegisterDialog";
import { ApiError, getReport, listReports, type Report, type ReportSummary } from "@/lib/api";
import { clearAuth, getUser, isLoggedIn } from "@/lib/auth";
import { fmtDate } from "@/lib/format";

export default function ArchivePage() {
  const router = useRouter();
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [authMode, setAuthMode] = useState<"login" | "register" | null>(
    () => typeof window !== "undefined" && !isLoggedIn() ? "login" : null,
  );
  const [accessVersion, setAccessVersion] = useState(0);

  useEffect(() => {
    if (!isLoggedIn()) {
      return;
    }

    (async () => {
      try {
        const allReports = await listReports();
        const newestDate = allReports[0]?.report_date;
        const archivedReports = newestDate
          ? allReports.filter((report) => report.report_date !== newestDate)
          : [];

        setReports(archivedReports);
        if (archivedReports[0]) setDetailLoading(true);
        setSelectedId(archivedReports[0]?.id ?? null);
      } catch (e) {
        if (e instanceof ApiError && e.status === 401) {
          clearAuth(getUser()?.is_operator ? "operator" : "user");
          setAuthMode("login");
          return;
        }
        setError(e instanceof Error ? e.message : "加载失败");
      } finally {
        setLoading(false);
      }
    })();
  }, [accessVersion]);

  useEffect(() => {
    if (selectedId === null) return;

    let active = true;

    getReport(selectedId)
      .then((report) => {
        if (active) setSelectedReport(report);
      })
      .catch((e) => {
        if (active) setError(e instanceof Error ? e.message : "加载失败");
      })
      .finally(() => {
        if (active) setDetailLoading(false);
      });

    return () => {
      active = false;
    };
  }, [selectedId]);

  const selectedIndex = useMemo(
    () => reports.findIndex((report) => report.id === selectedId),
    [reports, selectedId],
  );

  function selectReport(id: number) {
    if (id === selectedId) return;
    setDetailLoading(true);
    setError(null);
    setSelectedId(id);
  }

  function selectRelative(offset: number) {
    const next = reports[selectedIndex + offset];
    if (next) selectReport(next.id);
  }

  return (
    <div className="mx-auto max-w-[1400px] pb-8">
      <LoginDialog
        open={authMode === "login"}
        onClose={() => {
          setAuthMode(null);
          router.replace("/");
        }}
        onSuccess={() => {
          setAuthMode(null);
          setLoading(true);
          setAccessVersion((version) => version + 1);
        }}
        onRegister={() => setAuthMode("register")}
      />
      <RegisterDialog
        open={authMode === "register"}
        onClose={() => {
          setAuthMode(null);
          router.replace("/");
        }}
        onSuccess={() => {
          setAuthMode(null);
          setLoading(true);
          setAccessVersion((version) => version + 1);
        }}
        onLogin={() => setAuthMode("login")}
      />

      <header className="flex flex-col gap-3 border-b border-steel/80 pb-6 pt-8 sm:flex-row sm:items-end sm:justify-between lg:pt-10">
        <div>
          <p className="eyebrow">Archive</p>
          <h1 className="mt-2 font-serif text-3xl text-cloud md:text-4xl">往期归档</h1>
        </div>
        <p className="max-w-sm text-sm leading-relaxed text-fog sm:text-right">
          归档从上一期开始，今日日报始终留在「公开日报」。
        </p>
      </header>

      {loading && (
        <div className="paper-card mt-8 rounded-feature p-10 text-center">
          <span className="mx-auto block h-2 w-24 animate-pulse rounded-full bg-periwinkle/40" />
          <p className="mt-4 text-sm text-fog">正在整理往期日报…</p>
        </div>
      )}

      {!loading && error && !selectedReport && (
        <div className="mt-8 rounded-card border border-red-200 bg-red-50 p-6 text-center text-red-700">
          加载失败：{error}
        </div>
      )}

      {!loading && !error && reports.length === 0 && (
        <div className="paper-card mt-8 rounded-feature p-10 text-center">
          <p className="font-serif text-xl text-cloud">还没有可归档的日报</p>
          <p className="mt-2 text-sm text-fog">生成第二天的日报后，前一天会自动出现在这里。</p>
        </div>
      )}

      {!loading && reports.length > 0 && (
        <div className="mt-8 grid items-start gap-7 lg:grid-cols-[280px_minmax(0,1fr)]">
          <aside className="paper-card overflow-hidden rounded-feature lg:sticky lg:top-6 lg:max-h-[calc(100vh-3rem)] lg:overflow-y-auto">
            <div className="flex items-center justify-between border-b border-steel px-5 py-5">
              <div>
                <p className="eyebrow">历史列表</p>
                <h2 className="mt-1 font-serif text-xl text-cloud">往期存档</h2>
              </div>
              <span className="rounded-full bg-abyss px-3 py-1 font-mono text-xs text-deep-iris">
                {String(reports.length).padStart(2, "0")}
              </span>
            </div>

            <ol className="divide-y divide-steel">
              {reports.map((report, index) => {
                const active = report.id === selectedId;
                return (
                  <li key={report.id}>
                    <button
                      type="button"
                      onClick={() => selectReport(report.id)}
                      aria-current={active ? "page" : undefined}
                      className={`block w-full px-5 py-5 text-left transition-colors ${
                        active ? "bg-pale-iris/55" : "bg-white/45 hover:bg-abyss/60"
                      }`}
                    >
                      <span className="flex items-center justify-between gap-3">
                        <span className={`font-mono text-[11px] ${active ? "text-cyan" : "text-fog"}`}>
                          {fmtDate(report.report_date)}
                        </span>
                        {index === 0 && (
                          <span className="rounded-full border border-orchid/35 bg-orange-50 px-2 py-0.5 text-[10px] text-amber-700">
                            昨日
                          </span>
                        )}
                      </span>
                      <span className="mt-3 line-clamp-3 block font-serif text-base leading-relaxed text-cloud">
                        {report.summary || "（无摘要）"}
                      </span>
                      <span className={`mt-3 block text-xs ${active ? "text-cyan" : "text-fog"}`}>
                        {active ? "正在阅读" : "查看内容 →"}
                      </span>
                    </button>
                  </li>
                );
              })}
            </ol>
          </aside>

          <section className="min-w-0">
            <div className="flex min-h-12 items-center justify-between gap-4 border-b border-steel/80 pb-4">
              <div className="min-w-0">
                <p className="eyebrow">{selectedIndex === 0 ? "昨日存档内容" : "历史存档内容"}</p>
                <p className="mt-1 truncate text-sm text-fog">
                  {selectedReport ? fmtDate(selectedReport.report_date) : "正在加载"}
                </p>
              </div>
              <div className="flex shrink-0 items-center gap-2.5">
                <button
                  type="button"
                  onClick={() => selectRelative(-1)}
                  disabled={selectedIndex <= 0}
                  className="rounded-full border border-steel bg-white/90 px-4 py-2 text-xs font-medium text-silver shadow-sm transition-colors hover:border-cyan hover:text-cyan disabled:cursor-not-allowed disabled:opacity-35 disabled:shadow-none"
                >
                  ← 较新
                </button>
                <button
                  type="button"
                  onClick={() => selectRelative(1)}
                  disabled={selectedIndex < 0 || selectedIndex >= reports.length - 1}
                  className="rounded-full border border-steel bg-white/90 px-4 py-2 text-xs font-medium text-silver shadow-sm transition-colors hover:border-cyan hover:text-cyan disabled:cursor-not-allowed disabled:opacity-35 disabled:shadow-none"
                >
                  更早 →
                </button>
              </div>
            </div>

            {detailLoading && (
              <div className="paper-card mt-6 rounded-feature p-10 text-center">
                <span className="mx-auto block h-2 w-24 animate-pulse rounded-full bg-periwinkle/40" />
                <p className="mt-4 text-sm text-fog">正在加载存档内容…</p>
              </div>
            )}

            {!detailLoading && error && (
              <div className="mt-6 rounded-card border border-red-200 bg-red-50 p-6 text-center text-red-700">
                加载失败：{error}
              </div>
            )}

            {!detailLoading && !error && selectedReport && (
              <ReportView key={selectedReport.id} report={selectedReport} layout="archive" />
            )}
          </section>
        </div>
      )}
    </div>
  );
}
