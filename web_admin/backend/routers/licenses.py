import io
import base64
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from database import get_db
from models import User, Device, License, AuditLog
from schemas import LicenseResponse, CreateLicenseRequest, UpgradeLicenseRequest
from dependencies import get_current_user, require_admin
from crypto_service import generate_license_jwt, normalize_df

router = APIRouter(prefix="/api/licenses", tags=["Licenses"])

def format_license_response(lic: License) -> LicenseResponse:
    dev = lic.device
    return LicenseResponse(
        id=lic.id,
        device_id=dev.id,
        df=dev.df,
        model=dev.model,
        customer_name=dev.customer_name,
        customer_phone=dev.customer_phone,
        customer_email=dev.customer_email,
        license_jwt=lic.license_jwt,
        license_type=lic.license_type,
        issued_at=lic.issued_at,
        expires_at=lic.expires_at,
        is_permanent=lic.is_permanent,
        status=lic.status,
        version=lic.version,
        qr_code_base64=lic.qr_code_base64,
        notes=dev.notes,
        created_at=lic.created_at
    )

@router.get("", response_model=List[LicenseResponse])
def get_licenses(
    q: Optional[str] = Query(None, description="Từ khóa tìm kiếm (DF, Tên khách, SĐT, Model)"),
    status: Optional[str] = Query("ACTIVE", description="Lọc theo trạng thái (ACTIVE, SUPERSEDED, ALL)"),
    license_type: Optional[str] = Query(None, description="Lọc theo gói (TRIAL, PRO)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Tra cứu danh sách License (Cả SALE và ADMIN đều có quyền gọi).
    Hỗ trợ tìm kiếm theo DF, SĐT, Tên khách hàng phục vụ cấp lại mã nhanh.
    """
    query = db.query(License).join(Device)

    if status and status.upper() != "ALL":
        query = query.filter(License.status == status.upper())

    if license_type:
        query = query.filter(License.license_type == license_type.upper())

    if q and q.strip():
        term = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Device.df.ilike(term),
                Device.customer_name.ilike(term),
                Device.customer_phone.ilike(term),
                Device.model.ilike(term)
            )
        )

    # Ghi log tra cứu nếu có tìm kiếm
    if q and q.strip():
        db.add(AuditLog(
            user_id=current_user.id,
            action="SEARCH",
            details=f"Người dùng {current_user.username} ({current_user.role}) tìm kiếm từ khóa: '{q.strip()}'"
        ))
        db.commit()

    licenses = query.order_by(desc(License.id)).all()
    return [format_license_response(lic) for lic in licenses]

@router.get("/{id}", response_model=LicenseResponse)
def get_license_detail(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lấy chi tiết 1 License kèm Token và QR Code (Cấp lại cho khách)."""
    lic = db.query(License).filter(License.id == id).first()
    if not lic:
        raise HTTPException(status_code=404, detail="Không tìm thấy License yêu cầu!")

    # Ghi log xem/cấp lại
    db.add(AuditLog(
        user_id=current_user.id,
        action="REISSUE_VIEW",
        target_df=lic.device.df,
        details=f"Người dùng {current_user.username} ({current_user.role}) xem và lấy lại license cho {lic.device.customer_name}"
    ))
    db.commit()

    return format_license_response(lic)

@router.post("", response_model=LicenseResponse, status_code=status.HTTP_201_CREATED)
def create_license(
    req: CreateLicenseRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin) # Chỉ Admin mới được tạo
):
    """
    Sinh License mới cho thiết bị PDA (CHỈ DÀNH CHO ADMIN).
    Tự động chuẩn hóa DF, ký số JWT Ed25519 và sinh ảnh mã QR.
    """
    try:
        norm_df = normalize_df(req.df)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Tìm xem thiết bị đã có trong hệ thống chưa
    dev = db.query(Device).filter(Device.df == norm_df).first()
    if not dev:
        dev = Device(
            df=norm_df,
            model=req.model.strip(),
            customer_name=req.customer_name.strip(),
            customer_phone=req.customer_phone.strip() if req.customer_phone else None,
            customer_email=req.customer_email.strip() if req.customer_email else None,
            notes=req.notes.strip() if req.notes else None
        )
        db.add(dev)
        db.flush()
    else:
        # Cập nhật thông tin khách nếu có
        dev.model = req.model.strip()
        dev.customer_name = req.customer_name.strip()
        if req.customer_phone:
            dev.customer_phone = req.customer_phone.strip()
        if req.customer_email:
            dev.customer_email = req.customer_email.strip()
        if req.notes:
            dev.notes = req.notes.strip()
        db.flush()

    # Vô hiệu hóa các license cũ của thiết bị này nếu có
    active_licenses = db.query(License).filter(License.device_id == dev.id, License.status == "ACTIVE").all()
    for old_lic in active_licenses:
        old_lic.status = "SUPERSEDED"

    # Sinh License mới bằng Ed25519
    version = len(dev.licenses) + 1 if dev.licenses else 1
    lic_result = generate_license_jwt(
        df=norm_df,
        license_type=req.license_type,
        days_valid=req.days_valid,
        is_permanent=req.is_permanent,
        customer=dev.customer_name,
        model=dev.model,
        features=req.features,
        version=version
    )

    new_lic = License(
        device_id=dev.id,
        license_jwt=lic_result["jwt_token"],
        license_type="PRO" if req.is_permanent else req.license_type.upper(),
        issued_at=lic_result["issued_at"],
        expires_at=lic_result["expires_at"],
        is_permanent=lic_result["is_permanent"],
        status="ACTIVE",
        version=version,
        qr_code_base64=lic_result["qr_base64"],
        created_by=admin_user.id
    )
    db.add(new_lic)

    # Ghi log Audit
    db.add(AuditLog(
        user_id=admin_user.id,
        action="GENERATE",
        target_df=norm_df,
        details=f"Admin {admin_user.username} tạo mới License {new_lic.license_type} v{version} cho thiết bị {dev.model}"
    ))

    db.commit()
    db.refresh(new_lic)
    return format_license_response(new_lic)

@router.post("/{id}/upgrade", response_model=LicenseResponse)
def upgrade_license(
    id: int,
    req: UpgradeLicenseRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin) # Chỉ Admin mới được nâng cấp
):
    """
    Nâng cấp License cho thiết bị (Ví dụ: Trial -> Pro Vĩnh viễn) (CHỈ DÀNH CHO ADMIN).
    Giữ nguyên DF của máy, sinh JWT mới tăng số version.
    """
    target_lic = db.query(License).filter(License.id == id).first()
    if not target_lic:
        raise HTTPException(status_code=404, detail="Không tìm thấy License để nâng cấp!")

    dev = target_lic.device

    # Đánh dấu toàn bộ license ACTIVE hiện hành thành SUPERSEDED
    current_actives = db.query(License).filter(License.device_id == dev.id, License.status == "ACTIVE").all()
    for cur in current_actives:
        cur.status = "SUPERSEDED"

    new_version = target_lic.version + 1
    lic_result = generate_license_jwt(
        df=dev.df,
        license_type=req.license_type,
        days_valid=req.days_valid,
        is_permanent=req.is_permanent,
        customer=dev.customer_name,
        model=dev.model,
        version=new_version
    )

    upgraded_lic = License(
        device_id=dev.id,
        license_jwt=lic_result["jwt_token"],
        license_type="PRO" if req.is_permanent else req.license_type.upper(),
        issued_at=lic_result["issued_at"],
        expires_at=lic_result["expires_at"],
        is_permanent=lic_result["is_permanent"],
        status="ACTIVE",
        version=new_version,
        qr_code_base64=lic_result["qr_base64"],
        created_by=admin_user.id
    )
    db.add(upgraded_lic)

    # Cập nhật ghi chú nếu có
    if req.notes:
        dev.notes = f"{dev.notes}\n[Nâng cấp v{new_version}]: {req.notes}".strip()

    # Ghi log Audit
    db.add(AuditLog(
        user_id=admin_user.id,
        action="UPGRADE",
        target_df=dev.df,
        details=f"Admin {admin_user.username} nâng cấp License từ {target_lic.license_type} sang {upgraded_lic.license_type} v{new_version}"
    ))

    db.commit()
    db.refresh(upgraded_lic)
    return format_license_response(upgraded_lic)

