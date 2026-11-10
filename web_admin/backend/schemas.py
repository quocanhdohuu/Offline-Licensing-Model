from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

# ================= AUTH SCHEMAS =================
class LoginRequest(BaseModel):
    username: str = Field(..., example="admin")
    password: str = Field(..., example="admin123")

class UserResponse(BaseModel):
    id: int
    username: str
    full_name: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# ================= LICENSE SCHEMAS =================
class CreateLicenseRequest(BaseModel):
    df: str = Field(..., description="Mã DF 16 ký tự Crockford (VD: ABCD-EFGH-JKMN-PQRS)")
    model: str = Field(default="Newland NLS-MT90", description="Model PDA")
    customer_name: str = Field(..., description="Tên khách hàng / doanh nghiệp")
    customer_phone: Optional[str] = Field(None, description="Số điện thoại")
    customer_email: Optional[str] = Field(None, description="Email")
    notes: Optional[str] = Field(None, description="Ghi chú")
    license_type: str = Field(default="PRO", description="TRIAL hoặc PRO")
    days_valid: int = Field(default=365, description="Số ngày hiệu lực (bỏ qua nếu vĩnh viễn)")
    is_permanent: bool = Field(default=False, description="Bản quyền vĩnh viễn")
    features: Optional[List[str]] = Field(default=["SCANNER", "INVENTORY", "DIRECT_PRINT"])

class UpgradeLicenseRequest(BaseModel):
    license_type: str = Field(default="PRO", description="Gói mới (PRO / PERPETUAL)")
    days_valid: int = Field(default=365, description="Số ngày gia hạn thêm")
    is_permanent: bool = Field(default=True, description="Đổi sang bản quyền vĩnh viễn")
    notes: Optional[str] = Field(None, description="Lý do nâng cấp")

class LicenseResponse(BaseModel):
    id: int
    device_id: int
    df: str
    model: str
    customer_name: str
    customer_phone: Optional[str]
    customer_email: Optional[str]
    license_jwt: str
    license_type: str
    issued_at: datetime
    expires_at: Optional[datetime]
    is_permanent: bool
    status: str
    version: int
    qr_code_base64: str
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# ================= STATS SCHEMAS =================
class StatsResponse(BaseModel):
    total_devices: int
    total_active_licenses: int
    permanent_licenses: int
    trial_licenses: int
    expiring_soon_licenses: int # Hết hạn trong vòng 30 ngày
    models_distribution: dict

