from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from seed_data import init_and_seed_database
from routers import auth, licenses, stats

app = FastAPI(
    title="Tân Hưng Hà OLM - Admin Portal API",
    version="1.0.0",
    description="Cổng API Quản trị Bản quyền Offline Licensing Model (OLM)"
)

# Cấu hình CORS để React Frontend (Vite) gọi API không bị chặn
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký các Router nghiệp vụ
app.include_router(auth.router)
app.include_router(licenses.router)
app.include_router(stats.router)

@app.on_event("startup")
def on_startup():
    """Tự động kiểm tra và khởi tạo Database + Dữ liệu mẫu khi Server bật."""
    init_and_seed_database()

@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "TanHungHa OLM Admin API",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
