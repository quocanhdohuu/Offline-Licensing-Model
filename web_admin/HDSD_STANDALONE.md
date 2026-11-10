# HƯỚNG DẪN KHỞI CHẠY BẢN STANDALONE WEB QUẢN TRỊ OLM

---

## 1. Yêu cầu môi trường máy tính
- **Python**: 3.10 trở lên (đã tích vào "Add Python to PATH" khi cài đặt).
- **Node.js**: 18 trở lên (kèm `npm`).

---

## 2. Cài đặt thư viện lần đầu (Nếu máy mới chưa cài)

Mở Terminal tại thư mục này và chạy 2 lệnh:
```powershell
# 1. Cài đặt thư viện Backend
cd backend
pip install -r requirements.txt
cd ..

# 2. Cài đặt thư viện Frontend
cd frontend
npm install
cd ..
```

---

## 3. Khởi động hệ thống (1-Click)
- Click đúp vào file: **`run_admin_demo.bat`**
- Trình duyệt sẽ tự động mở trang web tại: **`http://localhost:5173`**
- Tài khoản đăng nhập:
  - **Quản trị viên (Admin)**: `admin` / `admin123`
  - **Kinh doanh (Sale)**: `sale` / `sale123`

---

## 4. Tắt hệ thống
- Click đúp vào file: **`stop_demo.bat`** (hoặc tắt các cửa sổ terminal).

