from fastapi import APIRouter, HTTPException ,Depends ,Request 
from datetime import datetime, timedelta, timezone

from authentication.core.db import get_db,Session
from authentication.schemas.auth import RegisterRequest, SendOTPRequest,VerifyOTPRequest, LoginRequest, ForgotPasswordRequest, ResetPasswordRequest

from authentication.model.auth import User , OTP
from authentication.core.security import (create_token,hash_password,generate_otp,verify_password,verify_access_token,hash_otp)

from authentication.utils.auth import OTPPurpose
from authentication.core.config import OTP_EXPIRE_MINUTES
from authentication.limiter import limiter


router = APIRouter()


# ------------------------
# helper
# ------------------------

def get_user(db:Session,email:str)-> User|None:
    return db.query(User).filter(User.email == email).first()

def cleanup_expired_otps(db: Session)->None:
    db.query(OTP).filter(
        OTP.expires_at < datetime.now(timezone.utc)
    ).delete()

def ensure_utc(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt
# ------------------------
# Register
# ------------------------

@router.post("/register")
@limiter.limit("5/minute")
def register(request:Request,data: RegisterRequest,db:Session = Depends(get_db))->dict:
    existing_user = get_user(db,data.email)

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User already exists"
        )

    new_user = User(
        email=data.email,
        password=hash_password(data.password),  # Hash in production
        verified=False
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "Registered successfully"
    }


# ------------------------
# Send OTP
# ------------------------

@router.post("/send-otp")
@limiter.limit("5/minute")
def send_otp(request:Request,data: SendOTPRequest,db:Session = Depends(get_db))->dict:

    user = get_user(db,data.email)

    if not user:
        raise HTTPException(401, "Invalid email or password")
    
    if user.verified:
        raise HTTPException(
            status_code=400,
            detail="Email already verified"
        )

    otp = generate_otp()
    otp_hash = hash_otp(otp)

    # flush db
    cleanup_expired_otps(db)

    db.query(OTP).filter(
        OTP.user_id == user.id,
        OTP.purpose == OTPPurpose.REGISTER,
        OTP.used == False
    ).delete()


    new_otp = OTP(
        user_id=user.id,
        otp_hash=otp_hash,
        purpose=OTPPurpose.REGISTER,
        expires_at=datetime.now(timezone.utc)
        + timedelta(minutes=int(OTP_EXPIRE_MINUTES))
    )

    db.add(new_otp)
    db.commit()

    # Simulate sending email
    print(f"OTP for {data.email}: {otp}")

    return {
        "message": "OTP sent"
    }


# ------------------------
# Verify OTP
# ------------------------

@router.post("/verify-otp")
@limiter.limit("5/minute")
def verify_otp(request:Request,data: VerifyOTPRequest,db:Session = Depends(get_db))->dict:

    otp_hash = hash_otp(data.otp)

    user = get_user(db,data.email)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    otp = db.query(OTP).filter(
        OTP.user_id == user.id,
        OTP.purpose == OTPPurpose.REGISTER,
        OTP.used == False
    ).first()

    if otp is None:
        raise HTTPException(400, "OTP expired")
    
    db_expiry = ensure_utc(otp.expires_at)


    if db_expiry < datetime.now(timezone.utc):
        raise HTTPException(400, "OTP expired")

    if otp.otp_hash != otp_hash:
        raise HTTPException(400, "Invalid OTP")
    
    
    otp.used = True
    user.verified = True

    db.commit()
    
    return {
        "message": "Email verified successfully"
    }

# ------------------------
# Verify LOGIN
# ------------------------
@router.post("/login")
@limiter.limit("5/minute")
def login(request:Request,data: LoginRequest,db:Session = Depends(get_db))->dict:

    # Find user
    user = get_user(db,data.email)
    
    if user is None or not verify_password(data.password, user.password):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )


    # Check email verification
    if not user.verified:
        raise HTTPException(
            status_code=403,
            detail="Please verify your email first"
        )
    

    token = create_token({"sub":str(user.id)})


    return {
        "message": "Login successful",
        "user": {
                "email": user.email,
                "verified": user.verified
            },
        "access_token": token,
        "token_type": "bearer"
    }

@router.post("/forgot-password")
@limiter.limit("5/minute")
def forgot_password(
    request:Request,
    data: ForgotPasswordRequest,
    db: Session = Depends(get_db)
)->dict:
    user = get_user(db,data.email)

    # Don't reveal whether the email exists
    if user is None:
        return {
            "message": "If the email exists, an OTP has been sent."
        }

    if not user.verified:
        raise HTTPException(
            status_code=400,
            detail="Please verify your email first."
        )

    otp = generate_otp()
    otp_hash = hash_otp(otp)

    cleanup_expired_otps(db)

    db.query(OTP).filter(
        OTP.user_id == user.id,
        OTP.purpose == OTPPurpose.FORGOT_PASSWORD,
        OTP.used == False
    ).delete()

    new_otp = OTP(
        user_id=user.id,
        otp_hash=otp_hash,
        purpose=OTPPurpose.FORGOT_PASSWORD,
        expires_at=datetime.now(timezone.utc)
        + timedelta(minutes=int(OTP_EXPIRE_MINUTES))
    )

    db.add(new_otp)
    db.commit()

    # TODO: Send email
    print(f"Forgot Password OTP: {otp}")

    return {
        "message": "If the email exists, an OTP has been sent."
    }

@router.post("/reset-password")
@limiter.limit("5/minute")
def reset_password(request:Request,
    data: ResetPasswordRequest,
    db: Session = Depends(get_db)
)->dict:
    # Find user
    user = get_user(db,data.email)

    if user is None:
        raise HTTPException(
            status_code=400,
            detail="Invalid email or OTP"
        )

    # Find active OTP
    otp = db.query(OTP).filter(
        OTP.user_id == user.id,
        OTP.purpose == OTPPurpose.FORGOT_PASSWORD,
        OTP.used == False
    ).first()

    if otp is None:
        raise HTTPException(
            status_code=400,
            detail="OTP expired"
        )

    # Check expiry
    db_expiry = ensure_utc(otp.expires_at)
    if db_expiry < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=400,
            detail="OTP expired"
        )

    # Verify OTP
    otp_hash = hash_otp(data.otp)

    if otp_hash != otp.otp_hash:
        raise HTTPException(
            status_code=400,
            detail="Invalid OTP"
        )

    # Prevent using the same password again (optional but recommended)
    if verify_password(data.new_password, user.password):
        raise HTTPException(
            status_code=400,
            detail="New password must be different from the current password"
        )

    # Update password
    user.password = hash_password(data.new_password)

    # Invalidate OTP
    otp.used = True

    db.commit()

    return {
        "message": "Password reset successfully"
    }

# protected route
@router.post("/admin")
def admin(data = Depends(verify_access_token))->dict:
    print(data)
    return data