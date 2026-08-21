"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { clearAuth, getUser, isLoggedIn } from "@/lib/auth";
import Brand from "@/app/components/Brand";

type NavIconName = "membership" | "feedback" | "about";
type NavItem = { href?: string; label: string; soon?: boolean; icon?: NavIconName };

// 上组：内容
const TOP_GROUP: NavItem[] = [
  { href: "/mine", label: "订阅日报" },
  { href: "/", label: "公开日报" },
  { href: undefined, label: "邮箱日报", soon: true },
  { href: "/archive", label: "往期归档" },
  { href: undefined, label: "我的收藏", soon: true },
];

const OPERATOR_GROUP: NavItem[] = [
  { href: "/ops", label: "返回运营工作台" },
  { href: "/", label: "公开日报" },
];

// 下组：账户与商业（展示顺序从上到下）
const BOTTOM_GROUP: NavItem[] = [
  { href: "/review", label: "运营工作台" },
  { href: "/upgrade", label: "升级会员", icon: "membership" },
  { href: "/feedback", label: "意见反馈", icon: "feedback" },
  { href: "/landing", label: "产品介绍", icon: "about" },
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

  const contentItems = isOperator ? OPERATOR_GROUP : TOP_GROUP;

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
        {contentItems.map((item) => (
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
        {(isOperator ? [] : BOTTOM_GROUP.filter((item) => item.href !== "/review")).map((item) => (
          item.href ? (
            <Link key={item.label} href={item.href} className={itemCls(item)}>
              <span className="inline-flex items-center gap-3">
                {item.icon && <NavIcon name={item.icon} />}
                {item.label}
              </span>
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
            onClick={() => router.push(isOperator ? "/ops" : "/profile")}
            className="flex w-full items-center gap-3 rounded-card border border-steel bg-white/80 px-3 py-2.5 text-left shadow-sm transition-all hover:border-cyan/40 hover:bg-white"
          >
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-cyan font-serif text-sm text-white">
              {(email?.[0] ?? "微").toUpperCase()}
            </span>
            <span className="min-w-0 flex-1">
              <span className="block truncate text-sm text-cloud">{email}</span>
              <span className="block font-mono text-[10px] text-fog">{isOperator ? "返回运营工作台" : "点击编辑我的画像"}</span>
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

function NavIcon({ name }: { name: NavIconName }) {
  if (name === "membership") {
    return (
      <svg aria-hidden="true" viewBox="0 0 24 24" className="h-4 w-4 shrink-0" fill="none" stroke="currentColor" strokeWidth="1.8">
        <path d="M4 8.5 7.5 12 12 5l4.5 7L20 8.5 18.5 18h-13L4 8.5Z" strokeLinejoin="round" />
        <path d="M7 21h10" strokeLinecap="round" />
      </svg>
    );
  }

  if (name === "feedback") {
    return (
      <svg aria-hidden="true" viewBox="0 0 24 24" className="h-4 w-4 shrink-0" fill="none" stroke="currentColor" strokeWidth="1.8">
        <path d="M5 5.5h14v10H9l-4 3v-13Z" strokeLinejoin="round" />
        <path d="M8 9h8M8 12h5" strokeLinecap="round" />
      </svg>
    );
  }

  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" className="h-4 w-4 shrink-0" fill="none" stroke="currentColor" strokeWidth="1.8">
      <circle cx="12" cy="12" r="8" />
      <path d="M12 11v5M12 8h.01" strokeLinecap="round" />
    </svg>
  );
}
