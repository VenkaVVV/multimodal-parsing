"""
处理器基类
定义所有处理器的通用接口
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Literal, Dict, Any
from loguru import logger

from ..core.result import ParseResult


class BaseHandler(ABC):
    """处理器基类"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化处理器
        
        Args:
            config: 配置字典
        """
        self.config = config
        logger.info(f"{self.__class__.__name__} initialized")
    
    @abstractmethod
    def parse(
        self,
        file_path: Path,
        mode: Literal["traditional", "vlm"] = "traditional"
    ) -> ParseResult:
        """
        解析文档（抽象方法，子类必须实现）
        
        Args:
            file_path: 文件路径
            mode: 解析模式（traditional/vlm）
            
        Returns:
            ParseResult: 解析结果
        """
        pass
    
    def _get_metadata(self, file_path: Path, **kwargs) -> Dict[str, Any]:
        """
        获取基础元数据
        
        Args:
            file_path: 文件路径
            **kwargs: 额外的元数据
            
        Returns:
            元数据字典
        """
        metadata = {
            "source": str(file_path),
            "filename": file_path.name,
            "format": file_path.suffix.lower().lstrip("."),
            "handler": self.__class__.__name__,
        }
        metadata.update(kwargs)
        return metadata
    
    def _validate_file(self, file_path: Path):
        """
        验证文件是否存在
        
        Args:
            file_path: 文件路径
            
        Raises:
            FileNotFoundError: 文件不存在
        """
        if not file_path.exists():
            from ..utils.exceptions import FileNotFoundError as CustomFileNotFoundError
            raise CustomFileNotFoundError(str(file_path))


__all__ = ["BaseHandler"]
