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

# pick a Chinese system voice for `say` fallback; empty = system default
say_voice() {
  for v in Tingting Meijia Sinji Yue; do
    if say -v '?' 2>/dev/null | grep -qi "^$v "; then echo "$v"; return; fi
  done
  echo ""
}

play_clip() {
  local key="$1"
  local mp3="$CLIPDIR/$VOICE/$key.mp3"
  if [ -f "$mp3" ] && command -v afplay >/dev/null 2>&1; then
    afplay "$mp3" && return 0
  fi
  # fallback: say
  local txt; txt="$(fb_text "$key")"
  [ -z "$txt" ] && return 0
  local sv; sv="$(say_voice)"
  if [ -n "$sv" ]; then say -v "$sv" "$txt"; else say "$txt"; fi
}

MODE="${1:-done}"
case "$MODE" in
  flag) touch "$FLAG"; exit 0 ;;
  done)  play_clip done ;;
  stuck) play_clip stuck ;;
  error) play_clip error ;;
  perm)  play_clip perm ;;
  wait)  play_clip wait ;;
  ask)   play_clip ask ;;
  done-if-flagged)
    if [ -f "$FLAG" ]; then rm -f "$FLAG"; play_clip done; fi ;;
  notify)
    raw="$(cat)"
    key="stuck"
    case "$raw" in
      *permission*|*approve*|*allow*|*授权*|*批准*) key="perm" ;;
      *waiting*|*idle*|*input*|*等待*|*输入*)       key="wait" ;;
    esac
    play_clip "$key" ;;
  say)
    txt="$2"; [ -z "$txt" ] && exit 0
    sv="$(say_voice)"
    if [ -n "$sv" ]; then say -v "$sv" "$txt"; else say "$txt"; fi ;;
  *)
    txt="$MODE"
    sv="$(say_voice)"
    if [ -n "$sv" ]; then say -v "$sv" "$txt"; else say "$txt"; fi ;;
esac
