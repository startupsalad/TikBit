"""ai-radar 抓取器离线测试。零网络、零第三方依赖。

跑法（二选一）：
    python tests/test_fetch.py      # 纯标准库，自带 runner
    pytest tests/test_fetch.py      # 装了 pytest 也能跑
"""

import importlib.util
import sys
from pathlib import Path

# 以文件路径加载 scripts/fetch.py（它是独立脚本，非包）
_FETCH = Path(__file__).resolve().parent.parent / "scripts" / "fetch.py"
_spec = importlib.util.spec_from_file_location("fetch", _FETCH)
fetch = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fetch)


SAMPLE_RSS = """<?xml version="1.0"?>
<rss version="2.0"><channel><title>X</title>
  <item>
    <title>SuperModel 3.0 released</title>
    <link>https://ex.com/a</link>
    <pubDate>Fri, 12 Jun 2026 08:00:00 +0000</pubDate>
    <description><![CDATA[<p>2x <b>reasoning</b> perf.</p>]]></description>
  </item>
  <item>
    <title>No link item</title>
    <description>should be dropped</description>
  </item>
</channel></rss>"""

SAMPLE_ATOM = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>Agentic coding tips</title>
    <link href="https://ex.com/b"/>
    <updated>2026-06-11T15:30:00Z</updated>
    <summary>ship faster</summary>
  </entry>
