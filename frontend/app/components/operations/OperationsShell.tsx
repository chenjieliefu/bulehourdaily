"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import Brand from "@/app/components/Brand";
import PublicSitePreviewDialog from "@/app/components/operations/PublicSitePreviewDialog";
import { apiCurrentUser } from "@/lib/api";
import { clearAuth, getToken, getUser, setAuthSession } from "@/lib/auth";

const NAV = [
  { label: "日报运营", items: [
    { href: "/ops", label: "今日工作台", icon: "◉" },
    { href: "/ops/reports", label: "日报记录", icon: "▤" },
    { href: "/ops/sources", label: "信息源", icon: "◎" },
  ] },
  { label: "内测运营", items: [
    { href: "/ops/users", label: "内测用户", icon: "♙" },
    { href: "/ops/product-feedback", label: "用户反馈", icon: "□" },
  ] },
];

export default function OperationsShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [ready, setReady] = useState(false);
  const [email, setEmail] = useState("");
  const [mobileOpen, setMobileOpen] = useState(false);
  const [previewOpen, setPreviewOpen] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const cachedUser = getUser("operator");
    const token = getToken("operator");
    if (!cachedUser?.is_operator || !token) {
      router.replace("/?auth=login&next=%2Fops");
      return;
    }

    async function verifyOperator() {
      try {
        const user = await apiCurrentUser();
        if (!user.is_operator) throw new Error("无运营者权限");
        if (cancelled) return;
        setAuthSession(token!, user);
        setEmail(user.email);
        setReady(true);
      } catch {
        clearAuth("operator");
        if (!cancelled) router.replace("/?auth=login&next=%2Fops");
      }
    }
    void verifyOperator();
    return () => { cancelled = true; };
  }, [router]);

  useEffect(() => { // eslint-disable-next-line react-hooks/set-state-in-effect
    setMobileOpen(false); }, [pathname]);

  const active = (href: string) => href === "/ops" ? pathname === href : pathname.startsWith(href);

  function logout() {
    clearAuth("operator");
    router.replace("/");
  }

  if (!ready) return <div className="flex min-h-screen items-center justify-center text-sm text-fog">正在验证运营身份…</div>;

  return (
    <div className="min-h-screen bg-[#f7f9f8] lg:flex">
      <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-steel bg-white/95 px-5 backdrop-blur lg:hidden">
        <Brand compact />
        <button onClick={() => setMobileOpen(!mobileOpen)} className="rounded-lg border border-steel px-3 py-2 text-sm text-cloud" aria-expanded={mobileOpen}>菜单</button>
      </header>

      <aside className={`${mobileOpen ? "block" : "hidden"} fixed inset-x-0 bottom-0 top-16 z-20 overflow-y-auto border-r border-steel bg-[#eef4f6] lg:sticky lg:top-0 lg:block lg:h-screen lg:w-[264px] lg:shrink-0`}>
        <div className="hidden border-b border-steel px-6 py-6 lg:block">
          <Link href="/ops"><Brand compact /></Link>
          <p className="mt-3 font-mono text-[10px] uppercase tracking-[0.2em] text-fog">Operations</p>
        </div>
        <nav className="space-y-5 px-4 py-5" aria-label="运营工作台导航">
          {NAV.map((group) => (
            <section key={group.label}>
              <p className="mb-1.5 px-3 font-mono text-[10px] uppercase tracking-[0.16em] text-fog/80">{group.label}</p>
              <div className="space-y-0.5">
                {group.items.map((item) => (
                  <Link key={item.href} href={item.href} className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition ${active(item.href) ? "bg-white font-medium text-cloud shadow-sm ring-1 ring-steel/80" : "text-ash hover:bg-white/60 hover:text-cloud"}`}>
                    <span className={`flex h-6 w-6 items-center justify-center rounded-md font-mono text-xs ${active(item.href) ? "bg-pale-iris text-cyan" : "text-fog"}`}>{item.icon}</span>
                    {item.label}
                  </Link>
                ))}
              </div>
            </section>
          ))}
        </nav>
        <div className="border-t border-steel px-4 py-4 lg:sticky lg:bottom-0 lg:bg-[#eef4f6]">
          <button
            type="button"
            onClick={() => setPreviewOpen(true)}
            className="flex w-full items-center justify-between rounded-xl px-3 py-2 text-left text-xs text-fog hover:bg-white/60 hover:text-cloud"
          >
            <span>查看公开站点</span>
            <span>预览</span>
          </button>
          <div className="mt-2 rounded-xl border border-steel bg-white/70 px-3 py-3">
            <p className="truncate text-xs text-cloud">{email}</p>
            <button onClick={logout} className="mt-2 text-[11px] text-fog hover:text-red-600">退出运营账号</button>
          </div>
        </div>
      </aside>

      <main className="min-w-0 flex-1 px-5 pb-20 sm:px-8 lg:px-10 xl:px-14">
        <div className="mx-auto max-w-[1280px]">{children}</div>
      </main>

      <PublicSitePreviewDialog open={previewOpen} onClose={() => setPreviewOpen(false)} />
    </div>
  );
}
