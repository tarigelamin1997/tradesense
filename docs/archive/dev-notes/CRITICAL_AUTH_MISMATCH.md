# 🚨 CRITICAL: Authentication Implementation Mismatch

**Priority**: BLOCKER - Must be resolved before ANY deployment

## The Problem

The frontend expects **httpOnly cookie-based authentication** (secure), but traditional backend implementations use **JWT in response body** (less secure). This mismatch will cause 100% authentication failure.

## Frontend Expectation (Current Implementation)

```typescript
// Frontend sends credentials and expects cookie to be SET by backend
const response = await fetch('/auth/token', {
    method: 'POST',
    body: credentials,
    credentials: 'include'  // ← EXPECTS COOKIES
});

// Frontend does NOT store token - expects it in httpOnly cookie
// All subsequent requests just include cookies automatically
```

## Traditional Backend (Will Break)

```python
@app.post("/auth/token")
async def login(credentials):
    token = create_jwt_token(user)
    return {
        "access_token": token,  # ← Frontend IGNORES this
        "token_type": "bearer"
    }
    # NO COOKIE SET = AUTHENTICATION BROKEN
```

## Required Backend Implementation

```python
from fastapi import Response, Cookie
from datetime import datetime, timedelta

@app.post("/auth/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    response: Response
):
    # Authenticate user
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(401, "Invalid credentials")
    
    # Create token
    access_token = create_access_token(data={"sub": user.email})
    
    # SET HTTPONLY COOKIE (Critical!)
    response.set_cookie(
        key="auth-token",
        value=access_token,
        httponly=True,          # Cannot be accessed by JavaScript
        secure=True,            # HTTPS only in production
        samesite="lax",         # CSRF protection
        max_age=86400,          # 24 hours
        domain=".tradesense.com" # For subdomain access
    )
    
    # Still return token for API compatibility
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "message": "Cookie has been set"
    }

# All protected endpoints must accept BOTH cookie and header auth
async def get_current_user(
    authorization: Optional[str] = Header(None),
    auth_token: Optional[str] = Cookie(None)
):
    # Try cookie first (more secure)
    token = auth_token
    
    # Fallback to Authorization header (for API clients)
    if not token and authorization:
        scheme, token = authorization.split() if authorization else (None, None)
        if scheme != "Bearer":
            raise HTTPException(401, "Invalid authentication scheme")
    
    if not token:
        raise HTTPException(401, "Not authenticated")
    
    # Verify token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(401, "Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(401, "Invalid token")
```

## Complete Working Implementation

```python
# src/backend/core/auth.py
from typing import Optional
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status, Response, Cookie, Header
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from src.backend.core.config import settings
from src.backend.db.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Support both cookie and bearer token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)

class AuthService:
    def __init__(self):
        self.secret_key = settings.jwt_secret_key.get_secret_value()
        self.algorithm = settings.jwt_algorithm
        self.access_token_expire_minutes = settings.jwt_expiration_hours * 60
    
    def create_access_token(self, data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)
    
    async def authenticate_user(self, db: AsyncSession, email: str, password: str) -> Optional[User]:
        user = await db.query(User).filter(User.email == email).first()
        if not user or not self.verify_password(password, user.hashed_password):
            return None
        return user
    
    async def get_current_user(
        self,
        db: AsyncSession = Depends(get_db),
        token_from_header: Optional[str] = Depends(oauth2_scheme),
        token_from_cookie: Optional[str] = Cookie(None, alias="auth-token")
    ) -> User:
        # Prefer cookie (more secure)
        token = token_from_cookie or token_from_header
        
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id: str = payload.get("sub")
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
        
        user = await db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        
        return user

auth_service = AuthService()

# API Endpoints
from fastapi import APIRouter

router = APIRouter()

@router.post("/auth/token")
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Login endpoint that sets httpOnly cookie"""
    user = await auth_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth_service.create_access_token(data={"sub": str(user.id)})
    
    # Set httpOnly cookie
    response.set_cookie(
        key="auth-token",
        value=access_token,
        httponly=True,
        secure=settings.environment == "production",  # Only HTTPS in production
        samesite="lax",
        max_age=settings.jwt_expiration_hours * 3600,
        path="/",
        domain=None  # Let browser handle domain
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name
        }
    }

@router.post("/auth/logout")
async def logout(response: Response):
    """Logout endpoint that clears the cookie"""
    response.delete_cookie(
        key="auth-token",
        path="/",
        secure=settings.environment == "production",
        samesite="lax"
    )
    return {"message": "Successfully logged out"}

@router.get("/auth/me")
async def get_current_user_info(
    current_user: User = Depends(auth_service.get_current_user)
):
    """Get current user info using cookie or bearer token"""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at
    }

# CORS Configuration must allow credentials
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # Must be specific origins, not "*"
    allow_credentials=True,  # ← CRITICAL for cookies
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)
```

