import datetime as dt
import random
import smtplib
from datetime import timedelta
from email.message import EmailMessage
from typing import cast

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Cookie,
    Depends,
    Header,
    HTTPException,
    Request,
    Response,
    status,
)
from jose import JWTError, jwt
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..core.config import settings
from ..db.session import get_db
from ..models import AuthCode, User
from ..schemas.auth import RequestCode, TokenResponse, UserRead, VerifyCode
from ..services import AnalyticsEventType, record_event

router = APIRouter(prefix="/api/auth", tags=["auth"])


def send_email_smtp(to_email: str, subject: str, body: str):
    """Send email via SMTP with optional TLS."""
    # Print code in dev mode for easy access
    print(f"\n{'='*50}")
    print(f"📧 EMAIL TO: {to_email}")
    print(f"📋 SUBJECT: {subject}")
    print(f"📝 BODY: {body}")
    print(f"{'='*50}\n")

    # In development, just print the code - don't try to send actual email
    if not settings.SMTP_USER:
        print("📧 Development mode: Email not sent (SMTP not configured)")
        return

    msg = EmailMessage()
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        if settings.SMTP_USE_TLS:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:
                smtp.starttls()
                smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD or "")
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:
                smtp.send_message(msg)
        print("✅ Email sent successfully")
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
    now = dt.datetime.utcnow()

    # Check 1 code per minute limit
    one_minute_ago = now - timedelta(seconds=settings.RATE_LIMIT_WINDOW_SECONDS)
    recent_code = (
        db.query(AuthCode)
        .filter(
            AuthCode.email == email,
            AuthCode.ip_address == ip_address,
            AuthCode.created_at >= one_minute_ago,
        )
        .first()
    )
    if recent_code:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Please wait {settings.RATE_LIMIT_WINDOW_SECONDS}s between requests",
        )

    # Check 5 codes per 24 hours limit
    one_day_ago = now - timedelta(hours=settings.RATE_LIMIT_WINDOW_HOURS)
    codes_today = (
        db.query(func.count(AuthCode.id))
        .filter(
            AuthCode.email == email,
            AuthCode.ip_address == ip_address,
            AuthCode.created_at >= one_day_ago,
        )
        .scalar()
    )
    if codes_today >= settings.RATE_LIMIT_CODES_PER_DAY:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Maximum {settings.RATE_LIMIT_CODES_PER_DAY} codes per {settings.RATE_LIMIT_WINDOW_HOURS}h exceeded",
        )

    # Check IP-level quota window
    if ip_address and ip_address != "unknown":
        ip_codes_today = (
            db.query(func.count(AuthCode.id))
            .filter(
                AuthCode.ip_address == ip_address,
                AuthCode.created_at >= one_day_ago,
            )
            .scalar()
        )
        if ip_codes_today >= settings.RATE_LIMIT_CODES_PER_IP_PER_DAY:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    "Too many codes requested from this IP; try again later or contact support"
                ),
            )