</feed>"""

TRENDING_HTML = """
<article class="Box-row"><h2><a href="/acme/llm-toolkit">acme/llm-toolkit</a></h2></article>
<article class="Box-row"><h2><a href="/foo/pasta-recipes">foo/pasta-recipes</a></h2></article>
"""


def test_parse_since():
    assert fetch.parse_since("36h") == 36 * 3600
    assert fetch.parse_since("7d") == 7 * 86400
    assert fetch.parse_since("30d") == 30 * 86400
    assert fetch.parse_since("garbage") == 36 * 3600  # 非法回落默认


def test_strip_html():
    out = fetch._strip_html("<p>hello <b>world</b></p>")
    assert "<" not in out and "hello" in out and "world" in out


def test_parse_feed_rss():
    items = fetch.parse_feed(SAMPLE_RSS)
    assert len(items) == 1  # 无 link 的被丢弃
    assert items[0]["title"] == "SuperModel 3.0 released"
    assert items[0]["url"] == "https://ex.com/a"
    assert items[0]["published_at"] is not None
    assert "<" not in items[0]["summary_raw"]


def test_parse_feed_atom():
    items = fetch.parse_feed(SAMPLE_ATOM)
    assert len(items) == 1
    assert items[0]["url"] == "https://ex.com/b"
    assert items[0]["title"] == "Agentic coding tips"


def test_within():
    import time

    now = time.time()
    assert fetch._within(None, now) is True  # 无时间戳保留
    from datetime import datetime, timezone

    old = datetime(2000, 1, 1, tzinfo=timezone.utc).isoformat()
    assert fetch._within(old, now) is False


def test_run_dynamic_routing():
    """全 dynamic 源 → 无网络调用，应路由到 dynamic_sources。"""
    sources = [
        {"name": "X: @sama", "category": "social", "method": "dynamic", "query": "Sam Altman", "enabled": True},
        {"name": "Disabled", "category": "vendor", "method": "rss", "url": "http://x", "enabled": False},
    ]
    result = fetch.run(sources, fetch.parse_since("36h"), None)
    assert result["items"] == []
    assert len(result["dynamic_sources"]) == 1
    assert result["dynamic_sources"][0]["name"] == "X: @sama"
    assert result["stats"]["sources_failed"] == 0


def test_github_trending_parser():
    p = fetch._TrendingParser()
    p.feed(TRENDING_HTML)
    assert "acme/llm-toolkit" in p.repos
    # AI 正则过滤在 fetch_github_trending 里；这里只验证解析出仓库名
    assert any("pasta" in r for r in p.repos)


def test_hf_spaces_registered():
    # 社区 / AI 应用跟踪：HF Spaces 抓取器已注册
    assert "hf_spaces" in fetch.FETCHERS


def test_format_stars():
    assert fetch._format_stars(999) == "999"
    assert fetch._format_stars(1000) == "1k"
    assert fetch._format_stars(1530) == "1.5k"


def test_github_stars_daily_uses_recent_created_window():
    from datetime import datetime, timezone

    calls = []
    fake_now = datetime(2026, 6, 12, tzinfo=timezone.utc).timestamp()

    def fake_http_get_json(url):
        calls.append(url)
        return {
            "items": [
                {
                    "full_name": "new/agent-kit",
                    "html_url": "https://github.com/new/agent-kit",
                    "stargazers_count": 420,
                    "language": "Python",
                    "description": "Fresh AI agent toolkit",
                    "created_at": "2026-06-10T00:00:00Z",
                    "pushed_at": "2026-06-11T00:00:00Z",
                },
                {
                    "full_name": "old/agent-kit",
                    "html_url": "https://github.com/old/agent-kit",
                    "stargazers_count": 99000,
                    "language": "Python",
                    "description": "Old but recently pushed",
                    "created_at": "2020-01-01T00:00:00Z",
                    "pushed_at": "2026-06-11T00:00:00Z",
                },
                {
                    "full_name": "new/plain-tool",
                    "html_url": "https://github.com/new/plain-tool",
                    "stargazers_count": 9999,
                    "language": "Go",
                    "description": "Fresh but unrelated tool",
                    "created_at": "2026-06-10T00:00:00Z",
                    "pushed_at": "2026-06-11T00:00:00Z",
                },
            ]
        }

    old_http_get_json = fetch.http_get_json
    old_time = fetch.time.time
    try:
        fetch.http_get_json = fake_http_get_json
        fetch.time.time = lambda: fake_now
        out = fetch.fetch_github_stars(
            {
                "name": "GitHub AI 项目雷达",
                "category": "community",
                "query": ["topic:ai-agents"],
                "periods": {"daily": {"lookback_days": 7, "min_stars": 50, "limit": 10}},
            },
            cutoff_ts=fake_now - fetch.parse_since("36h"),
        )
    finally:
        fetch.http_get_json = old_http_get_json
        fetch.time.time = old_time

    assert calls and "created:>2026-06-05" in calls[0]
    assert "pushed:>" not in calls[0]
    assert [i["url"] for i in out] == ["https://github.com/new/agent-kit"]
    assert out[0]["published_at"] == "2026-06-10T00:00:00Z"
    assert out[0]["extra"]["github_period"] == "daily"


def test_github_stars_weekly_uses_30_day_momentum_window():
    from datetime import datetime, timezone

    calls = []
    fake_now = datetime(2026, 6, 12, tzinfo=timezone.utc).timestamp()

    def fake_http_get_json(url):
        calls.append(url)
        return {
            "items": [
                {
                    "full_name": "month/agent-kit",
                    "html_url": "https://github.com/month/agent-kit",
                    "stargazers_count": 880,
                    "language": "TypeScript",
                    "description": "AI agent workflow toolkit",
                    "created_at": "2026-05-20T00:00:00Z",
                    "pushed_at": "2026-06-11T00:00:00Z",
                },
                {
                    "full_name": "older/agent-kit",
                    "html_url": "https://github.com/older/agent-kit",
                    "stargazers_count": 99000,
                    "language": "Python",
                    "description": "AI agent toolkit created too early",
                    "created_at": "2026-04-01T00:00:00Z",
                    "pushed_at": "2026-06-11T00:00:00Z",
                },
            ]
        }

    old_http_get_json = fetch.http_get_json
    old_time = fetch.time.time
    try:
        fetch.http_get_json = fake_http_get_json
        fetch.time.time = lambda: fake_now
        out = fetch.fetch_github_stars(
            {
                "name": "GitHub AI 项目雷达",
                "category": "community",
                "query": ["topic:ai-agents"],
                "periods": {"weekly": {"lookback_days": 30, "min_stars": 100, "limit": 10}},
            },
            cutoff_ts=fake_now - fetch.parse_since("7d"),
        )
    finally:
        fetch.http_get_json = old_http_get_json
        fetch.time.time = old_time

    assert calls and "created:>2026-05-13" in calls[0]
    assert "stars:>100" in calls[0]
    assert "pushed:>" not in calls[0]
    assert [i["url"] for i in out] == ["https://github.com/month/agent-kit"]
    assert out[0]["extra"]["github_period"] == "weekly"
    assert out[0]["summary_raw"].startswith("周报·近30天动量项目")


def test_github_stars_monthly_uses_foundation_active_window():
    from datetime import datetime, timezone

    calls = []
    fake_now = datetime(2026, 6, 12, tzinfo=timezone.utc).timestamp()

    def fake_http_get_json(url):
        calls.append(url)
        return {
            "items": [
                {
                    "full_name": "foundation/langchain-ai",
                    "html_url": "https://github.com/foundation/langchain-ai",
                    "stargazers_count": 92000,
                    "language": "Python",
                    "description": "LLM application framework for agents",
                    "created_at": "2020-01-01T00:00:00Z",
                    "pushed_at": "2026-06-01T00:00:00Z",
                },
                {
                    "full_name": "stale/agent-kit",
                    "html_url": "https://github.com/stale/agent-kit",
                    "stargazers_count": 50000,
                    "language": "Python",
                    "description": "AI agent toolkit no longer active",
                    "created_at": "2020-01-01T00:00:00Z",
                    "pushed_at": "2025-01-01T00:00:00Z",
                },
                {
                    "full_name": "foundation/plain-db",
                    "html_url": "https://github.com/foundation/plain-db",
                    "stargazers_count": 100000,
                    "language": "Go",
                    "description": "database engine",
                    "created_at": "2018-01-01T00:00:00Z",
                    "pushed_at": "2026-06-01T00:00:00Z",
                },
            ]
        }

    old_http_get_json = fetch.http_get_json
    old_time = fetch.time.time
    try:
        fetch.http_get_json = fake_http_get_json
        fetch.time.time = lambda: fake_now
        out = fetch.fetch_github_stars(
            {
                "name": "GitHub AI 项目雷达",
                "category": "community",
                "query": ["topic:llm"],
                "periods": {"monthly": {"active_days": 180, "min_stars": 5000, "limit": 10}},
            },
            cutoff_ts=fake_now - fetch.parse_since("30d"),
        )
    finally:
        fetch.http_get_json = old_http_get_json
        fetch.time.time = old_time

    assert calls and "pushed:>2025-12-14" in calls[0]
    assert "stars:>5000" in calls[0]
    assert "created:>" not in calls[0]
    assert [i["url"] for i in out] == ["https://github.com/foundation/langchain-ai"]
    assert out[0]["published_at"] == "2026-06-01T00:00:00Z"
    assert out[0]["extra"]["github_period"] == "monthly"
    assert out[0]["extra"]["freshness"] == "pushed"


# ── 零依赖 runner ──
def _main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL {t.__name__}: {e}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  ERROR {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_main())
