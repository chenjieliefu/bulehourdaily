"""URL 规范化与确定性去重（纯函数，便于单测）。"""
import hashlib
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

# 常见追踪参数，去重时忽略
TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "utm_id", "fbclid", "gclid", "gclsrc", "dclid", "mc_cid", "mc_eid",
    "igshid", "spm", "scm", "cmpid", "ncid", "mkt_tok", "vero_id",
    "wickedid", "yclid", "_ga", "_gl", "ref", "ref_src", "ref_url",
}


def normalize_url(url: str) -> str:
    """规范化：小写 scheme/host、去默认端口、去追踪参数、去锚点、去尾部斜杠。"""
    if not url:
        return ""
    url = url.strip()
    parts = urlsplit(url)

    scheme = parts.scheme.lower()
    if scheme not in ("http", "https"):
        return ""

    netloc = parts.netloc.lower()
    # 去掉用户信息（若有）
    if "@" in netloc:
        netloc = netloc.rsplit("@", 1)[1]
    # 去掉默认端口
    if scheme == "http" and netloc.endswith(":80"):
        netloc = netloc[:-3]
    elif scheme == "https" and netloc.endswith(":443"):
        netloc = netloc[:-4]
    if not netloc:
        return ""

    path = parts.path.rstrip("/") or "/"

    kept_query = [
        (k, v)
        for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if k.lower() not in TRACKING_PARAMS
    ]
    query = urlencode(kept_query)

    return urlunsplit((scheme, netloc, path, query, ""))


def url_hash(url: str) -> str:
    """规范化后 URL 的 SHA-256，作为去重键。"""
    return hashlib.sha256(normalize_url(url).encode("utf-8")).hexdigest()
