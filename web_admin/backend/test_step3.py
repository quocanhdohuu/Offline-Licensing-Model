from starlette.testclient import TestClient
from main import app

client = TestClient(app)

def test_step3():
    print("=" * 65)
    print(" BẮT ĐẦU KIỂM THỬ BƯỚC 3: HỆ THỐNG REST API & PHÂN QUYỀN RBAC")
    print("=" * 65)

    # 1. Test Login Admin
    res_admin_login = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert res_admin_login.status_code == 200, f"Login admin thất bại: {res_admin_login.text}"
    admin_data = res_admin_login.json()
    admin_token = admin_data["access_token"]
    assert admin_data["user"]["role"] == "ADMIN"
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print("[+] 1. Đăng nhập Admin thành công: Nhận Token & Vai trò ADMIN (PASSED)")

    # 2. Test Login Sale
    res_sale_login = client.post("/api/auth/login", json={"username": "sale", "password": "sale123"})
    assert res_sale_login.status_code == 200, f"Login sale thất bại: {res_sale_login.text}"
    sale_data = res_sale_login.json()
    sale_token = sale_data["access_token"]
    assert sale_data["user"]["role"] == "SALE"
    sale_headers = {"Authorization": f"Bearer {sale_token}"}
    print("[+] 2. Đăng nhập Sale thành công: Nhận Token & Vai trò SALE (PASSED)")

    # 3. Test Login sai mật khẩu
    res_fail = client.post("/api/auth/login", json={"username": "admin", "password": "wrongpassword"})
    assert res_fail.status_code == 401
    print("[+] 3. Kiểm tra bảo mật mật khẩu sai -> Trả về 401 Unauthorized (PASSED)")

    # 4. Test Tra cứu danh sách License (Role SALE)
    res_lics = client.get("/api/licenses", headers=sale_headers)
    assert res_lics.status_code == 200
    all_lics = res_lics.json()
    assert len(all_lics) >= 3
    print(f"[+] 4. Sale xem danh sách License: Thành công ({len(all_lics)} thiết bị) (PASSED)")

    # 5. Test Tìm kiếm tức thời theo Số điện thoại khách hàng (Role SALE)
    res_search = client.get("/api/licenses?q=0912345678", headers=sale_headers)
    assert res_search.status_code == 200
    search_results = res_search.json()
    assert len(search_results) == 1
    assert "Newland" in search_results[0]["model"]
    print(f"[+] 5. Sale tìm kiếm theo SĐT '0912345678' -> Tìm thấy: {search_results[0]['model']} (PASSED)")

    # 6. Test Xem chi tiết & Lấy lại License cho khách (Role SALE)
    target_id = search_results[0]["id"]
    res_detail = client.get(f"/api/licenses/{target_id}", headers=sale_headers)
    assert res_detail.status_code == 200
    detail_data = res_detail.json()
    assert detail_data["qr_code_base64"].startswith("data:image/png;base64,")
    print(f"[+] 6. Sale xem chi tiết & lấy lại QR Code cấp lại cho khách -> OK (PASSED)")

    # 7. PHÂN QUYỀN: Sale cố tình gọi API tạo License mới -> Phải bị chặn 403 Forbidden!
    import time
    ts_suffix = str(int(time.time()))[-4:]
    test_df_code = f"TEST-1234-5678-{ts_suffix}"

    new_payload = {
        "df": test_df_code,
        "model": "Honeywell CT40",
        "customer_name": "Kho Vận Hải Phòng",
        "customer_phone": "0933221100",
        "license_type": "PRO",
        "days_valid": 365,
        "is_permanent": False
    }
    res_forbidden = client.post("/api/licenses", json=new_payload, headers=sale_headers)
    assert res_forbidden.status_code == 403, f"Lỗi phân quyền: Sale lại tạo được license! Status: {res_forbidden.status_code}"
    print(f"[+] 7. BẢO MẬT PHÂN QUYỀN: Chặn Sale tạo key -> Trả về 403 Forbidden chính xác (PASSED)")

    # 8. Admin gọi API tạo License mới -> Thành công 201 Created!
    res_create = client.post("/api/licenses", json=new_payload, headers=admin_headers)
    assert res_create.status_code == 201, f"Admin tạo key lỗi: {res_create.text}"
    created_lic = res_create.json()
    assert created_lic["df"] == test_df_code
    assert created_lic["version"] == 1
    print(f"[+] 8. Admin sinh License mới ({created_lic['model']} - v{created_lic['version']}) -> Ký số thành công (PASSED)")

    # 9. PHÂN QUYỀN: Sale cố tình nâng cấp gói -> Bị chặn 403 Forbidden!
    upgrade_payload = {
        "license_type": "PRO",
        "is_permanent": True,
        "notes": "Nâng cấp từ Trial lên Vĩnh viễn"
    }
    res_up_forbidden = client.post(f"/api/licenses/{created_lic['id']}/upgrade", json=upgrade_payload, headers=sale_headers)
    assert res_up_forbidden.status_code == 403
    print(f"[+] 9. BẢO MẬT PHÂN QUYỀN: Chặn Sale nâng cấp gói -> Trả về 403 Forbidden (PASSED)")

    # 10. Admin thực hiện nâng cấp License -> Thành công (version tăng lên 2, permanent=True)
    res_upgrade = client.post(f"/api/licenses/{created_lic['id']}/upgrade", json=upgrade_payload, headers=admin_headers)
    assert res_upgrade.status_code == 200
    upgraded_lic = res_upgrade.json()
    assert upgraded_lic["version"] == 2
    assert upgraded_lic["is_permanent"] is True
    assert upgraded_lic["status"] == "ACTIVE"
    print(f"[+] 10. Admin nâng cấp License lên PRO Vĩnh viễn (Version: {upgraded_lic['version']}) -> Thành công (PASSED)")

    # 11. Test tải file ảnh QR PNG và file .lic
    res_qr = client.get(f"/api/licenses/{upgraded_lic['id']}/download-qr", headers=sale_headers)
    assert res_qr.status_code == 200
    assert res_qr.headers["content-type"] == "image/png"
    assert len(res_qr.content) > 500

    res_lic_file = client.get(f"/api/licenses/{upgraded_lic['id']}/download-lic", headers=sale_headers)
    assert res_lic_file.status_code == 200
    assert b"eyJ" in res_lic_file.content
    print(f"[+] 11. Tải file ảnh QR Code PNG và file .lic trực tiếp -> Thành công (PASSED)")

    # 12. Test Thống kê (Stats)
    res_stats_sale = client.get("/api/stats", headers=sale_headers)
    assert res_stats_sale.status_code == 403 # Sale không được xem

    res_stats_admin = client.get("/api/stats", headers=admin_headers)
    assert res_stats_admin.status_code == 200
    stats = res_stats_admin.json()
    assert stats["total_devices"] >= 4
    assert stats["permanent_licenses"] >= 2
    print(f"[+] 12. Thống kê Dashboard Admin: {stats['total_devices']} máy, {stats['permanent_licenses']} vĩnh viễn (PASSED)")

    print("=" * 65)
    print(">>> TOÀN BỘ KIỂM THỬ BƯỚC 3: XUẤT SẮC THÀNH CÔNG 100% (ALL PASSED) <<<")
    print("=" * 65)

if __name__ == "__main__":
    test_step3()

