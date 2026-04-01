"""
启动脚本
"""
import uvicorn
from src.utils.config import get_config
from src.utils.logger import setup_logger


def start_server():
    """启动API服务器"""
    # 加载配置
    config = get_config()
    
    # 设置日志
    log_level = config.get("logging.level", "INFO")
    log_file = config.get("logging.file", "logs/app.log")
    setup_logger(log_level, log_file)
    
    # 获取API配置
    host = config.get("api.host", "0.0.0.0")
    port = config.get("api.port", 8000)
    workers = config.get("api.workers", 1)
    
    print(f"""
    ╔═══════════════════════════════════════════╗
    ║  Multimodal Document Parser               ║
    ║  Version: 0.1.0                           ║
    ║  Server: http://{host}:{port}              ║
    ╚═══════════════════════════════════════════╝
    """)
    
    # 启动服务
    uvicorn.run(
        "src.api.routes:app",
        host=host,
        port=port,
        workers=workers,
        reload=False,
        log_level=log_level.lower()
    )


if __name__ == "__main__":
    start_server()
