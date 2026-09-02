"""审计日志：记录账号、时间、来源 IP、操作结果；绝不记录密码。"""
import logging
import os
from logging.handlers import RotatingFileHandler

from app.config import settings

LOG_DIR = os.path.dirname(settings.log_file) or "."
os.makedirs(LOG_DIR, exist_ok=True)

audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)

if not audit_logger.handlers:
    handler = RotatingFileHandler(
        settings.log_file, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    audit_logger.addHandler(handler)


def write_audit(username: str, ip: str, success: bool, detail: str = "") -> None:
    """写一条审计日志。detail 只允许放错误码等非敏感信息。"""
    result = "SUCCESS" if success else "FAIL"
    msg = f"username={username} | ip={ip} | result={result}"
    if detail:
        msg += f" | detail={detail}"
    if success:
        audit_logger.info(msg)
    else:
        audit_logger.warning(msg)
