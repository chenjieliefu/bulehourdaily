"""鉴权接口结构。"""
from pydantic import BaseModel, Field, field_validator


class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=6, max_length=128)
    invite_code: str = Field(min_length=1, max_length=64)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        """密码只允许 ASCII 可打印非空白字符（码点 33–126）。

        排除空格、制表符、换行、中文、全角空格和 emoji。
        """
        if any(ord(c) < 33 or ord(c) > 126 for c in value):
            raise ValueError("密码不能包含空格或中文字符，请使用字母、数字和常见符号")
        return value


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=128)


class UserRead(BaseModel):
    id: int
    email: str
    is_operator: bool = False


class AuthResponse(BaseModel):
    token: str
    user: UserRead
