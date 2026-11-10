#!/bin/bash
# notify-voice.sh -- task voice notify engine (macOS)
# Plays edge-tts neural mp3 via afplay; falls back to `say` if mp3 missing/unplayable.
# Self-contained: locate everything relative to this script.
#   <dir>/notify-voice.sh   <dir>/voice_clips/<voice>/<type>.mp3
#   <dir>/choice.txt (chosen voice)   <dir>/.flag (long-task marker)
# Usage: notify-voice.sh <mode> ["custom text" | --dry-run]
# TIKBIT_VAULT_ROOT opts into exact visible-tab identity; unknown callers mute.
# Without it, generic clients work; standalone Codex workers are rejected using
# local session_meta. TIKBIT_VOICE_SUPPRESS=1 silences delegated branches.
#   modes: done | stuck | error | perm | wait
#          ask                      (PreToolUse: need a decision -- AskUserQuestion/ExitPlanMode)
#          flag | done-if-flagged   (long-task gating, for Claude Code Stop hook)
#          say "text"               (speak custom text via `say`)
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLIPDIR="$HERE/voice_clips"
CHOICE="$HERE/choice.txt"
FLAG="$HERE/.flag"

# chosen voice (private, set by picker); default xiaoxiao
VOICE="xiaoxiao"
[ -f "$CHOICE" ] && VOICE="$(tr -d '[:space:]' < "$CHOICE")"
[ -z "$VOICE" ] && VOICE="xiaoxiao"

# fallback phrases for `say` (Mac handles UTF-8 directly)
fb_text() {
  case "$1" in
    done)  echo "任务完成啦" ;;
    stuck) echo "任务卡住了，来看一下" ;;
    error) echo "任务出错了，请检查" ;;
    perm)  echo "需要你授权一下" ;;
    wait)  echo "在等你回复呢" ;;
    ask)   echo "需要你拿个主意" ;;
    *)     echo "" ;;
  esac
}

# spoken suffix per type, used only when the numbered clip is absent.
# Keep in sync with $SFX in notify-voice.ps1 and `kinds` in gen-clips.py.
sfx_text() {
  case "$1" in
    done)  echo "，搞定啦" ;;
    perm)  echo "，需要授权一下" ;;
    stuck) echo "，卡住了，来看一下" ;;
    wait)  echo "，在等你回复呢" ;;
    ask)   echo "，需要你拿个主意" ;;
    error) echo "，出错了，请检查" ;;
    *)     echo "，搞定啦" ;;
  esac
}

CN_NUMS=("一" "二" "三" "四" "五" "六" "七" "八" "九" "十")

# pick a Chinese system voice for `say` fallback; empty = system default
say_voice() {
  for v in Tingting Meijia Sinji Yue; do
    if say -v '?' 2>/dev/null | grep -qi "^$v "; then echo "$v"; return; fi
  done
  echo ""
}

speak_text() {
  local txt="$1"
  [ -z "$txt" ] && return 0
  local sv; sv="$(say_voice)"
  if [ -n "$sv" ]; then say -v "$sv" "$txt"; else say "$txt"; fi
}

play_clip() {
  local key="$1"
  local mp3="$CLIPDIR/$VOICE/$key.mp3"
  if [ -f "$mp3" ] && command -v afplay >/dev/null 2>&1; then
    afplay "$mp3" && return 0
  fi
  # fallback: say
  speak_text "$(fb_text "$key")"
}

