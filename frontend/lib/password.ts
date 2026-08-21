// 密码规则：只允许 ASCII 可打印非空白字符（码点 33–126）。
// 空格、制表符、换行、中文、全角空格、emoji 会被静默过滤。
export function sanitizePassword(value: string): string {
  let result = "";
  for (const ch of value) {
    const code = ch.codePointAt(0) ?? 0;
    if (code >= 33 && code <= 126) {
      result += ch;
    }
  }
  return result;
}
