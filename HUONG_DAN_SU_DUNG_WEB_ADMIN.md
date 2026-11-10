# HƯỚNG DẪN VẬN HÀNH & KIỂM THỬ DEMO WEB QUẢN TRỊ LICENSE (TÂN HƯNG HÀ OLM)

---

## 1. KHỞI ĐỘNG HỆ THỐNG (CHỈ 1 CLICK)

Để khởi động toàn bộ hệ thống gồm cả Backend (FastAPI) và Frontend (React Vite):
- Click đúp chuột vào file: **`run_admin_demo.bat`** tại thư mục gốc của dự án.
- Trình duyệt web sẽ tự động mở trang chủ tại địa chỉ: **`http://localhost:5173`**
- Backend API Docs (Swagger UI) hoạt động tại: **`http://127.0.0.1:8000/docs`**

*(Khi muốn dừng hệ thống, bạn chỉ cần click đúp vào file `stop_demo.bat`)*

---

## 2. TÀI KHOẢN ĐĂNG NHẬP HỆ THỐNG

Hệ thống đã tích hợp sẵn tính năng **"1-Click Demo Login"** trên màn hình đăng nhập:

| Vai trò | Tên đăng nhập | Mật khẩu | Quyền hạn chính |
| :--- | :--- | :--- | :--- |
| **Quản Trị Viên (Admin)** | `admin` | `admin123` | **Toàn quyền**: Xem thống kê KPI, sinh license mới từ DF, nâng cấp gói Trial lên Pro Vĩnh viễn, xem và tải QR code. |
| **Kinh Doanh (Sale)** | `sale` | `sale123` | **Hỗ trợ khách**: Tra cứu danh sách, tìm kiếm theo SĐT/DF, xem và lấy lại mã QR/Token cấp lại khi khách mất key. **Không có quyền** tạo mới hay nâng cấp gói. |

---

## 3. CÁC KỊCH BẢN KIỂM THỬ NGHIỆM THU THỰC TẾ (UAT SCENARIOS)

### 📌 Kịch bản 1: Kiểm thử Phân quyền (Role-Based Access Control)
1. Trên màn hình đăng nhập, bấm nút **[Đăng nhập KINH DOANH (Sale)]**.
2. **Quan sát giao diện**:
   - Header hiển thị Huy hiệu màu xanh lục: `KINH DOANH (SALE)`.
   - Nút `+ Cấp License Mới` **hoàn toàn biến mất**.
   - Cụm thẻ thống kê KPI **bị ẩn**.
   - Trong bảng danh sách, cột thao tác **chỉ có duy nhất nút `[Xem & Cấp lại]`** (không có nút Nâng cấp).
3. Đăng xuất và bấm nút **[Đăng nhập QUẢN TRỊ VIÊN (Admin)]**:
   - Header hiển thị Huy hiệu màu đỏ tím: `QUẢN TRỊ VIÊN (ADMIN)`.
   - Xuất hiện cụm **Thẻ Thống Kê KPI** (Tổng số PDA, Pro vĩnh viễn, Trial, Hết hạn).
   - Xuất hiện nút nổi bật **`[+ Cấp License Mới]`** ở góc trên bên phải.
   - Mỗi dòng thiết bị xuất hiện thêm nút **`[Nâng cấp]`**.

---

### 📌 Kịch bản 2: Khách hàng Mới & Admin Cấp License Mới
1. Đăng nhập tài khoản **Admin**.
2. Bấm nút **[+ Cấp License Mới]** ở góc trên bên phải màn hình.
3. Trong Modal:
   - **Nhập mã DF**: Gõ thử `ABCD-EFGH-JKMN-PQRS` (ô nhập tự động chuyển chữ HOA và tự chèn dấu gạch). Thử gõ các ký tự cấm như `I` hoặc `O` để xem hệ thống cảnh báo chuẩn Crockford Base32.
   - **Chọn Model**: Chọn `Newland NLS-MT90` hoặc `Zebra MC3300x`.
   - **Tên khách hàng**: Nhập `Công ty Kho Vận Tân Cảng`.
   - **Số điện thoại**: `0977889900`.
   - **Gói bản quyền**: Chọn `DÙNG THỬ (TRIAL)` 15 ngày (hoặc tích chọn Vĩnh viễn).
