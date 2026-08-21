export function OperationsPageHeader({ eyebrow, title, description, actions }: {
  eyebrow: string;
  title: string;
  description?: string;
  actions?: React.ReactNode;
}) {
  return (
    <header className="flex flex-col gap-5 border-b border-steel/80 pb-7 pt-8 md:flex-row md:items-end md:justify-between lg:pt-10">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h1 className="mt-2 font-serif text-3xl text-cloud">{title}</h1>
        {description && <p className="mt-2 max-w-3xl text-sm leading-6 text-fog">{description}</p>}
      </div>
      {actions && <div className="shrink-0">{actions}</div>}
    </header>
  );
}

export function OperationsSection({ children }: { children: React.ReactNode }) {
  return <div className="py-8">{children}</div>;
}

export function DataState({ loading, error, empty, onRetry }: {
  loading?: boolean;
  error?: string | null;
  empty?: string;
  onRetry?: () => void;
}) {
  if (loading) return <div className="paper-card rounded-card p-10 text-center text-sm text-fog">正在加载本地运营数据…</div>;
  if (error) return <div className="rounded-card border border-red-200 bg-red-50 p-6 text-sm text-red-700"><p>{error}</p>{onRetry && <button onClick={onRetry} className="mt-3 rounded-full border border-red-300 px-4 py-1.5 text-xs">重试</button>}</div>;
  return <div className="paper-card rounded-card p-10 text-center text-sm text-fog">{empty || "暂无数据"}</div>;
}
