@echo off
chcp 65001 >nul
REM 选择语音音色。按安装位置依次找引擎：
REM   1) ~/.claude/      = AI 装的（给AI的安装指令.md 那条路，推荐）
REM   2) ~/.task-voice/  = install.py 装的
REM   3) 工具包 engine/  = 还没装，仅试听（选择结果不会生效）
set TARGET=%USERPROFILE%\.claude\pick-voice.ps1
if not exist "%TARGET%" set TARGET=%USERPROFILE%\.task-voice\pick-voice.ps1
if not exist "%TARGET%" set TARGET=%~dp0engine\pick-voice.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%TARGET%"
echo.
pause
