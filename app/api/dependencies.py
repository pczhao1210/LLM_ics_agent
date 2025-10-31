from fastapi import Header, HTTPException, Query, status
from ..config import settings


async def verify_api_token(
    authorization: str | None = Header(default=None, convert_underscores=False),
    token: str | None = Query(default=None)
):
    """校验API访问令牌，支持Bearer头或token查询参数。"""
    expected_token = settings.api_token
    
    # 未配置令牌时不启用认证
    if not expected_token:
        return
    
    provided_token = None
    
    if authorization:
        scheme, _, value = authorization.partition(" ")
        if scheme.lower() == "bearer":
            provided_token = value.strip()
    
    if not provided_token and token:
        provided_token = token.strip()
    
    if provided_token != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API token",
            headers={"WWW-Authenticate": "Bearer"}
        )
