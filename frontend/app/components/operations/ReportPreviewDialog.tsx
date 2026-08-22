"use client";

import { useEffect, useRef } from "react";
import ReportView from "@/app/components/ReportView";
import type { Report } from "@/lib/api";

type ReportPreviewDialogProps = {
  open: boolean;
  report: Report | null;
  onClose: () => void;
};

export default function ReportPreviewDialog({ open, report, onClose }: ReportPreviewDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    if (open && !dialog.open) {
      dialog.showModal();
      requestAnimationFrame(() => closeButtonRef.current?.focus());
    } else if (!open && dialog.open) {
      dialog.close();
    }
  }, [open]);

  return (
    <dialog
      ref={dialogRef}
      aria-labelledby="report-preview-title"
      data-report-preview
      onCancel={(event) => {
        event.preventDefault();
        onClose();
      }}
      className="m-auto h-[94vh] w-[min(96vw,1440px)] overflow-hidden rounded-[24px] border border-steel bg-[#f7f9f8] p-0 text-cloud shadow-2xl backdrop:bg-slate-950/45 backdrop:backdrop-blur-sm"
    >
      <div className="flex h-full flex-col">
        <header className="flex shrink-0 items-center justify-between gap-4 border-b border-steel bg-white px-5 py-3 sm:px-6">
          <div>
            <h2 id="report-preview-title" className="font-serif text-xl text-cloud">日报展示预览</h2>
            <p className="mt-0.5 text-xs text-fog">
              {report ? `${report.report_date} · ${report.status === "published" ? "已发布" : "草稿"}` : "日报记录"}
            </p>
          </div>
          <button
            ref={closeButtonRef}
            type="button"
            onClick={onClose}
            aria-label="关闭日报展示预览"
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-xl text-fog transition-colors hover:bg-abyss hover:text-cloud"
          >
            ×
          </button>
        </header>

        <div className="min-h-0 flex-1 overflow-y-auto px-4 pb-8 sm:px-6 lg:px-10">
          {open && report && <ReportView report={report} />}
        </div>
      </div>
    </dialog>
  );
}
