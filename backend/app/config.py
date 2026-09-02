"""应用配置：从 .env 或环境变量读取，禁止硬编码敏感信息。"""
import os
from pathlib import Path

from dotenv import load_dotenv

# 加载 backend/.env（若存在）
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Settings:
    def __init__(self) -> None:
        self.ldap_host: str = os.getenv("LDAP_HOST", "127.0.0.1")
        self.ldap_port: int = int(os.getenv("LDAP_PORT", "636"))
        self.ldap_use_ssl: bool = os.getenv("LDAP_USE_SSL", "true").lower() == "true"
        self.ldap_domain: str = os.getenv("LDAP_DOMAIN", "corp.local")
        self.log_file: str = os.getenv("LOG_FILE", "logs/audit.log")

    def validate(self) -> None:
        """启动前校验关键配置。"""
        if not self.ldap_host or not self.ldap_domain:
            raise RuntimeError("缺少 LDAP_HOST / LDAP_DOMAIN 配置，请检查 backend/.env")


settings = Settings()
