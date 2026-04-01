"""
FastAPI应用入口
"""
from loguru import logger

from .api.routes import app
from .utils.config import get_config
from .utils.logger import setup_logger


def main():
    """主函数"""
    # 加载配置
    config = get_config()
    
    # 设置日志
    log_level = config.get("logging.level", "INFO")
    log_file = config.get("logging.file", "logs/app.log")
    setup_logger(log_level, log_file)
    
    logger.info("Multimodal Document Parser starting...")
    
    # 返回app供uvicorn使用
    return app


# 导出app
__all__ = ["app", "main"]
