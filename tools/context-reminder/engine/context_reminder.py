#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对话长度提醒 · UserPromptSubmit 钩子引擎（跨平台，仅用 Python 标准库）

原理：每次用户发消息时，Claude Code 把一段 JSON 从 stdin 传进来，里面有本次会话的
transcript 路径。我们读那份 transcript，量出"当前上下文有多大"（= 每轮都要被重读、
直接决定花钱的 token 量），到达阈值档位时，把一句提醒写到 stdout。
对 UserPromptSubmit 来说，exit 0 时 stdout 的文本会被直接注入到 Claude 的上下文里——
于是 AI 一定看得到，会主动提醒用户"该开新对话/清上下文了"，不依赖 AI 自觉数轮次。

为什么用"上下文 token 量"而不是"轮次"做触发：
  - 它直接等于成本（长对话每轮重读全部历史，是账单主力）；
  - /clear、/compact 之后会自动回落，不会误报；
  - 同一档位只提醒一次（记在 state.json），不刷屏。

任何异常都静默 exit 0，绝不阻塞用户发消息。
"""
import sys, json, os, time
from pathlib import Path

# ===== 可调阈值（单位：token）。按需改这里即可 =====
BANDS = [
    # (下限, 档位名, 严重度措辞)
    (130_000, "gentle", "已有一定长度，留意一下。"),
    (230_000, "firm",   "已经偏长，每轮都在重读全部历史、成本明显上升。"),
    (350_000, "urgent", "非常长了，每多说一句都在全价重读海量历史、很烧钱。"),
]
STATE_DIR = Path.home() / ".context-reminder"
STATE_FILE = STATE_DIR / "state.json"
STATE_TTL_DAYS = 7  # 清理多少天前的旧会话记录


def fmt(n):
    return f"{n/1_000_000:.1f}M" if n >= 1_000_000 else f"{round(n/1000)}K"


def band_index(ctx):
    """返回当前上下文落在第几档（-1 表示未达任何阈值）。"""
    idx = -1
    for i, (lo, _, _) in enumerate(BANDS):
        if ctx >= lo:
            idx = i
    return idx


def read_context_and_turns(transcript_path):
    """读 transcript，返回 (当前上下文token, 大致用户轮次)。读不到返回 (0,0)。"""
    ctx, turns = 0, 0
    try:
        with open(transcript_path, encoding="utf-8") as fh:
            for line in fh:
                try:
                    o = json.loads(line)
                except Exception:
                    continue
                msg = o.get("message", {}) or {}
                # 统计用户轮次：role=user 且不是工具结果回填
                if o.get("type") == "user" or msg.get("role") == "user":
                    c = msg.get("content")
                    is_tool_result = isinstance(c, list) and any(
                        isinstance(b, dict) and b.get("type") == "tool_result" for b in c
                    )
                    if not is_tool_result:
                        turns += 1
                # 当前上下文 = 最后一条 assistant usage 的 input+cache_read+cache_creation
                u = msg.get("usage") or {}
                if u:
                    cur = (u.get("input_tokens", 0) or 0) \
                        + (u.get("cache_read_input_tokens", 0) or 0) \
                        + (u.get("cache_creation_input_tokens", 0) or 0)
                    if cur > 0:
                        ctx = cur  # 取最后一次（最新上下文规模）
    except Exception:
        return 0, 0
    return ctx, turns


def load_state():
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(state):
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        # 顺手清理过期会话记录，避免文件无限增长
        cutoff = time.time() - STATE_TTL_DAYS * 86400
        state = {k: v for k, v in state.items()
                 if isinstance(v, dict) and v.get("ts", 0) > cutoff}
        STATE_FILE.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def main():
    raw = sys.stdin.read() if not sys.stdin.isatty() else ""
    try:
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        data = {}
    sid = data.get("session_id", "unknown")
    tpath = data.get("transcript_path", "")
    if not tpath or not os.path.exists(tpath):
        return  # 拿不到 transcript，静默退出

    ctx, turns = read_context_and_turns(tpath)
    idx = band_index(ctx)
    if idx < 0:
        return  # 还短，不打扰

    state = load_state()
    prev = state.get(sid, {}).get("band", -1)
    # 改为：超阈值后每轮都提醒，直到开新对话或降档（用 /clear、/compact）
    # 如果降档了（用户清理过上下文），停止提醒；重新涨上来时再报
    if idx < prev:
        # 降档了，更新记录但不提醒（说明用户清理过了）
        state[sid] = {"band": idx, "ts": time.time()}
        save_state(state)
        return

    _, _, words = BANDS[idx]
    turn_txt = f"、约 {turns} 轮" if turns else ""
    # 这段会被注入 Claude 上下文：指示 AI 先判断"压缩还是新开"，再把建议带给用户
    msg = (
        f"[对话长度提醒｜系统自动] 当前对话上下文已约 {fmt(ctx)} token{turn_txt}。{words} "
        f"请你判断当前场景后，用一句自然的话提醒用户：若仍在处理同一件事、只是聊长了，"
        f"建议用 /compact 压缩上下文（保留记忆、挤掉冗余、显著省 token），必要时提示压缩有损、"
        f"精确核对类内容压完留意细节；若已切换到新话题，则建议开新对话（旧话题摘要不必再带着重读）。"
        f"默认优先压缩，除非明显换了话题。不要展开解释钩子原理，说完继续正常回应用户的请求。"
    )
    print(msg)

    state[sid] = {"band": idx, "ts": time.time()}
    save_state(state)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # 任何意外都不阻塞用户
    sys.exit(0)
