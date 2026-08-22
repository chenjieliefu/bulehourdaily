"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ApiError, getReport, type Report } from "@/lib/api";
import { clearAuth } from "@/lib/auth";
import ReportView from "@/app/components/ReportView";

export default function ReportDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        setReport(await getReport(Number(params.id)));
      } catch (e) {
        if (e instanceof ApiError && e.status === 401) {
          clearAuth("user");
          router.replace(`/login?next=${encodeURIComponent(`/reports/${params.id}`)}`);
          return;
        }
        setError(e instanceof Error ? e.message : "加载失败");
      } finally {
        setLoading(false);
      }
    })();
  }, [params.id, router]);

  return (
    <div>
      {loading && <p className="mt-16 text-center text-fog">加载中…</p>}
      {!loading && error && <p className="mt-16 text-center text-red-400">加载失败：{error}</p>}
      {!loading && !error && report && <ReportView report={report} />}
    </div>
  );
}