# Resolve one verified visible tab, or a verified standalone Codex main thread.
# All parsing is read-only; Python 3 is only required for identity-aware calls.
resolve_context() {
  if [ "${TIKBIT_VOICE_SUPPRESS:-}" = "1" ]; then
    printf 'false\t0\texplicit-suppression\n'; return
  fi
  if [ -z "${TIKBIT_VAULT_ROOT:-}" ] && [ -z "${CODEX_THREAD_ID:-}" ]; then
    printf 'true\t0\tstandalone\n'; return
  fi
  if ! command -v python3 >/dev/null 2>&1; then
    printf 'false\t0\tpython3-required\n'; return
  fi
  python3 - <<'PY' 2>/dev/null || printf 'false\t0\tcontext-read-failed\n'
import datetime as dt
import json, os, re
from pathlib import Path

def emit(allowed, tab, reason):
    print(('true' if allowed else 'false') + '\t' + str(tab) + '\t' + reason)

def tab_index(root, sid):
    if not sid:
        return 0
    try:
        with open(Path(root) / '.obsidian/plugins/tikbit-claudian/data.json', encoding='utf-8-sig') as f:
            tabs = json.load(f).get('tabManagerState', {}).get('openTabs') or []
        slot = 0
        for i, tab in enumerate(tabs):
            cid = str(tab.get('conversationId') or '')
            if not cid or cid in ('.', '..') or re.search(r'[\\/:*?"<>|]', cid):
                continue
            try:
                with open(Path(root) / '.claudian/sessions' / (cid + '.meta.json'), encoding='utf-8-sig') as f:
                    meta = json.load(f)
                ps = meta.get('providerState') or {}
                ids = (meta.get('sessionId'), ps.get('providerSessionId'), ps.get('threadId'))
                if sid in ids:
                    if slot:
                        return 0
                    slot = i + 1
            except (OSError, ValueError, TypeError, AttributeError):
                continue
        return slot
    except (OSError, ValueError, TypeError, AttributeError):
        return 0

def codex_kind(tid):
    if not re.fullmatch(r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}', tid):
        return 'unknown'
    home = Path.home()
    roots = [Path(x) for x in (os.environ.get('CODEX_HOME'), home / '.codex', home / '.tikbit/codex') if x]
    now = dt.datetime.now().astimezone()
    dates = {now.strftime('%Y/%m/%d'), (now - dt.timedelta(days=1)).strftime('%Y/%m/%d')}
    if tid[14] == '7':
        try:
            born = dt.datetime.fromtimestamp(int(tid.replace('-', '')[:12], 16) / 1000, dt.timezone.utc)
            dates.update((born.strftime('%Y/%m/%d'), born.astimezone().strftime('%Y/%m/%d')))
        except (ValueError, OverflowError, OSError):
            pass
    main = False
    for root in roots:
        for date in dates:
            try:
                files = (root / 'sessions' / date).glob('rollout-*-' + tid + '.jsonl')
                for file in files:
                    try:
                        with file.open(encoding='utf-8-sig') as f:
                            record = json.loads(f.readline())
                        payload = record.get('payload') or {}
                        if record.get('type') != 'session_meta' or payload.get('id') != tid:
                            continue
                        source = payload.get('source')
                        if payload.get('parent_thread_id') or source == 'subagent' or isinstance(source, dict) and source.get('subagent'):
                            return 'subagent'
                        if isinstance(source, str) and source.strip():
                            main = True
                    except (OSError, ValueError, TypeError, AttributeError):
                        continue
            except OSError:
                continue
    return 'main' if main else 'unknown'

root = os.environ.get('TIKBIT_VAULT_ROOT', '').strip()
tid = os.environ.get('CODEX_THREAD_ID', '').strip()
sid = tid or os.environ.get('CLAUDE_CODE_SESSION_ID', '')
if root:
    slot = tab_index(root, sid)
    emit(slot > 0, slot, 'exact-visible-tab' if slot else 'no-unique-visible-tab')
else:
    kind = codex_kind(tid)
    emit(kind == 'main', 0, 'codex-' + kind if kind != 'unknown' else 'codex-context-unverified')
PY
}

# Announce with the tab number when we can work out which tab we are.
# Verified slots use a numbered clip or one labelled phrase.
# Generic audio is reserved for standalone use, never unmatched opted-in tabs.
announce() {
  local key="$1"
  [ "$VOICE_ALLOWED" = "true" ] || return 0
  local slot="$VOICE_TAB"
  case "$slot" in ''|*[!0-9]*) slot=0 ;; esac

  if [ "$slot" -ge 1 ]; then
    local mp3="$CLIPDIR/claudian_multitab/dialog${slot}_${key}.mp3"
    if [ -f "$mp3" ] && command -v afplay >/dev/null 2>&1; then
      afplay "$mp3" && return 0
    fi
    # Clip missing (tab number beyond what was generated, or a partial install):
    # speak the whole labelled phrase in one go rather than playing the
    # unnumbered clip and then repeating -- the number is the entire point.
    local num="$slot"
    [ "$slot" -le "${#CN_NUMS[@]}" ] && num="${CN_NUMS[$((slot - 1))]}"
    speak_text "对话${num}$(sfx_text "$key")"
    return 0
  fi

  play_clip "$key"
}

MODE="${1:-done}"
# --- context gate ---
IFS=$'\t' read -r VOICE_ALLOWED VOICE_TAB VOICE_REASON <<< "$(resolve_context)"
case "$VOICE_TAB" in ''|*[!0-9]*) VOICE_ALLOWED=false; VOICE_TAB=0; VOICE_REASON=context-read-failed ;; esac
if [ "${2:-}" = "--dry-run" ] || [ "$MODE" = "--dry-run" ]; then
  case "$VOICE_ALLOWED" in true|false) ;; *) VOICE_ALLOWED=false ;; esac
  printf '{"allowed":%s,"tab":%s,"reason":"%s"}\n' "$VOICE_ALLOWED" "$VOICE_TAB" "$VOICE_REASON"
  exit 0
fi
[ "$VOICE_ALLOWED" = "true" ] || exit 0
case "$MODE" in
  flag) touch "$FLAG"; exit 0 ;;
  done)  announce done ;;
  stuck) announce stuck ;;
  error) announce error ;;
  wait)  announce wait ;;
  ask)   announce ask ;;
  perm)
    # Legacy explicit slot cannot override caller identity.
    announce perm "${2:-0}" ;;
  done-if-flagged)
    if [ -f "$FLAG" ]; then rm -f "$FLAG"; announce done; fi ;;
  notify)
    raw="$(cat)"
    # Default to wait, not stuck: most Notification hooks mean "waiting on you".
    key="wait"
    case "$raw" in
      *permission*|*approve*|*allow*|*authoriz*|*授权*|*批准*) key="perm" ;;
      *error*|*failed*|*stuck*|*出错*|*失败*)                 key="stuck" ;;
    esac
    announce "$key" ;;
  say)
    txt="$2"; [ -z "$txt" ] && exit 0
    speak_text "$txt" ;;
  *)
    speak_text "$MODE" ;;
esac
