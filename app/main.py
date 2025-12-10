from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
# ‼️ 导入 FastAPI 的请求验证错误类
from fastapi.exceptions import RequestValidationError
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

# --- ‼️ NEW: 自定义异常处理器 ---
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    捕获并自定义处理 Pydantic 的请求体验证错误。
    """
    error_messages = []
    
    # ‼️ 检查是否是 JSON decode error
    # 这种错误的 errors() 列表通常只有一个元素
    if len(exc.errors()) == 1 and exc.errors()[0]['type'] == 'json_invalid':
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, # 对于无效JSON，400更合适
            content={
                "detail": "无效的JSON格式 (Invalid JSON format)",
                "error_detail": exc.errors()[0]['msg'] # 直接使用原始的解码错误信息
            },
        )
    for error in exc.errors():
        # 'loc' 是一个元组，例如 ('body', 'username')
        # 我们把它转换成 'body.username' 的形式
        field_path = ".".join(str(loc_item) for loc_item in error['loc'])
        
        error_type = error['type']
        msg = error['msg']
        
        # 根据不同的错误类型，生成更友好的消息
        if error_type == 'missing':
            message = f"字段 '{field_path}' 是必需的 (Field is required)。"
        elif 'string' in error_type:
            message = f"字段 '{field_path}' 必须是有效的字符串 (Must be a valid string)。"
        elif error_type == 'value_error':
            # 这种通常是 pydantic 自定义校验的错误，msg 已经足够清晰
            message = f"字段 '{field_path}' 的值无效: {msg}"
        else:
            # 对于其他未知错误，保留原始消息
            message = f"字段 '{field_path}' 发生错误: {msg}"
            
        error_messages.append({"error_field": field_path, "error_detail": message})

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "请求体验证失败 (Request body validation failed)", "errors": error_messages},
    )

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
        "description": "输入你的 Bearer Token. 格式: 'Bearer &lt;token&gt;（只粘贴 token 本身）'"
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

@app.get("/diagrams", response_model=list[schemas.Diagram])
def read_diagrams(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(security.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    获取当前登录用户的所有流程图列表。
    支持分页查询。
    """
    diagrams = crud.get_user_diagrams(db, user_id=current_user.id, skip=skip, limit=limit)
    return diagrams

@app.get("/diagrams/{diagram_id}", response_model=schemas.Diagram)
def read_diagram(
    diagram_id: int,
    db: Session = Depends(security.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    获取单个流程图的详细信息。
    只能获取属于当前登录用户的流程图。
    """
    # 1. 从数据库获取图
    db_diagram = crud.get_diagram(db, diagram_id=diagram_id)
    
    # 2. 检查图是否存在
    if db_diagram is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="流程图未找到")
        
    # 3. ‼️ 关键：检查图的所有者是否是当前用户
    if db_diagram.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问此资源")
        
    # 4. 如果所有检查都通过，返回图的信息
    return db_diagram

@app.put("/diagrams/{diagram_id}", response_model=schemas.Diagram)
def update_diagram_route(
    diagram_id: int,
    diagram_update: schemas.DiagramUpdate,
    db: Session = Depends(security.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    更新指定的流程图。
    只能更新属于当前登录用户的流程图。
    """
    # 1. 复用权限校验逻辑
    db_diagram = crud.get_diagram(db, diagram_id=diagram_id)
    if db_diagram is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="流程图未找到")
    if db_diagram.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问此资源")
        
    # 2. 调用CRUD函数执行更新
    return crud.update_diagram(db=db, db_diagram=db_diagram, diagram_update=diagram_update)


@app.delete("/diagrams/{diagram_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_diagram_route(
    diagram_id: int,
    db: Session = Depends(security.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    删除指定的流程图。
    只能删除属于当前登录用户的流程图。
    """
    # 1. 再次复用权限校验逻辑
    db_diagram = crud.get_diagram(db, diagram_id=diagram_id)
    if db_diagram is None:
        # 即使图不存在，对于DELETE操作，返回404也是合适的
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="流程图未找到")
    if db_diagram.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问此资源")
        
    # 2. 调用CRUD函数执行删除
    crud.delete_diagram(db=db, db_diagram=db_diagram)
    
    # 3. 对于 204 状态码，FastAPI 不会发送任何响应体
    return None


# 总结：
# Depends(get_db): 这是FastAPI的“依赖注入”系统。它告诉FastAPI，在调用register_user函数之前，必须先执行get_db函数，并将其返回的db会话对象作为参数传入。
# response_model=schemas.UserOut: 这非常重要！它强制API的响应体必须符合UserOut模型的结构，自动过滤掉password_hash等敏感字段，确保不会泄露给客户端。
# HTTPException: 这是FastAPI处理业务错误的標準方式，可以方便地返回指定的HTTP状态码和错误信息。