## Testing the Implementation

```python
# tests/test_auth_cookies.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_login_sets_cookie(client: AsyncClient):
    """Test that login sets httpOnly cookie"""
    response = await client.post("/auth/token", data={
        "username": "test@example.com",
        "password": "testpass123"
    })
    
    assert response.status_code == 200
    assert "auth-token" in response.cookies
    
    # Verify cookie attributes
    cookie = response.cookies["auth-token"]
    assert cookie.get("httponly") == True
    assert cookie.get("samesite") == "lax"

@pytest.mark.asyncio
async def test_protected_endpoint_with_cookie(client: AsyncClient):
    """Test accessing protected endpoint with cookie"""
    # Login
    login_response = await client.post("/auth/token", data={
        "username": "test@example.com",
        "password": "testpass123"
    })
    
    # Access protected endpoint (cookie automatically sent)
    me_response = await client.get("/auth/me")
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "test@example.com"

@pytest.mark.asyncio
async def test_logout_clears_cookie(client: AsyncClient):
    """Test that logout clears the cookie"""
    # Login first
    await client.post("/auth/token", data={
        "username": "test@example.com",
        "password": "testpass123"
    })
    
    # Logout
    logout_response = await client.post("/auth/logout")
    assert logout_response.status_code == 200
    
    # Verify cookie is cleared
    assert "auth-token" not in logout_response.cookies
```

## Migration Guide for Existing APIs

If you have existing API clients expecting tokens in headers:

```python
# Support both authentication methods
async def get_current_user(
    authorization: Optional[str] = Header(None),
    auth_token: Optional[str] = Cookie(None, alias="auth-token"),
    db: AsyncSession = Depends(get_db)
) -> User:
    # 1. Try cookie first (web app)
    token = auth_token
    
    # 2. Try Authorization header (mobile/API)
    if not token and authorization:
        try:
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                token = None
        except:
            token = None
    
    # 3. Validate token
    if not token:
        raise HTTPException(401, "Not authenticated")
    
    # ... rest of validation
```

## Deployment Checklist

- [ ] Backend sets httpOnly cookies on login
- [ ] Backend accepts cookies for authentication
- [ ] CORS allows credentials (`allow_credentials=True`)
- [ ] CORS has specific origins (not wildcards)
- [ ] Cookies have `secure=True` in production
- [ ] Cookies have appropriate `domain` setting
- [ ] Frontend sends `credentials: 'include'`
- [ ] Both `/auth/token` and `/auth/logout` handle cookies

## Common Pitfalls

1. **CORS Wildcards**: `allow_origins=["*"]` breaks cookie support
2. **Missing credentials**: Frontend forgets `credentials: 'include'`
3. **HTTP in production**: Secure cookies won't work on HTTP
4. **Domain mismatch**: Cookie domain doesn't match request domain
5. **SameSite strict**: Can break OAuth flows

## Summary

The frontend is built for **maximum security** using httpOnly cookies. The backend MUST support this pattern or authentication will completely fail. This is not a preference—it's a requirement based on the frontend implementation.