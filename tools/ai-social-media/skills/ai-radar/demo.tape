# ai-radar demo · vhs 录制脚本（github.com/charmbracelet/vhs）
# 生成: vhs demo.tape  →  demo.gif
Output demo.gif
Set FontSize 16
Set Width 1100
Set Height 600
Set Theme "Catppuccin Mocha"
Set TypingSpeed 55ms

Type "# ai-radar 抓取引擎实跑（可复现，非摆拍）"
Enter
Sleep 800ms
Type "python3 scripts/fetch.py --since 36h > /tmp/radar.json"
Enter
Sleep 4s
Type "python3 -c \"import json;d=json.load(open('/tmp/radar.json'));print('抓取',len(d['items']),'条 ·',d['stats']['sources_ok'],'源OK')\""
Enter
Sleep 2500ms
Type "# 宿主 agent 再把英文源加工成结论先行的中文研报 → samples/daily-sample.md"
Enter
Sleep 2s
