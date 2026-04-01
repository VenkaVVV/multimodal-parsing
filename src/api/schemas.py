"""
Pydantic模型定义
定义API请求和响应的数据模型
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="服务状态")
    version: str = Field(..., description="版本号")


class ParseRequest(BaseModel):
    """解析请求"""
    mode: str = Field(default="traditional", description="解析模式")
    enable_chunking: bool = Field(default=False, description="是否启用分片")
    enable_snapshot: bool = Field(default=True, description="是否生成快照")


class ImageResponse(BaseModel):
    """图片响应"""
    path: str
    page: int
    bbox: List[float] = []


class ChunkResponse(BaseModel):
    """分片响应"""
    id: int
    content: str
    tokens: int


class SnapshotResponse(BaseModel):
    """快照响应"""
    page: int
    path: str
    width: Optional[int] = None
    height: Optional[int] = None


class ParseResponse(BaseModel):
    """解析响应"""
    success: bool = Field(..., description="是否成功")
    markdown: Optional[str] = Field(None, description="Markdown内容")
    json_data: Optional[Dict[str, Any]] = Field(None, description="JSON数据")
    images: List[ImageResponse] = Field(default_factory=list, description="图片列表")
    chunks: Optional[List[ChunkResponse]] = Field(None, description="分片列表")
    snapshots: Optional[List[SnapshotResponse]] = Field(None, description="快照列表")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    processing_time: float = Field(default=0.0, description="处理时间")
    error: Optional[str] = Field(None, description="错误信息")


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str
    status: str
    progress: float = 0.0
    result: Optional[ParseResponse] = None
    created_at: datetime
    updated_at: datetime


__all__ = [
    "HealthResponse",
    "ParseRequest",
    "ParseResponse",
    "ImageResponse",
    "ChunkResponse",
    "SnapshotResponse",
    "TaskStatusResponse",
]
