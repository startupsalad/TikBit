@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo   PPT 风格速查图册
echo   地址: http://localhost:8199/templates/style-picker.html
echo   浏览器会自动打开；关闭本窗口即停止服务器。
echo ============================================
echo.
start "" cmd /c "timeout /t 2 >nul & start http://localhost:8199/templates/style-picker.html"
python -m http.server 8199
