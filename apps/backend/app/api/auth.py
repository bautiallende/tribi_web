from datetime import datetime, timedelta
import random
import smtplib
from email.message import EmailMessage

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, status, Header
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from ..db.session import get_db
from ..core.config import settings
from ..models import User, AuthCode
from ..schemas.auth import RequestCode, VerifyCode, TokenResponse, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


def send_email_smtp(to_email: str, subject: str, body: str):
    msg = EmailMessage()
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:
        smtp.send_message(msg)


@router.post("/request-code")
def request_code(payload: RequestCode, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    email = payload.email
    # find or create user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email)
        db.add(user)
        db.flush()

    # generate 6-digit code
    code = f"{random.randint(0, 999999):06d}"
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    auth_code = AuthCode(user_id=user.id, code=code, expires_at=expires_at, used=False)
    db.add(auth_code)
    db.commit()

    # send email in background
    subject = "Your Tribi login code"
    body = f"Your login code is: {code}. It expires in 10 minutes."
    background_tasks.add_task(send_email_smtp, email, subject, body)

    return {"message": "code_sent"}


@router.post("/verify", response_model=TokenResponse)
def verify_code(payload: VerifyCode, db: Session = Depends(get_db)):
    email = payload.email
    code = payload.code
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    now = datetime.utcnow()
    auth = (
        db.query(AuthCode)
        .filter(AuthCode.user_id == user.id, AuthCode.code == code, AuthCode.used.is_(False))
        .order_by(AuthCode.expires_at.desc())
        .first()
    )
    if not auth or auth.expires_at < now:
        raise HTTPException(status_code=400, detail="Invalid or expired code")

    # mark used
    auth.used = True
    user.last_login = now
    db.commit()

    # create JWT
    payload_jwt = {"sub": user.email, "exp": datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRES_MIN)}
    token = jwt.encode(payload_jwt, settings.JWT_SECRET, algorithm="HS256")

    return {"token": token, "user": UserRead.from_orm(user)}


def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)) -> User:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing credentials")
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError()
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth header")

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
