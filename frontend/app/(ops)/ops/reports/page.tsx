"use client";

import { useCallback, useEffect, useState } from "react";
import { DataState, OperationsPageHeader, OperationsSection } from "@/app/components/operations/OperationsPage";
import ReportPreviewDialog from "@/app/components/operations/ReportPreviewDialog";
import { getReport, listReports, type Report } from "@/lib/api";
import { fmtTime } from "@/lib/format";

export default function ReportsOperationsPage() {
  const [rows, setRows] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [previewReport, setPreviewReport] = useState<Report | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const summaries = await listReports();
      setRows(await Promise.all(summaries.map((report) => getReport(report.id))));
    } catch (e) {
      setError(e instanceof Error ? e.message : "日报记录加载失败");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { // eslint-disable-next-line react-hooks/set-state-in-effect
    void load();
  }, [load]);

  return (
    <>
      <OperationsPageHeader
        eyebrow="Report History"
        title="日报记录"
        description="公开日报的草稿与发布历史。这里用于追溯，不承担用户侧阅读导航。"
      />
      <OperationsSection>
        {(loading || error || !rows.length) ? (
          <DataState loading={loading} error={error} empty="暂无日报记录" onRetry={load} />
        ) : (
          <div className="overflow-x-auto rounded-card border border-steel bg-white">
            <table className="w-full min-w-[720px] text-left text-sm">
              <thead className="bg-abyss/60 font-mono text-[10px] uppercase tracking-widest text-fog">
                <tr>
                  <th className="px-5 py-3 font-normal">日期</th>
                  <th className="px-4 py-3 font-normal">状态</th>
                  <th className="px-4 py-3 font-normal">内容</th>
                  <th className="px-4 py-3 font-normal">发布时间</th>
                  <th className="px-5 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-steel">
                {rows.map((row) => (
                  <tr key={row.id}>
                    <td className="px-5 py-4 font-medium text-cloud">{row.report_date}</td>
                    <td className="px-4 py-4">
                      <span className={`rounded-full border px-2.5 py-1 text-xs ${row.status === "published" ? "border-emerald-200 bg-emerald-50 text-emerald-700" : "border-amber-200 bg-amber-50 text-amber-700"}`}>
                        {row.status === "published" ? "已发布" : "草稿"}
                      </span>
                    </td>
                    <td className="px-4 py-4 text-fog">{row.topics.length} 主选题 · {row.briefs.length} 简讯</td>
                    <td className="px-4 py-4 text-fog">{fmtTime(row.published_at)}</td>
                    <td className="px-5 py-4 text-right">
                      <button type="button" onClick={() => setPreviewReport(row)} className="text-xs text-cyan hover:underline">
                        预览
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </OperationsSection>

      <ReportPreviewDialog
        open={previewReport !== null}
        report={previewReport}
        onClose={() => setPreviewReport(null)}
      />
    </>
  );
}
