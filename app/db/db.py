from sqlmodel import create_engine,Session
from app.core.config import settings
from app.core.exceptions import ApiException

# 创建引擎
engine = create_engine(settings.DATABASE_URL)

# 创建一个实现自动管理事务的依赖函数
def get_session():
    """
    fastApi依赖项，用户获取数据库回话，需要在使用的地方通过Depends注入
    实现自动提交或者回滚事务
    :return:
    """
    with Session(engine) as session:
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise ApiException(msg=f"数据库操作异常：{str(e)}")