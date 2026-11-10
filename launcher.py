import os
import sys
import time
import subprocess
import webbrowser

# Đảm bảo UTF-8 trên Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(CURRENT_DIR, "web_admin", "backend")
FRONTEND_DIR = os.path.join(CURRENT_DIR, "web_admin", "frontend")

def main():
    print("=" * 75)
    print("      TÂN HƯNG HÀ - CỔNG QUẢN TRỊ BẢN QUYỀN OFFLINE (PDA OLM PORTAL)")
    print("=" * 75)
    print()

    # 1. Khởi động Backend FastAPI
    print("[1/3] Đang khởi động Backend FastAPI (Port 8000)...")
    backend_cmd = [sys.executable, "-m", "uvicorn", "main:app", "--reload", "--host", "127.0.0.1", "--port", "8000"]
    backend_proc = subprocess.Popen(
        backend_cmd,
        cwd=BACKEND_DIR,
        shell=True
    )

    # 2. Khởi động Frontend React Vite
    print("[2/3] Đang khởi động Frontend React (Port 5173)...")
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    frontend_cmd = [npm_cmd, "run", "dev"]
    frontend_proc = subprocess.Popen(
        frontend_cmd,
        cwd=FRONTEND_DIR,
        shell=True
    )

    # 3. Đợi một lát và tự động mở trình duyệt
    print("[3/3] Đang đợi server sẵn sàng (3 giây)...")
    time.sleep(3)

    target_url = "http://localhost:5173"
    print(f"[✓] Đang mở trình duyệt tới: {target_url}")
    try:
        webbrowser.open(target_url)
    except Exception as e:
        print(f"[!] Không thể tự mở trình duyệt: {e}")

    print()
    print("=" * 75)
    print("       HỆ THỐNG ĐÃ SẴN SÀNG HOẠT ĐỘNG!")
    print("=" * 75)
    print(f"  * Web Quản trị (React) : {target_url}")
    print("  * Backend API Docs     : http://127.0.0.1:8000/docs")
    print()
    print("  Tài khoản đăng nhập:")
    print("    - Quản Trị Viên (Admin) : admin  /  admin123")
    print("    - Kinh Doanh (Sale)     : sale   /  sale123")
    print("=" * 75)
    print(">> Nhấn phím ENTER hoặc Ctrl+C tại cửa sổ này để DỪNG toàn bộ hệ thống <<")
    print()

    try:
        input()
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        print("\nĐang dừng các tiến trình máy chủ...")
        try:
            backend_proc.terminate()
            frontend_proc.terminate()
        except Exception:
            pass
        if sys.platform == "win32":
            os.system("taskkill /f /im node.exe >nul 2>&1")
        print("[✓] Đã dừng toàn bộ hệ thống thành công. Tạm biệt!")

if __name__ == "__main__":
    main()

