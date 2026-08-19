// 时间格式化：数据库存的是无时区 UTC，补 Z 后由浏览器转北京时间显示。
export function fmtTime(t: string | null) {
  if (!t) return "—";
  const s = String(t);
  const d = new Date(/[zZ]|[+-]\d{2}:\d{2}$/.test(s) ? s : s + "Z");
  return d.toLocaleString("zh-CN", { hour12: false });
}

export function fmtDate(d: string) {
  const [y, m, day] = d.split("-");
  return `${y} 年 ${Number(m)} 月 ${Number(day)} 日`;
}
