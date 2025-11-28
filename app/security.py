# 安全第一！我们绝不能在数据库中存储明文密码。我们将使用argon2-cffi库来处理密码的哈希和验证。
from passlib.context import CryptContext

# 1. 修改 CryptContext，将 argon2 作为首选方案
#    我们保留 bcrypt 是为了未来的兼容性，但默认不会使用它。
pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")

# 2. 验证密码的函数 (这个函数不需要任何改动)
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# 3. 哈希密码的函数 (这个函数也不需要任何改动)
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

