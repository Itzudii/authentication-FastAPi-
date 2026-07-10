
from enum import StrEnum

class OTPPurpose(StrEnum):
    REGISTER = "register"
    LOGIN = "login"
    FORGOT_PASSWORD = "forgot_password"