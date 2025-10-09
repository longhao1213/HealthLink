# 配置日志
import logging

import uvicorn
from fastapi import FastAPI
from fastapi_pagination import add_pagination
from starlette.middleware.cors import CORSMiddleware

from app.api import admin_user_api,knowledge_file_api,chat_app_api,chat_web_api
from app.core.exceptions import ApiException, api_exception_handler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="health link",
    description="瑶光AI医生智能体",
    version="0.1.0"
)

# 注册统一异常类
app.add_exception_handler(ApiException,api_exception_handler)
# 添加分页
add_pagination(app)
# 开启跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(admin_user_api.router)
app.include_router(knowledge_file_api.router)
app.include_router(chat_app_api.router)
app.include_router(chat_web_api.router)
@app.get("/")
async def root():
    return {
        "message": "欢迎使用瑶光AI医生智能体中心API",
        "version": "1.0.0",
        "available_agents": ["chat"]
    }

# 启动服务器
if __name__ == "__main__":
    logger.info(f"项目启动成功，请访问 http://127.0.0.1:28520")
    logger.info(f"接口文档地址 http://127.0.0.1:28520/docs")
    uvicorn.run(app,port=28520)