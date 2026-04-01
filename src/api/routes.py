"""
API路由
定义所有API端点
"""
import time
import uuid
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, Query, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from .schemas import (
    HealthResponse,
    ParseResponse,
    ImageResponse,
    ChunkResponse,
    SnapshotResponse
)
from ..core.parser import DocumentParser
from ..utils.config import get_config
from ..utils.file_utils import save_upload_file, ensure_dir


# 创建FastAPI应用
app = FastAPI(
    title="Multimodal Document Parser",
    description="多格式文档解析服务，支持PDF、Word、Excel、PPT、图片等格式",
    version="0.1.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化解析器
config = get_config()
logger.info(f"API初始化 - Config parser: {config.get('parser')}")
parser = DocumentParser(config.to_dict())
logger.info(f"API初始化 - Parser supported_formats: {parser.supported_formats}")

# 创建上传目录
upload_dir = ensure_dir("uploads")


@app.get("/", response_class=JSONResponse)
async def root():
    """根路径"""
    return {
        "name": "Multimodal Document Parser",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    健康检查
    
    Returns:
        HealthResponse: 健康状态
    """
    return HealthResponse(
        status="healthy",
        version="0.1.0"
    )


@app.post("/api/v1/parse", response_model=ParseResponse)
async def parse_document(
    file: UploadFile = File(..., description="上传的文档文件"),
    mode: str = Form("traditional", description="解析模式"),
    enable_chunking: bool = Form(False, description="是否启用语义分片"),
    enable_snapshot: bool = Form(True, description="是否生成快照")
):
    """
    解析文档
    
    - **file**: 上传的文档文件（支持pdf/docx/ppt/xlsx/图片）
    - **mode**: 解析模式
        - traditional: 传统模式（快速稳定）
        - vlm: VLM大模型模式（理解力强）
        - smart: 智能文档模式（完整版面分析+类型识别）⭐
    - **enable_chunking**: 是否启用语义分片
    - **enable_snapshot**: 是否生成文档快照
    
    Returns:
        ParseResponse: 解析结果
    """
    start_time = time.time()
    
    logger.info(f"收到解析请求: {file.filename}, 模式: {mode}")
    
    try:
        # 1. 保存上传文件
        file_content = await file.read()
        file_path = save_upload_file(file_content, file.filename, upload_dir)
        
        logger.info(f"文件已保存: {file_path}")
        
        # 2. 解析文档
        result = parser.parse(
            file_path,
            mode=mode,
            enable_chunking=enable_chunking,
            enable_snapshot=enable_snapshot
        )
        
        # 3. 构建响应
        processing_time = time.time() - start_time
        
        # 转换图片
        images = [
            ImageResponse(
                path=img.path,
                page=img.page,
                bbox=img.bbox
            )
            for img in result.images
        ]
        
        # 转换分片
        chunks = None
        if result.chunks:
            chunks = [
                ChunkResponse(
                    id=chunk.id,
                    content=chunk.content,
                    tokens=chunk.tokens
                )
                for chunk in result.chunks
            ]
        
        # 转换快照
        snapshots = None
        if result.snapshots:
            snapshots = [
                SnapshotResponse(
                    page=snap.page,
                    path=snap.path,
                    width=snap.width,
                    height=snap.height
                )
                for snap in result.snapshots
            ]
        
        logger.info(f"解析完成: {file.filename}, 耗时: {processing_time:.2f}秒")
        
        return ParseResponse(
            success=True,
            markdown=result.markdown,
            json_data=result.json_data,
            images=images,
            chunks=chunks,
            snapshots=snapshots,
            metadata=result.metadata,
            processing_time=processing_time
        )
    
    except Exception as e:
        logger.error(f"解析失败: {e}")
        processing_time = time.time() - start_time
        
        return ParseResponse(
            success=False,
            error=str(e),
            processing_time=processing_time
        )


@app.post("/api/v1/parse/async")
async def parse_async(
    file: UploadFile = File(...),
    mode: str = Query("traditional", regex="^(traditional|vlm)$"),
    enable_chunking: bool = Query(False),
    enable_snapshot: bool = Query(True),
    background_tasks: BackgroundTasks = None
):
    """
    异步解析文档（适合大文件）
    
    Returns:
        任务ID和状态
    """
    task_id = str(uuid.uuid4())
    
    # TODO: 实现异步任务队列
    # 这里可以集成Redis或Celery
    
    return {
        "task_id": task_id,
        "status": "pending",
        "message": "异步解析功能待实现"
    }


@app.get("/api/v1/tasks/{task_id}")
async def get_task_status(task_id: str):
    """
    查询任务状态
    
    Args:
        task_id: 任务ID
        
    Returns:
        任务状态
    """
    # TODO: 实现任务状态查询
    
    return {
        "task_id": task_id,
        "status": "not_found",
        "message": "任务查询功能待实现"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理"""
    logger.error(f"全局异常: {exc}")
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": str(exc),
            "message": "服务器内部错误"
        }
    )


__all__ = ["app"]
