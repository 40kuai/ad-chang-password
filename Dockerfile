# ===== 构建参数：基础镜像 =====
# 默认走国内可访问的 daocloud 加速源（Docker Hub 在国内常超时）；
# 若可直连 Docker Hub，构建时加 --build-arg NODE_IMAGE=node:20-alpine --build-arg PYTHON_IMAGE=python:3.11-slim 覆盖
ARG NODE_IMAGE=docker.m.daocloud.io/library/node:20-alpine
ARG PYTHON_IMAGE=docker.m.daocloud.io/library/python:3.11-slim

# ===== 阶段 1：构建前端 =====
FROM ${NODE_IMAGE} AS frontend-builder
WORKDIR /build/frontend

# 先复制依赖清单，利用 Docker 层缓存
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --registry=https://registry.npmmirror.com --no-audit --no-fund

COPY frontend/ ./
RUN npm run build

# ===== 阶段 2：后端运行时 =====
FROM ${PYTHON_IMAGE} AS runtime
WORKDIR /app

ENV TZ=Asia/Shanghai \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 安装后端依赖（国内镜像加速）
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple \
    -r /app/backend/requirements.txt

# 复制后端代码与前端构建产物
COPY backend/ /app/backend/
COPY --from=frontend-builder /build/frontend/dist /app/frontend/dist

# 提供默认配置模板；真实参数请在运行时通过环境变量覆盖（如 -e LDAP_HOST=xxx）
COPY backend/.env.example /app/backend/.env

# 非 root 运行（更安全）
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

WORKDIR /app/backend
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
