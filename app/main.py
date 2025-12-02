from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from fastapi.openapi.utils import get_openapi

# 导入项目中的模块
from . import models, schemas, crud, security
from .database import engine

# 创建数据库表
models.Base.metadata.create_all(bind=engine)

# 创建FastAPI应用实例
app = FastAPI()

# --- 终极自定义OpenAPI Schema ---
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    # 1. 获取默认的schema
    openapi_schema = get_openapi(
        title="在线流程图 API",
        version="1.0.0",
        description="一个用于在线绘制和保存流程图的后端API服务",
        routes=app.routes,
    )
    
    # 2. 找到 `components` -> `securitySchemes`
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
    if "securitySchemes" not in openapi_schema["components"]:
        openapi_schema["components"]["securitySchemes"] = {}
        
    # 3. 强制用我们想要的、最简单的 Bearer Token 认证方案来覆盖它
    openapi_schema["components"]["securitySchemes"]["OAuth2PasswordBearer"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "输入你的 Bearer Token. 格式: 'Bearer &lt;token&gt;'"
    }
            
    app.openapi_schema = openapi_schema
    return app.openapi_schema

# 4. 应用这个自定义函数
app.openapi = custom_openapi

# --- 根路由 ---
@app.get("/")
def read_root():
    return {"message": "你好，欢迎来到在线流程图API！"}

# --- 认证路由 ---

@app.post("/auth/register", response_model=schemas.UserOut)
def register_user(user: schemas.UserCreate, db: Session = Depends(security.get_db)):
    db_user_by_username = crud.get_user_by_username(db, username=user.username)
    if db_user_by_username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已被注册")

    db_user_by_email = crud.get_user_by_email(db, email=user.email)
    if db_user_by_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="邮箱已被注册")

    new_user = crud.create_user(db=db, user=user)
    return new_user

@app.post("/auth/login", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(security.get_db)):
    # 1. 根据用户名从数据库查找用户
    user = crud.get_user_by_username(db, username=form_data.username)
    
    # 2. 验证用户是否存在，以及密码是否正确
    if not user or not security.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="不正确的用户名或密码",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # 3. 如果验证成功，为该用户创建一个access token
    access_token = security.create_access_token(
        data={"sub": user.username}
    )
    
    # 4. 返回token
    return {"access_token": access_token, "token_type": "bearer"}


# --- 用户路由 (受保护) ---

@app.get("/users/me", response_model=schemas.UserOut)
def read_users_me(current_user: models.User = Depends(security.get_current_user)):
    """
    获取当前登录用户的信息。
    这个接口受OAuth2保护，请求时需要在Authorization header中提供Bearer Token。
    """
    return current_user

@app.post("/diagrams", response_model=schemas.Diagram, status_code=status.HTTP_201_CREATED)
def create_diagram(
    diagram: schemas.DiagramCreate, 
    db: Session = Depends(security.get_db), 
    current_user: models.User = Depends(security.get_current_user)
):
    """
    为当前登录用户创建一个新的流程图。
    
    - **title**: 流程图的标题。
    - **content**: (可选) 流程图的初始JSON内容。
    """
    return crud.create_user_diagram(db=db, diagram=diagram, user_id=current_user.id)


# 总结：
# Depends(get_db): 这是FastAPI的“依赖注入”系统。它告诉FastAPI，在调用register_user函数之前，必须先执行get_db函数，并将其返回的db会话对象作为参数传入。
# response_model=schemas.UserOut: 这非常重要！它强制API的响应体必须符合UserOut模型的结构，自动过滤掉password_hash等敏感字段，确保不会泄露给客户端。
# HTTPException: 这是FastAPI处理业务错误的標準方式，可以方便地返回指定的HTTP状态码和错误信息。