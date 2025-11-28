# 现在，我们要把之前设计的 users 和 diagrams 表，用Python代码的形式“画”出来。这些类就是所谓的ORM模型。
from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, JSON, text # <-- Import 'text'
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    # --- CHANGE HERE ---
    created_at = Column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP'))

    # 'diagrams'是给User模型添加的一个属性，方便地访问该用户所有的流程图
    # back_populates="owner" 表示这个关系与Diagram模型中的'owner'属性是相互关联的
    diagrams = relationship("Diagram", back_populates="owner")


class Diagram(Base):
    # __tablename__ 精确指定了这个类对应数据库里的表名。
    __tablename__ = "diagrams"

    # Column(...) 定义了表里的每一个字段，包括它的数据类型、是否是主键等约束。
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), default="未命名流程图")
    content = Column(JSON, nullable=True)
    share_uuid = Column(String(36), unique=True, index=True, nullable=True)
    
    # --- AND CHANGE HERE ---
    created_at = Column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updated_at = Column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    
    user_id = Column(Integer, ForeignKey("users.id"))
    # 'owner'是给Diagram模型添加的一个属性，方便地访问这张图的创建者(User)
    # back_populates="diagrams" 表示这个关系与User模型中的'diagrams'属性是相互关联的
    # relationship(...) 是ORM的精髓，它在代码层面建立了 User 和 Diagram 之间的关联，让我们可以方便地通过 user.diagrams 来获取一个用户的所有图，或者通过 diagram.owner 获取图的作者。
    owner = relationship("User", back_populates="diagrams")
