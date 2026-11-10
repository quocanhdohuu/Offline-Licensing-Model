from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models import Device, License, User
from schemas import StatsResponse
from dependencies import require_admin

router = APIRouter(prefix="/api/stats", tags=["Statistics"])

@router.get("", response_model=StatsResponse)
def get_stats(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin) # Chỉ Admin mới xem được thống kê
):
    """Lấy số liệu thống kê tổng quan hệ thống bản quyền PDA (Chỉ dành cho ADMIN)."""
    now_dt = datetime.now(timezone.utc)
    in_30_days = now_dt + timedelta(days=30)

    total_devices = db.query(func.count(Device.id)).scalar() or 0
    total_active_licenses = db.query(func.count(License.id)).filter(License.status == "ACTIVE").scalar() or 0
    permanent_licenses = db.query(func.count(License.id)).filter(License.status == "ACTIVE", License.is_permanent == True).scalar() or 0
    trial_licenses = db.query(func.count(License.id)).filter(License.status == "ACTIVE", License.license_type == "TRIAL").scalar() or 0

    expiring_soon = db.query(func.count(License.id)).filter(
        License.status == "ACTIVE",
        License.is_permanent == False,
        License.expires_at != None,
        License.expires_at <= in_30_days
    ).scalar() or 0

    # Phân bổ theo Model máy
    model_rows = db.query(Device.model, func.count(Device.id)).group_by(Device.model).all()
    models_distribution = {row[0]: row[1] for row in model_rows}

    return StatsResponse(
        total_devices=total_devices,
        total_active_licenses=total_active_licenses,
        permanent_licenses=permanent_licenses,
        trial_licenses=trial_licenses,
        expiring_soon_licenses=expiring_soon,
        models_distribution=models_distribution
    )

