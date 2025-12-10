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

def get_user_diagrams(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    """
    根据用户ID获取其所有的流程图，支持分页。
    """
    return db.query(models.Diagram).filter(models.Diagram.user_id == user_id).offset(skip).limit(limit).all()

def get_diagram(db: Session, diagram_id: int):
    """
    根据ID获取单个流程图。
    """
    return db.query(models.Diagram).filter(models.Diagram.id == diagram_id).first()

def update_diagram(db: Session, db_diagram: models.Diagram, diagram_update: schemas.DiagramUpdate):
    """
    更新指定的流程图。
    """
    # 1. 获取 Pydantic 模型中的数据，并转为字典
    update_data = diagram_update.model_dump(exclude_unset=True)
    
    # 2. 遍历字典，更新 SQLAlchemy 模型对象的属性
    for key, value in update_data.items():
        setattr(db_diagram, key, value)
        
    # 3. 提交更改
    db.add(db_diagram)
    db.commit()
    db.refresh(db_diagram)
    return db_diagram


# --- NEW: Delete Diagram Function ---

def delete_diagram(db: Session, db_diagram: models.Diagram):
    """
    删除指定的流程图。
    """
    db.delete(db_diagram)
    db.commit()
    # 删除后，我们通常不返回任何东西，所以在路由层直接返回一个成功状态即可
