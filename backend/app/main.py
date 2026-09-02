"""FastAPI 入口：POST /api/change-password"""
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app import ldap_service
from app.config import settings
from app.logger import write_audit

app = FastAPI(title="AD 域控自助改密平台", version="1.0.0")

# 允许前端（Vite dev server）跨域调用
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
    ],
    allow_methods=["POST"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    """参数校验失败时返回统一格式。"""
    return JSONResponse(status_code=422, content={"code": 1004, "message": "请求参数不合法"})


class ChangePasswordRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=128, description="域账号")
    old_password: str = Field(..., min_length=1, max_length=256)
    new_password: str = Field(..., min_length=8, max_length=256)


@app.get("/api/health")
def health():
    return {"code": 0, "message": "ok"}


@app.post("/api/change-password")
def change_password(req: ChangePasswordRequest, request: Request):
    client_ip = request.client.host if request.client else "unknown"

    if req.old_password == req.new_password:
        return {"code": 1004, "message": "新密码不能与旧密码相同"}

    code, message = ldap_service.change_password(
        req.username, req.old_password, req.new_password
    )

    # 审计日志（绝不记录密码）
    write_audit(req.username, client_ip, success=(code == 0), detail=f"code={code}")

    return {"code": code, "message": message}


# 生产部署：若存在前端构建产物（frontend/dist），则由 FastAPI 单端口托管静态页面
# 注意：该挂载必须放在所有 API 路由之后，避免遮挡 /api 接口
FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
