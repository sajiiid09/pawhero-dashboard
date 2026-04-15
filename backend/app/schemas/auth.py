from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    owner_id: str
    display_name: str


class RegisterResponse(BaseModel):
    owner_id: str
    email: EmailStr
    display_name: str
    verification_required: bool
    message: str


class VerifyOtpRequest(BaseModel):
    email: EmailStr
    code: str


class ResendOtpRequest(BaseModel):
    email: EmailStr


class ResendOtpResponse(BaseModel):
    message: str
