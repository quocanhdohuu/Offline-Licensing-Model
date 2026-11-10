@echo off
chcp 65001 >nul
echo ========================================================
echo  ĐANG KHỞI CHẠY BACKEND FASTAPI (TÂN HƯNG HÀ OLM API)
echo ========================================================
echo.
cd /d "%~dp0web_admin\backend"
echo Đang chạy tại: http://127.0.0.1:8000
echo Tài liệu Swagger UI: http://127.0.0.1:8000/docs
echo.
echo Nhấn Ctrl+C để dừng server.
echo --------------------------------------------------------
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
pause

