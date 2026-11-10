import os
from database import SessionLocal
from models import User, Device, License, AuditLog
from auth_utils import verify_password
from crypto_service import generate_license_jwt, normalize_df
from seed_data import init_and_seed_database

def test_step2():
    print("=" * 60)
    print(" BẮT ĐẦU KIỂM THỬ BƯỚC 2: DATABASE & CRYPTO SERVICE ED25519")
    print("=" * 60)

    # 1. Chạy seed
    init_and_seed_database()

    db = SessionLocal()
    try:
        # 2. Kiểm tra users
        admin = db.query(User).filter(User.username == "admin").first()
        sale = db.query(User).filter(User.username == "sale").first()
        assert admin is not None, "Không tìm thấy user admin!"
        assert sale is not None, "Không tìm thấy user sale!"
        assert admin.role == "ADMIN", "Role admin không khớp!"
        assert sale.role == "SALE", "Role sale không khớp!"
        assert verify_password("admin123", admin.password_hash), "Mật khẩu admin băm không hợp lệ!"
        assert verify_password("sale123", sale.password_hash), "Mật khẩu sale băm không hợp lệ!"
        print("[+] Kiểm tra User (Admin & Sale): THÀNH CÔNG (PASSED)")

        # 3. Kiểm tra Devices & Licenses
        devices = db.query(Device).all()
        assert len(devices) >= 3, f"Số lượng thiết bị không đủ: {len(devices)}"
        for dev in devices:
            assert len(dev.licenses) > 0, f"Thiết bị {dev.model} chưa có license!"
            lic = dev.licenses[0]
            assert lic.status == "ACTIVE"
            assert lic.license_jwt.startswith("eyJ") # Chuỗi Base64 Header JWT
            assert lic.qr_code_base64.startswith("data:image/png;base64,")
            print(f"    - Thiết bị: {dev.model} | DF: {dev.df} | Gói: {lic.license_type} | QR: OK")
        print("[+] Kiểm tra Lưu trữ Device & License DB: THÀNH CÔNG (PASSED)")

        # 4. Kiểm thử sinh License mới bằng Ed25519
        test_df = "ABCD-EFGH-JKMN-PQRS"
        res = generate_license_jwt(
            df=test_df,
            license_type="PRO",
            days_valid=30,
            customer="Công ty Kiểm Thử",
            model="Newland MT90 Test"
        )
        assert res["verified"] is True, "Chữ ký số Ed25519 không khớp với Public Key!"
        assert res["norm_df"] == "ABCD-EFGH-JKMN-PQRS"
        assert res["jwt_token"].count(".") == 2, "Token JWT không đúng định dạng 3 phần!"
        print(f"[+] Kiểm thử Ký số Ed25519 & Tự đối soát Public Key: HỢP LỆ 100% (PASSED)")

        # 5. Kiểm thử bắt lỗi mã DF sai bảng Crockford
        try:
            normalize_df("ABCD-EFGH-IIII-OOOO") # I và O không thuộc Crockford
            assert False, "Không bắt được lỗi ký tự I/O ngoài Crockford!"
        except ValueError as ve:
            print(f"[+] Bắt lỗi DF Crockford chuẩn xác: {ve}")

        print("=" * 60)
        print(">>> TOÀN BỘ KIỂM THỬ BƯỚC 2: XUẤT SẮC THÀNH CÔNG (ALL PASSED) <<<")
        print("=" * 60)

    finally:
        db.close()

if __name__ == "__main__":
    test_step2()

