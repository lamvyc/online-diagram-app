from passlib.context import CryptContext

from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt

# 引入我们项目中的其他模块
from . import schemas, crud  # crud在这里是隐式使用的，通过main.py调用
from .database import SessionLocal # 直接从database导入SessionLocal，用于get_db

# 1. 修改 CryptContext，将 argon2 作为首选方案
#    我们保留 bcrypt 是为了未来的兼容性，但默认不会使用它。
pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")

# 2. 验证密码的函数 (这个函数不需要任何改动)
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# 3. 哈希密码的函数 (这个函数也不需要任何改动)
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# --- JWT Configuration ---
# !! 替换成你自己生成的密钥 !!
SECRET_KEY = "376a6fe3ab778d2071075697dbf498f957fb79bc109156c665960b83fe61ed42"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 300  # Token 有效期300分钟

# --- JWT Creator Function ---
def create_access_token(data: dict):
    to_encode = data.copy()
    # 计算过期时间
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    # 使用 PyJWT 编码
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# --- FastAPI Dependency: OAuth2PasswordBearer ---
# 这个对象会告诉FastAPI去哪里寻找Token。
# tokenUrl="auth/login" 指明了获取token的端点是 /auth/login。
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


# --- FastAPI Dependency: get_db ---
# 我们把get_db也放在这里，或者保持在main.py，但为了让get_current_user能直接用，这里也需要能访问到它
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Core Dependency: Token Verification and User Retrieval ---
# 这是我们的“门禁守卫”
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据 (Could not validate credentials)",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # 1. 解码JWT
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # 2. 从payload中获取用户名
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
            
        # 3. 将用户名包装在Pydantic模型中
        token_data = schemas.TokenData(username=username)
    except JWTError:
        # 如果解码失败 (如token格式错误、过期等)，抛出异常
        raise credentials_exception
        
    # 4. 使用用户名从数据库中获取用户
    # 注意：这里我们直接调用crud.py里的函数
    user = crud.get_user_by_username(db, username=token_data.username)
    if user is None:
        # 如果在数据库中找不到该用户 (例如用户被删除)，也抛出异常
        raise credentials_exception
        
    # 5. 返回完整的User对象
    return user
