from sqlmodel import create_engine, Session
from app.core.config import settings

# 创建数据库引擎
# connect_args 是为了在SQLite中允许多线程访问，对于MySQL可以移除
engine = create_engine(
    settings.DATABASE_URL,
    echo=True,  # echo=True会打印所有执行的SQL语句，便于调试
    pool_pre_ping=True
)

def get_session():
    """
    FastAPI 依赖项，为每个请求提供一个数据库会话，
    并在请求结束后自动处理事务（提交或回滚）和关闭会话。
    """
    with Session(engine) as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
