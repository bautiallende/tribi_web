from datetime import datetime, timedelta
import random
from email.message import EmailMessage

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, status, Header, Request, Response, Cookie
from sqlalchemy.orm import Session
from sqlalchemy import func
from jose import jwt, JWTError

from ..db.session import get_db
from ..core.config import settings
from ..models import User, AuthCode
from ..schemas.auth import RequestCode, VerifyCode, TokenResponse, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


def send_email_smtp(to_email: str, subject: str, body: str):
    """Send email via SMTP with optional TLS."""
    # Print code in dev mode for easy access
    print(f"\n{'='*50}")
    print(f"📧 EMAIL TO: {to_email}")
    print(f"📋 SUBJECT: {subject}")
    print(f"📝 BODY: {body}")
    print(f"{'='*50}\n")
    
    msg = EmailMessage()
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        if settings.SMTP_USE_TLS and settings.SMTP_USER:
            import smtplib
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:
                smtp.starttls()
                smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                smtp.send_message(msg)
        else:
            # Dev mode - MailHog doesn't need auth
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:
                smtp.send_message(msg)
    except Exception as e:
        print(f"⚠️  Failed to send email: {e}")
        # Don't fail the request if email fails in dev


def get_client_ip(request: Request) -> str:
    """Extract client IP from request, considering proxies."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def check_rate_limit(email: str, ip_address: str, db: Session) -> None:
    """Check rate limits for OTP requests (email+IP based)."""
    now = datetime.utcnow()
    
    # Check 1 code per minute limit
    one_minute_ago = now - timedelta(seconds=settings.RATE_LIMIT_WINDOW_SECONDS)
    recent_code = (
        db.query(AuthCode)
        .filter(
            AuthCode.email == email,
            AuthCode.ip_address == ip_address,
            AuthCode.created_at >= one_minute_ago
        )
        .first()
    )
    if recent_code:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Please wait {settings.RATE_LIMIT_WINDOW_SECONDS} seconds between requests"
        )
    
    # Check 5 codes per 24 hours limit
    one_day_ago = now - timedelta(hours=settings.RATE_LIMIT_WINDOW_HOURS)
    codes_today = (
        db.query(func.count(AuthCode.id))
        .filter(
            AuthCode.email == email,
            AuthCode.ip_address == ip_address,
            AuthCode.created_at >= one_day_ago
        )
        .scalar()
    )
    if codes_today >= settings.RATE_LIMIT_CODES_PER_DAY:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Maximum {settings.RATE_LIMIT_CODES_PER_DAY} codes per {settings.RATE_LIMIT_WINDOW_HOURS} hours exceeded"
        )


@router.post("/request-code")
def request_code(
    payload: RequestCode,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Request OTP code with rate limiting."""
    email = payload.email
    ip_address = get_client_ip(request)
    
    # Check rate limits
    check_rate_limit(email, ip_address, db)
    
    # Find or create user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email)
        db.add(user)
        db.flush()

    # Generate 6-digit code
    code = f"{random.randint(0, 999999):06d}"
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    auth_code = AuthCode(
        user_id=user.id,
        email=email,
        code=code,
        expires_at=expires_at,
        used=False,
        ip_address=ip_address,
        attempts=0
    )
    db.add(auth_code)
    db.commit()

    # Send email in background
    subject = "Your Tribi login code"
    body = f"Your login code is: {code}. It expires in 10 minutes."
    background_tasks.add_task(send_email_smtp, email, subject, body)

    return {"message": "code_sent"}


@router.post("/verify", response_model=TokenResponse)
def verify_code(
    payload: VerifyCode,
    response: Response,
    db: Session = Depends(get_db)
):
    """Verify OTP code and return JWT (also set cookie for web)."""
    email = payload.email
    code = payload.code
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    now = datetime.utcnow()
    auth = (
        db.query(AuthCode)
        .filter(
            AuthCode.user_id == user.id,
            AuthCode.code == code,
            AuthCode.used == False  # noqa: E712
        )
        .order_by(AuthCode.expires_at.desc())
        .first()
    )
    
    if not auth:
        raise HTTPException(status_code=400, detail="Invalid code")
    
    if auth.expires_at < now:
        raise HTTPException(status_code=400, detail="Code expired")

    # Mark used
    auth.used = True  # type: ignore
    user.last_login = now  # type: ignore
    db.commit()

    # Create JWT
    payload_jwt = {
        "sub": user.email,
        "exp": datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRES_MIN)
    }
    token = jwt.encode(payload_jwt, settings.JWT_SECRET, algorithm="HS256")
    
    # Set httpOnly cookie for web clients
    response.set_cookie(
        key="tribi_token",
        value=token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=settings.JWT_EXPIRES_MIN * 60,
        domain=settings.COOKIE_DOMAIN
    )

    # Return token and user info
    from ..schemas.auth import UserRead
    return TokenResponse(
        token=token,
        user=UserRead.from_orm(user)
    )


@router.post("/logout")
def logout(response: Response):
    """Logout by clearing the auth cookie."""
    response.delete_cookie(
        key="tribi_token",
        httponly=True,
        secure=False,
        samesite="lax",
        domain=settings.COOKIE_DOMAIN
    )
    return {"message": "logged_out"}


def get_current_user(
    authorization: str | None = Header(None),
    tribi_token: str | None = Cookie(None),
    db: Session = Depends(get_db)
) -> User:
    """Get current user from Bearer token or cookie."""
    token = None
    
    # Try cookie first (web), then header (mobile)
    if tribi_token:
        token = tribi_token
    elif authorization:
        try:
            scheme, token_value = authorization.split()
            if scheme.lower() == "bearer":
                token = token_value
        except Exception:
            pass
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing credentials"
        )

    try:
        data = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        email = data.get("sub")
        if not email:
            raise JWTError()
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/me", response_model=UserRead)
def read_me(current_user: User = Depends(get_current_user)):
    return UserRead.from_orm(current_user)


def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """Get current user and validate they are an admin."""
    user_email_lower = current_user.email.lower()
    admin_list = settings.admin_emails_list
    
    # Debug logging
    print(f"\n🔍 Admin check:")
    print(f"  User email: {current_user.email} (lowercase: {user_email_lower})")
    print(f"  Admin emails from config: {admin_list}")
    print(f"  ADMIN_EMAILS env var: {settings.ADMIN_EMAILS}")
    print(f"  Is admin: {user_email_lower in admin_list}\n")
    
    if user_email_lower not in admin_list:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user
