from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import User
from schemas import LoginRequest, LoginResponse, UserResponse
from auth_utils import verify_password, create_access_token
from dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Xác thực đăng nhập tài khoản (Admin hoặc Sale) và cấp Token JWT."""
    user = db.query(User).filter(User.username == request.username.strip()).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tên đăng nhập hoặc mật khẩu không chính xác!"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản này đã bị tạm khóa!"
        )

    # Sinh JWT session token
    token = create_access_token(data={
        "sub": user.username,
        "role": user.role,
        "full_name": user.full_name
    })

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Lấy thông tin tài khoản đang đăng nhập."""
    return UserResponse.model_validate(current_user)

