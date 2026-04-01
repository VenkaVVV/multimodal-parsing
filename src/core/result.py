"""
解析结果模型
定义文档解析的结果数据结构
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class Image(BaseModel):
    """图片信息"""
    path: str = Field(..., description="图片路径")
    page: int = Field(..., description="所在页码")
    bbox: List[float] = Field(default_factory=list, description="边界框 [x1, y1, x2, y2]")
    description: Optional[str] = Field(None, description="图片描述")


class Chunk(BaseModel):
    """语义分片"""
    id: int = Field(..., description="分片ID")
    content: str = Field(..., description="分片内容")
    tokens: int = Field(default=0, description="token数量")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class Snapshot(BaseModel):
    """文档快照"""
    page: int = Field(..., description="页码")
    path: str = Field(..., description="快照图片路径")
    width: Optional[int] = Field(None, description="宽度")
    height: Optional[int] = Field(None, description="高度")


class ParseResult(BaseModel):
    """解析结果"""
    
    # 核心内容
    markdown: str = Field(..., description="Markdown内容")
    json_data: Optional[Dict[str, Any]] = Field(None, description="JSON结构化数据")
    
    # 提取的资源
    images: List[Image] = Field(default_factory=list, description="提取的图片")
    
    # 后处理结果
    chunks: Optional[List[Chunk]] = Field(None, description="语义分片")
    snapshots: Optional[List[Snapshot]] = Field(None, description="文档快照")
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    
    # 统计信息
    processing_time: float = Field(default=0.0, description="处理时间（秒）")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.model_dump()
    
    def get_summary(self) -> Dict[str, Any]:
        """获取摘要信息"""
        return {
            "markdown_length": len(self.markdown),
            "images_count": len(self.images),
            "chunks_count": len(self.chunks) if self.chunks else 0,
            "snapshots_count": len(self.snapshots) if self.snapshots else 0,
            "processing_time": self.processing_time,
            "metadata": self.metadata
        }


class ParseError(BaseModel):
    """解析错误"""
    error_type: str = Field(..., description="错误类型")
    error_message: str = Field(..., description="错误消息")
    error_details: Optional[Dict[str, Any]] = Field(None, description="错误详情")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


class ParseResponse(BaseModel):
    """解析响应"""
    success: bool = Field(..., description="是否成功")
    result: Optional[ParseResult] = Field(None, description="解析结果")
    error: Optional[ParseError] = Field(None, description="错误信息")
    
    @classmethod
    def from_result(cls, result: ParseResult) -> "ParseResponse":
        """从解析结果创建响应"""
        return cls(success=True, result=result)
    
    @classmethod
    def from_error(
        cls,
        error_type: str,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None
    ) -> "ParseResponse":
        """从错误创建响应"""
        return cls(
            success=False,
            error=ParseError(
                error_type=error_type,
                error_message=error_message,
                error_details=error_details
            )
        )


__all__ = [
    "Image",
    "Chunk",
    "Snapshot",
    "ParseResult",
    "ParseError",
    "ParseResponse",
]
