# 这个文件将专门负责所有与数据库连接相关的配置。
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. 数据库连接URL
# 格式: "mysql+mysqlconnector://<user>:<password>@<host>[:<port>]/<database>"
# !! 重要: 请将下面的用户名、密码、主机和数据库名替换为你自己的信息 !!
# 请务必将 SQLALCHEMY_DATABASE_URL 中的 root、your_password、localhost 替换成你自己的MySQL用户名、密码和主机地址。
SQLALCHEMY_DATABASE_URL = "mysql+mysqlconnector://root:root1234@localhost/online_diagram_db"


# 2. 创建SQLAlchemy引擎 (Engine)
# 'engine'是SQLAlchemy与数据库沟通的核心接口
engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)

# 3. 创建数据库会话 (Session)
# SessionLocal类将作为我们与数据库进行增删改查操作的会话实例
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. 创建模型基类 (Base)
# 我们之后创建的所有ORM模型(数据表对应的类)都需要继承这个Base类
Base = declarative_base()

