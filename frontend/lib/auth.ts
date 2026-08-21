// 登录态：运营工作台与普通用户使用独立会话，避免同域多标签登录互相覆盖。
const TOKEN_KEY = "weilan_token";
const USER_KEY = "weilan_user";
const USER_SESSION_KEY = "weilan_user_session";
const OPERATOR_SESSION_KEY = "weilan_operator_session";

export type AuthUser = { id: number; email: string; is_operator: boolean };
export type AuthScope = "user" | "operator";
type AuthSession = { token: string; user: AuthUser };

function inferredScope(): AuthScope {
  if (typeof window !== "undefined" && window.location.pathname.startsWith("/ops")) {
    return "operator";
  }
  return "user";
}

function sessionKey(scope: AuthScope): string {
  return scope === "operator" ? OPERATOR_SESSION_KEY : USER_SESSION_KEY;
}

function parseUser(raw: string | null): AuthUser | null {
  if (!raw) return null;
  try {
    const user = JSON.parse(raw) as Partial<AuthUser>;
    if (typeof user.id !== "number" || typeof user.email !== "string" || typeof user.is_operator !== "boolean") {
      return null;
    }
    return user as AuthUser;
  } catch {
    return null;
  }
}

function readSession(scope: AuthScope): AuthSession | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(sessionKey(scope));
  if (raw) {
    try {
      const session = JSON.parse(raw) as Partial<AuthSession>;
      const user = parseUser(session.user ? JSON.stringify(session.user) : null);
      if (typeof session.token === "string" && session.token && user) return { token: session.token, user };
    } catch {
      // 损坏的会话按未登录处理，继续尝试一次旧格式兼容。
    }
  }

  // 兼容升级前的双 key 登录态；运营页还会通过 /auth/me 校验其真实性。
  const token = localStorage.getItem(TOKEN_KEY);
  const user = parseUser(localStorage.getItem(USER_KEY));
  if (!token || !user) return null;
  const matchesScope = scope === "operator" ? user.is_operator : !user.is_operator;
  return matchesScope ? { token, user } : null;
}

export function getToken(scope: AuthScope = inferredScope()): string | null {
  return readSession(scope)?.token ?? null;
}

export function getUser(scope: AuthScope = inferredScope()): AuthUser | null {
  return readSession(scope)?.user ?? null;
}

export function setAuthSession(token: string, user: AuthUser) {
  const scope: AuthScope = user.is_operator ? "operator" : "user";
  localStorage.setItem(sessionKey(scope), JSON.stringify({ token, user } satisfies AuthSession));
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function clearAuth(scope: AuthScope = inferredScope()) {
  localStorage.removeItem(sessionKey(scope));
  // 清理升级前旧格式，防止错误会话再次被兼容逻辑读回。
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function isLoggedIn(): boolean {
  return !!getToken();
}
