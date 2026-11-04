@echo off
chcp 65001 > nul
echo =======================================================
echo [TÂN HƯNG HÀ] TIẾN HÀNH TẠO LICENSE DEMO CHO PDA MT90
echo =======================================================
python license_gen.py --df 9A2B-X7Y8-AT6Y-4F2E --type PRO --days 365 --customer "Tân Hưng Hà Test" --model "NLS-MT90"
echo.
pause

