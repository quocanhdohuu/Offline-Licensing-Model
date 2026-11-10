@echo off
chcp 65001 >nul
echo ========================================================
echo  ĐANG KHỞI CHẠY FRONTEND REACT (TÂN HƯNG HÀ OLM PORTAL)
echo ========================================================
echo.
cd /d "%~dp0web_admin\frontend"
echo Đang chạy tại: http://localhost:5173
echo.
echo Nhấn Ctrl+C để dừng server.
echo --------------------------------------------------------
npm.cmd run dev
pause

