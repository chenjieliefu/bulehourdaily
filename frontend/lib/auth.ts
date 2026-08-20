// 登录态：MVP 简化，token 存 localStorage（生产上线前收紧，见阶段4文档）。
const TOKEN_KEY = "weilan_token";
const USER_KEY = "weilan_user";

export type AuthUser = { id: number; email: string };

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function setUser(user: AuthUser) {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function getUser(): AuthUser | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(USER_KEY);
  return raw ? (JSON.parse(raw) as AuthUser) : null;
}

export function clearAuth() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function isLoggedIn(): boolean {
  return !!getToken();
}

// 运营者访问口令（本地存，用于质检页）
const OPERATOR_KEY = "weilan_operator_key";

export function getOperatorKey(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(OPERATOR_KEY);
}

export function setOperatorKey(key: string) {
  localStorage.setItem(OPERATOR_KEY, key);
}

export function clearOperatorKey() {
  localStorage.removeItem(OPERATOR_KEY);
}
