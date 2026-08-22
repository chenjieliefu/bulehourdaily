"use client";

import { useEffect, useRef } from "react";

type PublicSitePreviewDialogProps = {
  open: boolean;
  onClose: () => void;
};

export default function PublicSitePreviewDialog({ open, onClose }: PublicSitePreviewDialogProps) {
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
      aria-labelledby="public-site-preview-title"
      data-public-preview
      onCancel={(event) => {
        event.preventDefault();
        onClose();
      }}
      className="m-auto h-[94vh] w-[min(96vw,1440px)] overflow-hidden rounded-[24px] border border-steel bg-white p-0 text-cloud shadow-2xl backdrop:bg-slate-950/45 backdrop:backdrop-blur-sm"
    >
      <div className="flex h-full flex-col">
        <header className="flex shrink-0 items-center justify-between gap-4 border-b border-steel bg-white px-5 py-3 sm:px-6">
          <div>
            <h2 id="public-site-preview-title" className="font-serif text-xl text-cloud">公开站点预览</h2>
            <p className="mt-0.5 text-xs text-fog">访客视角 · 关闭预览后继续留在运营工作台</p>
          </div>
          <button
            ref={closeButtonRef}
            type="button"
            onClick={onClose}
            aria-label="关闭公开站点预览"
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-xl text-fog transition-colors hover:bg-abyss hover:text-cloud"
          >
            ×
          </button>
        </header>

        {open && (
          <iframe
            src="/"
            title="公开站点访客视角"
            className="min-h-0 flex-1 border-0 bg-white"
          />
        )}
      </div>
    </dialog>
  );
}
