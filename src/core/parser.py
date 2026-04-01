"""
主解析器
统一文档解析入口，根据文件格式选择对应的处理器
"""
import time
from pathlib import Path
from typing import Union, Literal, Optional
from loguru import logger

from .result import ParseResult, ParseResponse
from ..utils.config import get_config
from ..utils.exceptions import (
    FileNotFoundError,
    FileTooLargeError,
    UnsupportedFormatError,
    HandlerNotFoundError
)


class DocumentParser:
    """统一文档解析器"""
    
    def __init__(self, config: Optional[dict] = None):
        """
        初始化解析器
        
        Args:
            config: 配置字典，如果为None则使用全局配置
        """
        if config is None:
            config = get_config().to_dict()
        
        self.config = config
        self.max_file_size = config.get("parser", {}).get("max_file_size", 100 * 1024 * 1024)
        self.supported_formats = config.get("parser", {}).get("supported_formats", [])
        
        # 初始化处理器（延迟加载）
        self._handlers = {}
        
        logger.info(f"DocumentParser initialized, supported formats: {self.supported_formats}")
    
    def parse(
        self,
        file_path: Union[str, Path],
        mode: Literal["traditional", "vlm", "smart"] = "traditional",
        enable_chunking: bool = False,
        enable_snapshot: bool = True
    ) -> ParseResult:
        """
        解析文档
        
        Args:
            file_path: 文件路径
            mode: 解析模式（traditional/vlm/smart）
            enable_chunking: 是否启用语义分片
            enable_snapshot: 是否生成快照
            
        Returns:
            ParseResult: 解析结果
            
        Raises:
            FileNotFoundError: 文件不存在
            FileTooLargeError: 文件过大
            UnsupportedFormatError: 不支持的格式
        """
        start_time = time.time()
        file_path = Path(file_path)
        
        logger.info(f"开始解析文档: {file_path}, 模式: {mode}")
        
        try:
            # 1. 验证文件
            self._validate_file(file_path)
            
            # 2. 获取处理器
            handler = self._get_handler(file_path, mode=mode)
            
            # 3. 执行解析
            result = handler.parse(file_path, mode=mode)
            
            # 4. 后处理
            if enable_chunking:
                result = self._chunk_result(result)
            
            if enable_snapshot:
                result = self._generate_snapshots(result, file_path)
            
            # 5. 记录处理时间
            result.processing_time = time.time() - start_time
            
            logger.info(f"文档解析完成: {file_path}, 耗时: {result.processing_time:.2f}秒")
            
            return result
        
        except Exception as e:
            logger.error(f"文档解析失败: {file_path}, 错误: {e}")
            raise
    
    def _validate_file(self, file_path: Path):
        """
        验证文件
        
        Args:
            file_path: 文件路径
            
        Raises:
            FileNotFoundError: 文件不存在
            FileTooLargeError: 文件过大
            UnsupportedFormatError: 不支持的格式
        """
        # 检查文件是否存在
        if not file_path.exists():
            raise FileNotFoundError(str(file_path))
        
        # 检查文件大小
        file_size = file_path.stat().st_size
        if file_size > self.max_file_size:
            raise FileTooLargeError(
                str(file_path),
                file_size,
                self.max_file_size
            )
        
        # 检查文件格式
        suffix = file_path.suffix.lower().lstrip(".")
        if suffix not in self.supported_formats:
            raise UnsupportedFormatError(suffix)
    
    def _get_handler(self, file_path: Path, mode: str = "traditional"):
        """
        根据文件格式获取处理器
        
        Args:
            file_path: 文件路径
            mode: 解析模式
            
        Returns:
            处理器实例
        """
        suffix = file_path.suffix.lower()
        
        # 如果是智能模式，使用SmartDocumentHandler
        if mode == "smart":
            return self._get_smart_document_handler()
        
        # MinerU支持的格式
        if suffix in [".pdf", ".docx", ".doc", ".png", ".jpg", ".jpeg", ".bmp"]:
            return self._get_mineru_handler()
        
        # PPT格式
        elif suffix in [".ppt", ".pptx"]:
            return self._get_ppt_handler()
        
        # Excel格式
        elif suffix in [".xls", ".xlsx"]:
            return self._get_excel_handler()
        
        else:
            raise HandlerNotFoundError(suffix)
    
    def _get_mineru_handler(self):
        """获取MinerU处理器（延迟加载）"""
        if "mineru" not in self._handlers:
            from ..handlers.mineru_handler import MinerUHandler
            self._handlers["mineru"] = MinerUHandler(self.config)
        return self._handlers["mineru"]
    
    def _get_ppt_handler(self):
        """获取PPT处理器（延迟加载）"""
        if "ppt" not in self._handlers:
            from ..handlers.ppt_handler import PPTHandler
            self._handlers["ppt"] = PPTHandler(self.config)
        return self._handlers["ppt"]
    
    def _get_excel_handler(self):
        """获取Excel处理器（延迟加载）"""
        if "excel" not in self._handlers:
            from ..handlers.excel_handler import ExcelHandler
            self._handlers["excel"] = ExcelHandler(self.config)
        return self._handlers["excel"]
    
    def _get_smart_document_handler(self):
        """获取智能文档处理器（延迟加载）"""
        if "smart_document" not in self._handlers:
            from ..handlers.smart_document_handler import SmartDocumentHandler
            self._handlers["smart_document"] = SmartDocumentHandler(self.config)
        return self._handlers["smart_document"]
    
    def _chunk_result(self, result: ParseResult) -> ParseResult:
        """
        对解析结果进行语义分片
        
        Args:
            result: 解析结果
            
        Returns:
            更新后的解析结果
        """
        try:
            from ..postprocess.chunker import Chunker
            
            chunker = Chunker(self.config.get("chunking", {}))
            result.chunks = chunker.chunk(result.markdown)
            
            logger.info(f"语义分片完成，共 {len(result.chunks)} 个分片")
            
        except Exception as e:
            logger.warning(f"语义分片失败: {e}")
        
        return result
    
    def _generate_snapshots(self, result: ParseResult, file_path: Path) -> ParseResult:
        """
        生成文档快照
        
        Args:
            result: 解析结果
            file_path: 文件路径
            
        Returns:
            更新后的解析结果
        """
        try:
            from ..postprocess.snapshot import SnapshotGenerator
            
            snapshot_gen = SnapshotGenerator(self.config.get("snapshot", {}))
            result.snapshots = snapshot_gen.generate(file_path)
            
            logger.info(f"快照生成完成，共 {len(result.snapshots)} 页")
            
        except Exception as e:
            logger.warning(f"快照生成失败: {e}")
        
        return result
    
    def parse_to_response(
        self,
        file_path: Union[str, Path],
        mode: Literal["traditional", "vlm"] = "traditional",
        enable_chunking: bool = False,
        enable_snapshot: bool = True
    ) -> ParseResponse:
        """
        解析文档并返回响应（包含错误处理）
        
        Args:
            file_path: 文件路径
            mode: 解析模式
            enable_chunking: 是否启用语义分片
            enable_snapshot: 是否生成快照
            
        Returns:
            ParseResponse: 解析响应
        """
        try:
            result = self.parse(
                file_path,
                mode=mode,
                enable_chunking=enable_chunking,
                enable_snapshot=enable_snapshot
            )
            return ParseResponse.from_result(result)
        
        except FileNotFoundError as e:
            return ParseResponse.from_error(
                "FileNotFoundError",
                str(e),
                {"file_path": str(file_path)}
            )
        
        except FileTooLargeError as e:
            return ParseResponse.from_error(
                "FileTooLargeError",
                str(e),
                {"file_path": str(file_path)}
            )
        
        except UnsupportedFormatError as e:
            return ParseResponse.from_error(
                "UnsupportedFormatError",
                str(e),
                {"file_path": str(file_path)}
            )
        
        except Exception as e:
            logger.exception(f"解析文档时发生未知错误: {e}")
            return ParseResponse.from_error(
                "UnknownError",
                str(e),
                {"file_path": str(file_path)}
            )


__all__ = ["DocumentParser"]
