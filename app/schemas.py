''' 
首先，我们要定义API的“数据合同”。Pydantic模型（在FastAPI中通常称为Schemas）可以确保前端发送的数据格式是正确的，
并且我们也能控制返回给前端的数据内容（例如，绝不能返回密码哈希）。
'''
# 使用三引号字符串（''' 或 """）—— 实际是字符串，不是注释！
from pydantic import BaseModel, EmailStr
import datetime
from typing import Optional

# --- User Schemas ---

# 用于接收用户创建请求的Schema (输入)
class UserCreate(BaseModel):
    username: str
    email: EmailStr  # pydantic会自动校验邮件格式
    password: str

# 用于API响应的Schema (输出)
# 作用：从数据库读取数据并返回给客户端时，过滤掉敏感信息
class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: datetime.datetime

    # from_attributes = True 告诉Pydantic模型去读取SQLAlchemy模型的数据
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None


