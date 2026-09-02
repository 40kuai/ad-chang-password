# AD 域控自助改密平台

一个用于用户自助修改 Windows AD 域控登录密码的 Web 平台。

用户输入域账号、旧密码与新密码，通过 LDAPS 连接域控完成身份验证与密码修改，全程不依赖管理员权限，改密结果即时反馈。

## 功能特性

- 用户自助改密：输入域账号 + 旧密码 + 新密码（含确认），提交后由后端通过 LDAPS 完成修改
- 前端基础校验：长度、复杂度（大小写字母 / 数字 / 特殊字符）、新旧密码不一致、两次输入一致
- 标准 AD 改密方式：Delete 旧密码 + Add 新密码（UTF-16LE），符合 AD 自助改密规范
- 错误分类提示：旧密码错误 / 密码不合域控策略 / 连接失败等
- 审计日志：记录账号、时间、来源 IP、操作结果（绝不记录密码明文）
- Mock 模式：无真实域控环境也可本地演示全流程
- Docker 部署：多阶段构建，单端口提供服务

## 技术栈

| 端 | 技术 |
|----|------|
| 前端 | Vue 3 + Vite |
| 后端 | Python 3.9+ / FastAPI / ldap3 |
| 数据库 | 无（不落库，仅日志文件） |

## 目录结构

```
changpwd/
├── backend/                 # 后端服务
│   ├── app/
│   │   ├── main.py          # FastAPI 入口与路由
│   │   ├── config.py        # .env 配置读取
│   │   ├── ldap_service.py  # LDAP 绑定与改密逻辑
│   │   └── logger.py        # 审计日志
│   ├── requirements.txt     # 依赖清单（锁定版本）
│   └── .env.example         # 配置模板
├── frontend/                # 前端页面（Vue3 + Vite）
│   ├── src/App.vue          # 改密表单页
│   └── vite.config.js       # 开发代理 /api -> 后端
├── Dockerfile               # 多阶段构建镜像
└── .gitignore
```

## 快速开始（本地开发）

### 1. 后端

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
cp .env.example .env          # 按实际环境修改 LDAP_HOST / LDAP_DOMAIN 等
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

### 2. 前端

```bash
cd frontend
npm install --registry=https://registry.npmmirror.com
npm run dev                   # 默认 http://localhost:5173
```

前端开发服务器已配置 `/api` 代理到后端，直接访问前端地址即可联调。

### 3. Mock 模式（无真实域控演示）

在 `backend/.env` 中设置 `MOCK_LDAP=true`，旧密码须为 `OldPass@123`，其余任意合规新密码即可演示成功流程。

## Docker 部署

```bash
# 构建镜像（基础镜像默认走国内加速源；可直连 Docker Hub 时可用 --build-arg 覆盖）
docker build -t ad-password:1.0.0 .

# 运行（通过环境变量注入域控配置，勿写入镜像）
docker run -d -p 8000:8000 \
  -e LDAP_HOST=<域控地址> \
  -e LDAP_DOMAIN=<AD 域> \
  -e LDAP_PORT=636 \
  -e LDAP_USE_SSL=true \
  ad-password:1.0.0
```

构建产物由 FastAPI 单端口托管：`http://<主机>:8000/` 即为改密页面，`/api/*` 为接口。

## 配置说明

| 配置项 | 说明 | 示例 |
|--------|------|------|
| `LDAP_HOST` | 域控服务器地址（FQDN 或 IP） | `dc.example.com` |
| `LDAP_PORT` | LDAPS 端口，通常 636 | `636` |
| `LDAP_USE_SSL` | 是否启用 LDAPS | `true` |
| `LDAP_DOMAIN` | AD 域（注意与域控主机 FQDN 的区别） | `example.com` |
| `LOG_FILE` | 审计日志文件路径 | `logs/audit.log` |
| `MOCK_LDAP` | 是否启用 Mock 模式 | `false` |

> 域控主机 FQDN（如 `dc1.corp.local`）与 AD 域（如 `corp.local`）通常不同，两者需分别配置正确。

## 接口说明

### POST /api/change-password

请求体：

```json
{
  "username": "zhangsan",
  "old_password": "OldPass123!",
  "new_password": "NewPass456!"
}
```

响应（统一结构）：

```json
{ "code": 0, "message": "密码修改成功" }
```

错误码约定：

| code | 含义 |
|------|------|
| 0 | 成功 |
| 1001 | 旧密码错误或账号不存在 |
| 1002 | 新密码不符合域控密码策略 |
| 1003 | 连接域控失败或超时 |
| 1004 | 请求参数校验失败 |
| 1005 | 其他域控操作失败 |

### GET /api/health

健康检查。

## 安全说明

- 全程强制 LDAPS（TLS）连接，AD 明文连接会拒绝改密
- 使用用户自身凭据认证，后端不保存任何账号密码
- 审计日志不含密码明文
- 敏感配置统一走环境变量 / `.env`，不硬编码，`.env` 已被 git 忽略
- 容器内以非 root 用户运行

## License

内部项目，仅限授权范围内使用。
