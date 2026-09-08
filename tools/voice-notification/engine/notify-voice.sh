#!/bin/bash
# notify-voice.sh -- task voice notify engine (macOS)
# Plays edge-tts neural mp3 via afplay; falls back to `say` if mp3 missing/unplayable.
# Self-contained: locate everything relative to this script.
#   <dir>/notify-voice.sh   <dir>/voice_clips/<voice>/<type>.mp3
#   <dir>/choice.txt (chosen voice)   <dir>/.flag (long-task marker)
# Usage: notify-voice.sh <mode> ["custom text"]
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

# Resolve which Claudian tab we are, so the announcement can say "对话N".
# Opt-in: set TIKBIT_VAULT_ROOT to the Obsidian vault root. Unset = feature off,
# prints 0, and everything behaves exactly like the single-tab version.
# Mirrors Get-TabIndex in notify-voice.ps1 -- keep the two in sync.
tab_index() {
  local sid="${CLAUDE_CODE_SESSION_ID:-$CODEX_THREAD_ID}"
  [ -z "$sid" ] && { echo 0; return; }
  [ -z "$TIKBIT_VAULT_ROOT" ] && { echo 0; return; }
  command -v python3 >/dev/null 2>&1 || { echo 0; return; }

  TV_SID="$sid" python3 - "$TIKBIT_VAULT_ROOT" <<'PY' 2>/dev/null || echo 0
import json, os, sys
root = sys.argv[1]
sid  = os.environ.get("TV_SID", "")
sessions = os.path.join(root, ".claudian", "sessions")
data     = os.path.join(root, ".obsidian", "plugins", "tikbit-claudian", "data.json")
if not (sid and os.path.isdir(sessions) and os.path.isfile(data)):
    print(0); raise SystemExit
try:
    with open(data, encoding="utf-8") as f:
        tabs = json.load(f).get("tabManagerState", {}).get("openTabs") or []
except Exception:
    print(0); raise SystemExit

# openTabs order IS the number the user sees. Only touch those few meta files;
# the sessions dir grows into the hundreds and most entries are closed chats.
fresh_slot, fresh_stamp = 0, -1
for i, tab in enumerate(tabs):
    cid = str(tab.get("conversationId") or "")
    if not cid:
        continue
    meta_path = os.path.join(sessions, cid + ".meta.json")
    if not os.path.isfile(meta_path):
        continue
    try:
        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)
    except Exception:
        continue
    ps = meta.get("providerState") or {}
    ids = [str(meta.get("sessionId") or ""),
           str(ps.get("providerSessionId") or ""),
           str(ps.get("threadId") or "")]
    if sid in [x for x in ids if x]:
        print(i + 1); raise SystemExit
    # No id on disk = that tab never finished a turn = "fresh" candidate.
    if not any(ids):
        try:
            stamp = int(meta.get("updatedAt") or 0)
        except (TypeError, ValueError):
            stamp = 0
        if stamp >= fresh_stamp:
            fresh_stamp, fresh_slot = stamp, i + 1

# Fallback by elimination: on a brand-new conversation's FIRST turn the plugin
# has not written sessionId yet, so the exact match above always misses. The
# newest not-yet-persisted tab is the only unclaimed slot -- that is us.
print(fresh_slot)
PY
}

# Announce with the tab number when we can work out which tab we are.
# Degrades in three steps: pregenerated dialogN_<key>.mp3 -> spoken labelled
# phrase -> plain generic clip (only when the tab feature is off/unresolvable).
announce() {
  local key="$1"
  local slot="${2:-0}"
  [ "$slot" -eq 0 ] 2>/dev/null && slot="$(tab_index)"
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
case "$MODE" in
  flag) touch "$FLAG"; exit 0 ;;
  done)  announce done ;;
  stuck) announce stuck ;;
  error) announce error ;;
  wait)  announce wait ;;
  ask)   announce ask ;;
  perm)
    # a caller that already knows the tab index may pass it as $2
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
