| 操作系统 (OS)       | 进入命令 (Activation Command)     | 退出命令 (Deactivation Command) |
|--------------------|----------------------------------|--------------------------------|
| macOS / Linux      | `source venv/bin/activate`       | `deactivate`                   |
| Windows            | `.\venv\Scripts\activate`        | `deactivate`                   |

### 项目初始化与运行步骤
git clone https://github.com/lamvyc/online-diagram-app.git

cd online-diagram-app

python3 -m venv venv

source venv/bin/activate (或 Windows 的 .\venv\Scripts\activate)

pip install -r requirements.txt (这一步现在会正确安装所有依赖)

创建 MySQL 数据库并配置 database.py。

uvicorn app.main:app --reload



<!-- 每次提交代码前，请重新生成 requirements.txt 以确保依赖版本一致： -->
pip freeze > requirements.txt


### 数据库初始化
mysql -u root -p
密码：root1234

<!-- 成功登录后，你需要告诉 MySQL 你要操作哪个数据库。 -->
USE online_diagram_db;
<!-- 查看有哪些用户 -->
SELECT * FROM users;
