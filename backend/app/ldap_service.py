"""LDAP 改密核心逻辑：用户凭据绑定 -> 修改 unicodePwd。"""
import os

from ldap3 import ALL, MODIFY_ADD, MODIFY_DELETE, Connection, Server
from ldap3.core.exceptions import LDAPException, LDAPSocketOpenError
from ldap3.core.results import (
    RESULT_CONSTRAINT_VIOLATION,
    RESULT_INVALID_CREDENTIALS,
    RESULT_UNWILLING_TO_PERFORM,
)
from ldap3.utils.conv import escape_filter_chars

from app.config import settings

# 错误码（与接口约定一致）
ERR_OLD_PASSWORD = 1001
ERR_POLICY = 1002
ERR_CONNECT = 1003
ERR_OTHER = 1005
OK = 0

# 本地无真实域控时用于演示：MOCK_LDAP=true 则跳过真实 LDAP
MOCK_LDAP = os.getenv("MOCK_LDAP", "false").lower() == "true"
MOCK_OLD_PASSWORD = "OldPass@123"


def _search_base(domain: str) -> str:
    """由域名推导 LDAP 根（DC=xx,DC=yy）。"""
    return ",".join(f"DC={part}" for part in domain.split("."))


def _mock_change(old_password: str) -> tuple[int, str]:
    """仅用于本地无域控演示：旧密码须等于演示值。"""
    if old_password != MOCK_OLD_PASSWORD:
        return ERR_OLD_PASSWORD, "旧密码错误或账号不存在"
    return OK, "密码修改成功"


def change_password(username: str, old_password: str, new_password: str) -> tuple[int, str]:
    """修改 AD 密码。返回 (错误码, 消息)，错误码 0 表示成功。"""
    if MOCK_LDAP:
        return _mock_change(old_password)

    domain = settings.ldap_domain
    upn = f"{username}@{domain}"
    server = Server(
        settings.ldap_host,
        port=settings.ldap_port,
        use_ssl=settings.ldap_use_ssl,
        get_info=ALL,
        connect_timeout=5,
    )
    conn = None

    try:
        conn = Connection(server, user=upn, password=old_password, auto_bind=False)

        # 1. 手动绑定：失败时按 LDAP 错误码区分（49 = invalidCredentials）
        if not conn.bind():
            if conn.result.get("result") == RESULT_INVALID_CREDENTIALS:
                return ERR_OLD_PASSWORD, "旧密码错误或账号不存在"
            return ERR_OTHER, "账号认证失败，请稍后重试或联系管理员"

        # 2. 查询用户 DN
        escaped_upn = escape_filter_chars(upn)
        if not conn.search(
            search_base=_search_base(domain),
            search_filter=f"(&(objectClass=user)(userPrincipalName={escaped_upn}))",
            attributes=["distinguishedName"],
        ):
            return ERR_OTHER, "未找到该用户"

        user_dn = conn.entries[0].distinguishedName.value

        # 3. 修改 unicodePwd（AD 自助改密标准方式：Delete 旧密码 + Add 新密码，UTF-16LE 带引号）
        old_value = f'"{old_password}"'.encode("utf-16-le")
        new_value = f'"{new_password}"'.encode("utf-16-le")
        if not conn.modify(
            user_dn,
            {"unicodePwd": [(MODIFY_DELETE, [old_value]), (MODIFY_ADD, [new_value])]},
        ):
            code = conn.result.get("result")
            if code in (RESULT_UNWILLING_TO_PERFORM, RESULT_CONSTRAINT_VIOLATION):
                return ERR_POLICY, "新密码不符合域控密码策略（复杂度/历史/长度）"
            return ERR_OTHER, "域控操作失败，请稍后重试"

        return OK, "密码修改成功"
    except (LDAPSocketOpenError, TimeoutError, ConnectionError):
        return ERR_CONNECT, "无法连接域控服务器，请稍后重试或联系管理员"
    except LDAPException:
        return ERR_OTHER, "域控操作失败，请稍后重试"
    finally:
        if conn is not None:
            try:
                conn.unbind()
            except LDAPException:
                pass
