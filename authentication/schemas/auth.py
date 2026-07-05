from pydantic import BaseModel, EmailStr

from enum import StrEnum

class OTPPurpose(StrEnum):
    REGISTER = "register"
    LOGIN = "login"
    FORGOT_PASSWORD = "forgot_password"
# ------------------------
# Schemas
# ------------------------

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class SendOTPRequest(BaseModel):
    email: EmailStr


class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str