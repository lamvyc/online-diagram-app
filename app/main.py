from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from . import models, schemas, crud
from .database import engine, SessionLocal

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# --- Dependency ---
# 创建一个依赖项，用于在每个请求中获取数据库会话
# 它会创建一个会话，在请求处理完后关闭它
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def read_root():
    return {"message": "你好，欢迎来到在线流程图API！"}


# --- User Registration Endpoint ---
@app.post("/auth/register", response_model=schemas.UserOut)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # 1. 检查用户名是否已存在
    db_user_by_username = crud.get_user_by_username(db, username=user.username)
    if db_user_by_username:
        raise HTTPException(status_code=400, detail="用户名已被注册")

    # 2. 检查邮箱是否已存在
    db_user_by_email = crud.get_user_by_email(db, email=user.email)
    if db_user_by_email:
        raise HTTPException(status_code=400, detail="邮箱已被注册")

    # 3. 创建新用户
    new_user = crud.create_user(db=db, user=user)
    return new_user

# 总结：
# Depends(get_db): 这是FastAPI的“依赖注入”系统。它告诉FastAPI，在调用register_user函数之前，必须先执行get_db函数，并将其返回的db会话对象作为参数传入。
# response_model=schemas.UserOut: 这非常重要！它强制API的响应体必须符合UserOut模型的结构，自动过滤掉password_hash等敏感字段，确保不会泄露给客户端。
# HTTPException: 这是FastAPI处理业务错误的標準方式，可以方便地返回指定的HTTP状态码和错误信息。