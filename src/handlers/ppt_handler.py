"""
PPT处理器
通过LibreOffice将PPT转换为PDF，然后使用MinerU解析
"""
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Literal, Dict, Any
from loguru import logger

from .base import BaseHandler
from ..core.result import ParseResult
from ..utils.exceptions import ConversionError


class PPTHandler(BaseHandler):
    """PPT处理器 - 通过LibreOffice转PDF后用MinerU解析"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化PPT处理器
        
        Args:
            config: 配置字典
        """
        super().__init__(config)
        
        # LibreOffice配置
        libreoffice_config = config.get("libreoffice", {})
        self.libreoffice_path = libreoffice_config.get("path", self._get_default_libreoffice_path())
        self.timeout = libreoffice_config.get("timeout", 60)
        
        # 复用MinerU处理器
        from .mineru_handler import MinerUHandler
        self.mineru = MinerUHandler(config)
        
        logger.info(f"PPTHandler initialized, LibreOffice path: {self.libreoffice_path}")
    
    def _get_default_libreoffice_path(self) -> str:
        """获取默认的LibreOffice路径"""
        import platform
        system = platform.system()
        
        if system == "Darwin":  # macOS
            return "/Applications/LibreOffice.app/Contents/MacOS/soffice"
        elif system == "Linux":
            return "/usr/bin/libreoffice"
        elif system == "Windows":
            return "C:\\Program Files\\LibreOffice\\program\\soffice.exe"
        else:
            return "libreoffice"
    
    def parse(
        self,
        file_path: Path,
        mode: Literal["traditional", "vlm"] = "traditional"
    ) -> ParseResult:
        """
        解析PPT文档
        
        Args:
            file_path: 文件路径
            mode: 解析模式（traditional/vlm）
            
        Returns:
            ParseResult: 解析结果
        """
        logger.info(f"PPTHandler开始解析: {file_path}, 模式: {mode}")
        
        # 验证文件
        self._validate_file(file_path)
        
        # 1. 转换为PDF
        pdf_path = self._convert_to_pdf(file_path)
        
        try:
            # 2. 使用MinerU解析PDF
            result = self.mineru.parse(pdf_path, mode=mode)
            
            # 3. 更新元数据
            result.metadata["original_format"] = "ppt"
            result.metadata["conversion"] = "ppt→pdf"
            result.metadata["original_file"] = str(file_path)
            
            logger.info(f"PPTHandler解析完成: {file_path}")
            
            return result
        
        finally:
            # 4. 清理临时PDF
            if pdf_path.exists():
                pdf_path.unlink()
                logger.debug(f"清理临时PDF: {pdf_path}")
    
    def _convert_to_pdf(self, ppt_path: Path) -> Path:
        """
        使用LibreOffice将PPT转换为PDF
        
        Args:
            ppt_path: PPT文件路径
            
        Returns:
            PDF文件路径
            
        Raises:
            ConversionError: 转换失败
        """
        logger.info(f"开始转换PPT到PDF: {ppt_path}")
        
        # 创建临时目录
        temp_dir = tempfile.mkdtemp(prefix="ppt_convert_")
        output_dir = Path(temp_dir)
        
        try:
            # 构建LibreOffice命令
            cmd = [
                self.libreoffice_path,
                "--headless",
                "--convert-to", "pdf",
                "--outdir", str(output_dir),
                str(ppt_path)
            ]
            
            logger.debug(f"LibreOffice命令: {' '.join(cmd)}")
            
            # 执行转换
            start_time = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=self.timeout
            )
            elapsed_time = time.time() - start_time
            
            # 检查执行结果
            if result.returncode != 0:
                error_msg = result.stderr.decode('utf-8', errors='ignore')
                logger.error(f"LibreOffice转换失败: {error_msg}")
                raise ConversionError(
                    "ppt",
                    "pdf",
                    f"LibreOffice error: {error_msg}"
                )
            
            # 查找生成的PDF文件
            pdf_filename = f"{ppt_path.stem}.pdf"
            pdf_path = output_dir / pdf_filename
            
            if not pdf_path.exists():
                # 尝试查找任何PDF文件
                pdf_files = list(output_dir.glob("*.pdf"))
                if pdf_files:
                    pdf_path = pdf_files[0]
                else:
                    raise ConversionError(
                        "ppt",
                        "pdf",
                        "PDF file not generated"
                    )
            
            logger.info(f"PPT转换PDF完成，耗时: {elapsed_time:.2f}秒")
            
            return pdf_path
        
        except subprocess.TimeoutExpired:
            logger.error(f"LibreOffice转换超时（{self.timeout}秒）")
            raise ConversionError(
                "ppt",
                "pdf",
                f"Timeout after {self.timeout} seconds"
            )
        
        except FileNotFoundError:
            logger.error(f"LibreOffice未找到: {self.libreoffice_path}")
            raise ConversionError(
                "ppt",
                "pdf",
                f"LibreOffice not found at {self.libreoffice_path}"
            )
        
        except Exception as e:
            logger.error(f"PPT转换失败: {e}")
            raise ConversionError("ppt", "pdf", str(e))
    
    def check_libreoffice_available(self) -> bool:
        """
        检查LibreOffice是否可用
        
        Returns:
            是否可用
        """
        try:
            result = subprocess.run(
                [self.libreoffice_path, "--version"],
                capture_output=True,
                timeout=5
            )
            
            if result.returncode == 0:
                version = result.stdout.decode('utf-8', errors='ignore').strip()
                logger.info(f"LibreOffice可用: {version}")
                return True
            else:
                logger.warning("LibreOffice不可用")
                return False
        
        except Exception as e:
            logger.warning(f"检查LibreOffice失败: {e}")
            return False


__all__ = ["PPTHandler"]