@router.get("/{id}/download-qr")
def download_qr(
    id: int,
    token: Optional[str] = Query(None, description="Session JWT token khi gọi trực tiếp từ thẻ a"),
    db: Session = Depends(get_db)
):
    """Tải trực tiếp file ảnh mã QR PNG chất lượng cao về máy."""
    lic = db.query(License).filter(License.id == id).first()
    if not lic:
        raise HTTPException(status_code=404, detail="Không tìm thấy License!")

    # Giải mã Base64 data URI thành raw bytes
    header, encoded = lic.qr_code_base64.split(",", 1)
    qr_bytes = base64.b64decode(encoded)

    clean_df = lic.device.df.replace("-", "")
    filename = f"qr_{clean_df}.png"

    return Response(
        content=qr_bytes,
        media_type="image/png",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@router.get("/{id}/download-lic")
def download_lic(
    id: int,
    token: Optional[str] = Query(None, description="Session JWT token khi gọi trực tiếp từ thẻ a"),
    db: Session = Depends(get_db)
):
    """Tải trực tiếp file token .lic về máy."""
    lic = db.query(License).filter(License.id == id).first()
    if not lic:
        raise HTTPException(status_code=404, detail="Không tìm thấy License!")

    clean_df = lic.device.df.replace("-", "")
    filename = f"license_{clean_df}.lic"

    return Response(
        content=lic.license_jwt.encode("utf-8"),
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

