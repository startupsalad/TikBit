#!/bin/bash
# pick-voice.sh -- choose voice (macOS). Writes choice.txt next to this script.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLIPDIR="$HERE/voice_clips"

keys=(xiaoxiao xiaoyi yunxi yunyang)
names=("晓晓 · 温暖女声" "晓伊 · 年轻女声" "云希 · 沉稳男声" "云扬 · 播报男声")

play() { [ -f "$1" ] && command -v afplay >/dev/null 2>&1 && afplay "$1"; }

echo ""
echo "===== 任务语音通知 · 选择音色 ====="
echo "下面依次播放四个音色的「任务完成啦」，听完输入序号选择。"
echo ""
for i in "${!keys[@]}"; do
  echo "  $((i+1)). ${names[$i]}"
  play "$CLIPDIR/${keys[$i]}/done.mp3"
  sleep 0.5
done
echo ""
printf "请输入你要的音色序号 (1-4): "
read sel
if [[ "$sel" =~ ^[1-4]$ ]]; then
  chosen="${keys[$((sel-1))]}"
  printf "%s" "$chosen" > "$HERE/choice.txt"
  echo ""
  echo "已设置为：${names[$((sel-1))]}"
  echo "再听一遍确认："
  play "$CLIPDIR/$chosen/done.mp3"
  echo ""
  echo "搞定。以后任务通知就用这个声音了。"
else
  echo ""
  echo "没选有效序号，没有改动。下次再运行即可。"
fi
echo ""
