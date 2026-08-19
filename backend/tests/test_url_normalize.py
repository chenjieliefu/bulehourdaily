"""URL 规范化与去重纯函数测试。"""
from app.services.url_normalize import normalize_url, url_hash


def test_strip_tracking_params():
    assert (
        normalize_url("https://example.com/post?utm_source=x&utm_medium=y&a=1")
        == "https://example.com/post?a=1"
    )


def test_lowercase_scheme_and_host():
    assert normalize_url("HTTPS://Example.COM/Path") == "https://example.com/Path"


def test_remove_trailing_slash():
    assert normalize_url("https://example.com/post/") == "https://example.com/post"


def test_remove_fragment():
    assert normalize_url("https://example.com/post#section") == "https://example.com/post"


def test_remove_default_ports():
    assert normalize_url("https://example.com:443/x") == "https://example.com/x"
    assert normalize_url("http://example.com:80/x") == "http://example.com/x"


def test_invalid_scheme_returns_empty():
    assert normalize_url("ftp://example.com/x") == ""
    assert normalize_url("") == ""


def test_same_url_same_hash():
    a = "https://example.com/post?utm_source=tw&x=1"
    b = "https://example.com/post?x=1"
    assert url_hash(a) == url_hash(b)


def test_different_url_different_hash():
    assert url_hash("https://example.com/a") != url_hash("https://example.com/b")