@router.post("/request-code")
def request_code(
    payload: RequestCode,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
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
        record_event(
            db,
            event_type=AnalyticsEventType.USER_SIGNUP,
            user_id=cast(int, user.id),
            metadata={"source": "otp_request"},
        )

    # Generate 6-digit code
    code = f"{random.randint(0, 999999):06d}"
    expires_at = dt.datetime.utcnow() + timedelta(minutes=10)
    auth_code = AuthCode(
        user_id=user.id,
        email=email,
        code=code,
        expires_at=expires_at,
        used=False,
        ip_address=ip_address,
        attempts=0,
    )
    db.add(auth_code)
    db.commit()

    # Send email in background
    subject = "Your Tribi login code"
    body = f"Your login code is: {code}. It expires in 10 minutes."
    background_tasks.add_task(send_email_smtp, email, subject, body)

    return {"message": "code_sent"}


@router.post("/verify", response_model=TokenResponse)
def verify_code(payload: VerifyCode, response: Response, db: Session = Depends(get_db)):
    """Verify OTP code and return JWT (also set cookie for web)."""
    email = payload.email
    code = payload.code

    print("\n🔐 Verify code called:")
    print(f"  Email: {email}")
    print(f"  Code: {code}")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        print("  ❌ User not found")
        raise HTTPException(status_code=404, detail="User not found")

    now = dt.datetime.utcnow()
    auth = (
        db.query(AuthCode)
        .filter(
            AuthCode.user_id == user.id,
            AuthCode.code == code,
            AuthCode.used == False,  # noqa: E712
        )
        .order_by(AuthCode.expires_at.desc())
        .first()
    )

    if not auth:
        print("  ❌ Invalid code")
        raise HTTPException(status_code=400, detail="Invalid code")

    auth_expires = cast(dt.datetime, auth.expires_at)
    if auth_expires < now:
        print("  ❌ Code expired")
        raise HTTPException(status_code=400, detail="Code expired")

    # Mark used
    auth.used = True  # type: ignore
    user.last_login = now  # type: ignore
    db.commit()

    print("  ✅ Code verified")

    # Create JWT
    payload_jwt = {
        "sub": user.email,
        "exp": dt.datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRES_MIN),
    }
    token = jwt.encode(payload_jwt, settings.JWT_SECRET, algorithm="HS256")

    secure_flag = settings.cookie_secure_flag
    samesite_value = settings.cookie_samesite_value
    if samesite_value == "none" and not secure_flag:
        secure_flag = True

    print(f"  🔑 JWT created: {token[:20]}...")
    print("  🍪 Setting cookie:")
    print("     key: tribi_token")
    print("     httponly: True")
    print(f"     secure: {secure_flag}")
    print(f"     samesite: {samesite_value}")
    print(f"     max_age: {settings.JWT_EXPIRES_MIN * 60} seconds")
    print(f"     domain: {settings.COOKIE_DOMAIN}")

    # Set httpOnly cookie for web clients
    response.set_cookie(
        key="tribi_token",
        value=token,
        httponly=True,
        secure=secure_flag,
        samesite=samesite_value,
        max_age=settings.JWT_EXPIRES_MIN * 60,
        domain=settings.COOKIE_DOMAIN,
    )

    print("  ✅ Cookie set successfully\n")

    # Return token and user info
    from ..schemas.auth import UserRead

    return TokenResponse(token=token, user=UserRead.model_validate(user))


@router.post("/logout")
def logout(response: Response):
    """Logout by clearing the auth cookie."""
    secure_flag = settings.cookie_secure_flag
    samesite_value = settings.cookie_samesite_value
    if samesite_value == "none" and not secure_flag:
        secure_flag = True

    response.delete_cookie(
        key="tribi_token",
        httponly=True,
        secure=secure_flag,
        samesite=samesite_value,
        domain=settings.COOKIE_DOMAIN,
    )
    return {"message": "logged_out"}


def get_current_user(
    authorization: str | None = Header(None),
    tribi_token: str | None = Cookie(None),
    db: Session = Depends(get_db),
) -> User:
    """Get current user from Bearer token or cookie."""
    token = None

    # Debug logging
    print("\n🔐 get_current_user called:")
    print(f"  Cookie (tribi_token): {'✅ Present' if tribi_token else '❌ Missing'}")
    print(f"  Header (Authorization): {'✅ Present' if authorization else '❌ Missing'}")

    # Try cookie first (web), then header (mobile)
    if tribi_token:
        token = tribi_token
        print(f"  Using cookie token: {tribi_token[:20]}...")
    elif authorization:
        try:
            scheme, token_value = authorization.split()
            if scheme.lower() == "bearer":
                token = token_value
                print(f"  Using bearer token: {token[:20]}...")
        except Exception as e:
            print(f"  ❌ Failed to parse authorization header: {e}")
            pass

    if not token:
        print("  ❌ No token found - returning 401\n")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing credentials"
        )

    try:
        data = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        email = data.get("sub")
        print("  ✅ Token decoded successfully")
        print(f"  Email from token: {email}")
        if not email:
            raise JWTError()
    except JWTError as e:
        print(f"  ❌ JWT decode error: {e}\n")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    user = db.query(User).filter(User.email == email).first()
    if not user:
        print("  ❌ User not found in database\n")
        raise HTTPException(status_code=404, detail="User not found")

    print(f"  ✅ User authenticated: {user.email}\n")
    return user


@router.get("/me", response_model=UserRead)
def read_me(current_user: User = Depends(get_current_user)):
    return UserRead.model_validate(current_user)


def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """Get current user and validate they are an admin."""
    user_email_lower = current_user.email.lower()
    admin_list = settings.admin_emails_list

    # Debug logging
    print("\n🔍 Admin check:")
    print(f"  User email: {current_user.email} (lowercase: {user_email_lower})")
    print(f"  Admin emails from config: {admin_list}")
    print(f"  ADMIN_EMAILS env var: {settings.ADMIN_EMAILS}")
    print(f"  Is admin: {user_email_lower in admin_list}\n")

    if user_email_lower not in admin_list:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )
    return current_user
