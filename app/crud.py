# 为了让API路由的逻辑保持干净，我们将所有直接与数据库交互的函数都封装起来。这是一种很好的实践，称为“仓储模式”(Repository Pattern)。
from sqlalchemy.orm import Session
from . import models, schemas, security

# --- User CRUD ---

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    # 1. 对明文密码进行哈希
    hashed_password = security.get_password_hash(user.password)
    
    # 2. 创建一个SQLAlchemy User模型实例
    db_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password
    )
    
    # 3. 将实例添加到数据库会话中
    db.add(db_user)
    # 4. 提交会话，将更改写入数据库
    db.commit()
    # 5. 刷新实例，以获取数据库生成的新数据（如ID）
    db.refresh(db_user)
    
    return db_user

def create_user_diagram(db: Session, diagram: schemas.DiagramCreate, user_id: int):
    """
    为指定用户创建一个新的流程图。
    """
    # 创建一个SQLAlchemy Diagram模型实例
    db_diagram = models.Diagram(
        **diagram.model_dump(),  # 将Pydantic模型转为字典
        user_id=user_id
    )
    
    db.add(db_diagram)
    db.commit()
    db.refresh(db_diagram)
    return db_diagram

