import os
from database import engine, SessionLocal, Base
from models import User, Device, License, AuditLog
from auth_utils import get_password_hash
from crypto_service import generate_license_jwt

def init_and_seed_database():
    print("[*] Đang khởi tạo Schema Database SQLite (olm_admin.db)...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 1. Tạo tài khoản mẫu nếu chưa có
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            print("[+] Tạo tài khoản Quản trị viên (Admin): admin / admin123")
            admin_user = User(
                username="admin",
                password_hash=get_password_hash("admin123"),
                full_name="Nguyễn Văn Quản Trị (Admin)",
                role="ADMIN",
                is_active=True
            )
            db.add(admin_user)
            db.flush()

        sale_user = db.query(User).filter(User.username == "sale").first()
        if not sale_user:
            print("[+] Tạo tài khoản Nhân viên Kinh doanh (Sale): sale / sale123")
            sale_user = User(
                username="sale",
                password_hash=get_password_hash("sale123"),
                full_name="Trần Thị Bích Ngọc (Sale)",
                role="SALE",
                is_active=True
            )
            db.add(sale_user)
            db.flush()

        # 2. Tạo 3 thiết bị mẫu với License Ed25519 hợp lệ
        sample_devices = [
            {
                "df": "MN73-006Q-5G96-S3E8",
                "model": "Newland NLS-MT90",
                "customer": "Công ty Cổ phần Vận tải Á Châu",
                "phone": "0912345678",
                "email": "contact@achau-trans.vn",
                "type": "PRO",
                "days": 365,
                "permanent": False,
                "notes": "Máy kiểm kho xuất nhập bãi xe container"
            },
            {
                "df": "9A2B-X7Y8-AT6Y-4F2E",
                "model": "Zebra MC3300x",
                "customer": "Tập đoàn Bán lẻ Tân Hưng Hà",
                "phone": "0988776655",
                "email": "kho@tanhungha.com.vn",
                "type": "PRO",
                "days": 0,
                "permanent": True,
                "notes": "Máy quét kho tổng - Bản quyền vĩnh viễn"
            },
            {
                "df": "B3C4-D5E6-F7G8-H9J1",
                "model": "iMin Swift 2",
                "customer": "Chuỗi Cà phê Sài Gòn Phố",
                "phone": "0909112233",
                "email": "saigonpho.cafe@gmail.com",
                "type": "TRIAL",
                "days": 15,
                "permanent": False,
                "notes": "Đang dùng thử nghiệm 15 ngày tại chi nhánh Quận 1"
            }
        ]

        for s in sample_devices:
            existing_dev = db.query(Device).filter(Device.df == s["df"]).first()
            if not existing_dev:
                print(f"[+] Khởi tạo thiết bị mẫu: {s['model']} - DF: {s['df']}")
                dev = Device(
                    df=s["df"],
                    model=s["model"],
                    customer_name=s["customer"],
                    customer_phone=s["phone"],
                    customer_email=s["email"],
                    notes=s["notes"]
                )
                db.add(dev)
                db.flush()

                # Sinh License JWT Ed25519 thật
                lic_data = generate_license_jwt(
                    df=s["df"],
                    license_type=s["type"],
                    days_valid=s["days"],
                    is_permanent=s["permanent"],
                    customer=s["customer"],
                    model=s["model"],
                    version=1
                )

                lic = License(
                    device_id=dev.id,
                    license_jwt=lic_data["jwt_token"],
                    license_type="PRO" if s["permanent"] else s["type"],
                    issued_at=lic_data["issued_at"],
                    expires_at=lic_data["expires_at"],
                    is_permanent=s["permanent"],
                    status="ACTIVE",
                    version=1,
                    qr_code_base64=lic_data["qr_base64"],
                    created_by=admin_user.id
                )
                db.add(lic)
                db.flush()

                # Ghi log mẫu
                log = AuditLog(
                    user_id=admin_user.id,
                    action="GENERATE",
                    target_df=s["df"],
                    details=f"Khởi tạo license mẫu ({s['type']}) cho {s['customer']}",
                    ip_address="127.0.0.1"
                )
                db.add(log)

        db.commit()
        print("[✓] Hoàn tất nạp dữ liệu mẫu ban đầu vào SQLite Database thành công!")

    except Exception as e:
        db.rollback()
        print(f"[-] Lỗi khi nạp dữ liệu mẫu: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    init_and_seed_database()