4. Bấm nút **[Sinh License & Ký Số Ed25519]**:
   - Hệ thống xử lý ký số mật mã trong 0.2 giây.
   - Modal hiển thị ngay thông báo thành công kèm **Mã QR Code bản quyền chất lượng cao**.
   - Bấm **[Tải ảnh QR (PNG)]** để lưu file ảnh về máy tính.
   - Bấm **[Sao chép chuỗi Token]** để copy vào Clipboard.
5. Đóng modal $\rightarrow$ Thiết bị vừa tạo xuất hiện ngay ở dòng đầu tiên của bảng dữ liệu.

---

### 📌 Kịch bản 3: Khách hàng Factory Reset / Xóa App $\rightarrow$ Sale Tra cứu & Cấp lại Tức Thì
1. Đăng nhập tài khoản **Sale** (`sale` / `sale123`).
2. Giả lập tình huống: Khách hàng gọi điện báo máy Newland MT90 bị nhân viên xóa app hoặc chạy lại cài đặt gốc bị mất bản quyền.
3. Sale nhập số điện thoại của khách: `0912345678` (hoặc gõ mã DF `MN73`) vào ô tìm kiếm:
   - Bảng dữ liệu tự động lọc ra ngay thiết bị `Newland NLS-MT90` của `Công ty Cổ phần Vận tải Á Châu`.
4. Sale bấm nút **[Xem & Cấp lại]**:
   - Popup mở ra hiển thị to rõ mã QR Code bản quyền hiện hành.
   - Bấm **[Tải ảnh QR Code (PNG)]**: File ảnh `qr_MN73006Q5G96S3E8.png` lập tức được tải về máy tính để Sale gửi qua Zalo/Email cho khách.
   - Bấm **[Sao chép gửi khách]** để copy chuỗi Token JWT.
5. Khách hàng mở app PDA quét lại mã QR trên màn hình máy tính $\rightarrow$ **Ứng dụng lập tức được kích hoạt trở lại 100% Offline**.

---

### 📌 Kịch bản 4: Nâng cấp Bản quyền từ Dùng Thử lên PRO Vĩnh Viễn
1. Đăng nhập tài khoản **Admin** (`admin` / `admin123`).
2. Tìm thiết bị đang dùng gói Trial: ví dụ máy **iMin Swift 2** (DF: `B3C4-D5E6-F7G8-H9J1`, đang ở phiên bản `v1`).
3. Bấm nút **[Nâng cấp]** ở cột Thao tác trên dòng máy đó.
4. Trong Modal Nâng cấp:
   - Hệ thống hiển thị mã DF phần cứng cố định của máy.
   - Chọn phương thức: **`Gói PRO VĨNH VIỄN (Perpetual)`**.
   - Nhập ghi chú: *"Khách hàng thanh toán mua đứt bản quyền trọn đời"*.
5. Bấm nút **[Xác Nhận Nâng Cấp & Ký Số Token v2]**:
   - Hệ thống giữ nguyên mã DF của máy, sinh ra chữ ký Ed25519 mới với loại gói `PRO` vĩnh viễn và số hiệu phiên bản tăng lên **v2**.
   - Bảng dữ liệu tự động cập nhật: Huy hiệu gói chuyển từ `TRIAL` sang **`PRO VĨNH VIỄN`**, hạn sử dụng chuyển thành **`Vĩnh viễn`**, version thành **`v2`**.
6. Dùng máy PDA quét mã QR mới $\rightarrow$ App trên PDA tự động nhận diện gói PRO vĩnh viễn thành công!

---

## 4. DANH MỤC THIẾT BỊ MẪU CÓ SẴN ĐỂ TEST NGAY

| Model Thiết Bị | Mã DF (Hardware Fingerprint) | Khách Hàng | Gói Ban Đầu | Trạng Thái |
| :--- | :--- | :--- | :---: | :---: |
| **Newland NLS-MT90** | `MN73-006Q-5G96-S3E8` | Công ty Cổ phần Vận tải Á Châu | **PRO (1 năm)** | Đang kích hoạt |
| **Zebra MC3300x** | `9A2B-X7Y8-AT6Y-4F2E` | Tập đoàn Bán lẻ Tân Hưng Hà | **PRO Vĩnh viễn** | Đang kích hoạt |
| **iMin Swift 2** | `B3C4-D5E6-F7G8-H9J1` | Chuỗi Cà phê Sài Gòn Phố | **TRIAL (15 ngày)** | Đang kích hoạt |

---
*Tài liệu được đóng gói phục vụ nghiệm thu dự án Cổng Quản trị Tân Hưng Hà Offline Licensing Model (OLM).*

