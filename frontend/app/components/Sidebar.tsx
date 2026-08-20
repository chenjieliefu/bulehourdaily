"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { clearAuth, getUser, isLoggedIn } from "@/lib/auth";
import Brand from "@/app/components/Brand";

type NavItem = { href?: string; label: string; soon?: boolean };

// 上组：内容
const TOP_GROUP: NavItem[] = [
  { href: "/mine", label: "订阅日报" },
  { href: "/", label: "公开日报" },
  { href: undefined, label: "邮箱日报", soon: true },
  { href: "/archive", label: "往期归档" },
  { href: undefined, label: "我的收藏", soon: true },
];

// 下组：账户与商业（展示顺序从上到下）
const BOTTOM_GROUP: NavItem[] = [
  { href: "/review", label: "运营质检" },
  { href: undefined, label: "升级会员", soon: true },
  { href: undefined, label: "兑换会员", soon: true },
  { href: undefined, label: "邀请送会员", soon: true },
  { href: undefined, label: "意见反馈", soon: true },
  { href: "/landing", label: "产品介绍" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [loggedIn, setLoggedIn] = useState(false);
  const [email, setEmail] = useState<string | null>(null);
  const [isOperator, setIsOperator] = useState(false);

  useEffect(() => {
    // 登录态只存在于浏览器 localStorage，挂载后同步一次（避免服务端渲染水合不一致）
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoggedIn(isLoggedIn());
    setEmail(getUser()?.email ?? null);
    setIsOperator(getUser()?.is_operator ?? false);
  }, [pathname]);

  const isActive = (href?: string) =>
    href ? (href === "/" ? pathname === "/" : pathname.startsWith(href)) : false;

  function logout() {
    clearAuth();
    setLoggedIn(false);
    setEmail(null);
    router.push("/");
  }

  const itemCls = (item: NavItem) =>
    item.soon
      ? "cursor-not-allowed whitespace-nowrap rounded-xl px-3 py-2.5 text-sm text-fog/45"
      : `whitespace-nowrap rounded-xl px-3 py-2.5 text-sm transition-all ${
          isActive(item.href) ? "bg-white text-cloud shadow-sm ring-1 ring-steel" : "text-ash hover:bg-white/65 hover:text-cloud"
        }`;

  return (
    <aside className="flex flex-col border-b border-steel bg-abyss/80 backdrop-blur-xl lg:sticky lg:top-0 lg:h-screen lg:w-[252px] lg:border-b-0 lg:border-r">
      {/* Logo */}
      <div className="border-b border-steel/70 px-5 py-5 lg:py-7">
        <Link href="/" className="inline-flex rounded-xl outline-none transition-opacity hover:opacity-80 focus-visible:ring-2 focus-visible:ring-cyan/40">
          <Brand compact />
        </Link>
      </div>

      {/* 上组：内容 */}
      <nav aria-label="内容导航" className="flex gap-1 overflow-x-auto px-3 py-2 lg:flex-col lg:gap-0.5 lg:px-4 lg:py-5">
        {TOP_GROUP.map((item) => (
          item.href ? (
            <Link key={item.label} href={item.href} className={itemCls(item)}>
              <span className="inline-flex items-center gap-3">
                <span className={`h-1.5 w-1.5 rounded-full ${isActive(item.href) ? "bg-orchid" : "bg-periwinkle/60"}`} />
                {item.label}
              </span>
            </Link>
          ) : (
            <span key={item.label} className={itemCls(item)} title="即将上线">
              <span className="inline-flex items-center gap-3"><span className="h-1.5 w-1.5 rounded-full bg-steel" />{item.label}</span>
            </span>
          )
        ))}
      </nav>

      {/* 下组：账户与商业 */}
      <nav aria-label="账户与服务" className="mt-auto hidden gap-1 overflow-x-auto border-t border-steel/70 px-3 py-3 lg:flex lg:flex-col lg:gap-0.5 lg:px-4 lg:py-4">
        {BOTTOM_GROUP.filter((item) => item.href !== "/review" || isOperator).map((item) => (
          item.href ? (
            <Link key={item.label} href={item.href} className={itemCls(item)}>
              {item.label}
            </Link>
          ) : (
            <span key={item.label} className={itemCls(item)} title="即将上线">{item.label}</span>
          )
        ))}
      </nav>

      {/* 底部：头像 + 账号 */}
      <div className="border-t border-steel/70 px-3 py-4 lg:px-4">
        {loggedIn ? (
          <button
            onClick={() => router.push("/profile")}
            className="flex w-full items-center gap-3 rounded-card border border-steel bg-white/80 px-3 py-2.5 text-left shadow-sm transition-all hover:border-cyan/40 hover:bg-white"
          >
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-cyan font-serif text-sm text-white">
              {(email?.[0] ?? "微").toUpperCase()}
            </span>
            <span className="min-w-0 flex-1">
              <span className="block truncate text-sm text-cloud">{email}</span>
              <span className="block font-mono text-[10px] text-fog">点击编辑我的画像</span>
            </span>
          </button>
        ) : (
          <Link
            href="/login"
            className="flex w-full items-center gap-3 rounded-card border border-steel bg-white/80 px-3 py-2.5 shadow-sm transition-all hover:border-cyan/40 hover:bg-white"
          >
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-steel text-sm text-silver">?</span>
            <span className="text-sm text-ash">登录 / 注册</span>
          </Link>
        )}

        {loggedIn && (
          <button
            onClick={logout}
            className="mt-2 w-full rounded-md px-3 py-1.5 text-left text-xs text-fog transition-colors hover:text-red-400"
          >
            退出登录
          </button>
        )}
      </div>
    </aside>
  );
}
