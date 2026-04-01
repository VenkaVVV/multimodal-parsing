"""
快照生成模块
为文档生成页面快照图片
"""
from pathlib import Path
from typing import List, Dict, Any
from loguru import logger

from ..core.result import Snapshot


class SnapshotGenerator:
    """快照生成器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化快照生成器
        
        Args:
            config: 配置字典
        """
        self.enabled = config.get("enabled", True)
        self.dpi = config.get("dpi", 150)
        
        logger.info(f"SnapshotGenerator initialized, enabled={self.enabled}, dpi={self.dpi}")
    
    def generate(self, file_path: Path) -> List[Snapshot]:
        """
        生成文档快照
        
        Args:
            file_path: 文件路径
            
        Returns:
            快照列表
        """
        if not self.enabled:
            return []
        
        suffix = file_path.suffix.lower()
        
        # 只为PDF生成快照
        if suffix == ".pdf":
            return self._generate_pdf_snapshots(file_path)
        
        # 其他格式暂不支持
        logger.debug(f"快照生成不支持格式: {suffix}")
        return []
    
    def _generate_pdf_snapshots(self, file_path: Path) -> List[Snapshot]:
        """
        为PDF生成快照
        
        Args:
            file_path: PDF文件路径
            
        Returns:
            快照列表
        """
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(file_path)
            snapshots = []
            
            # 创建输出目录
            output_dir = Path("output/snapshots")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # 渲染页面为图片
                mat = fitz.Matrix(self.dpi / 72, self.dpi / 72)
                pix = page.get_pixmap(matrix=mat)
                
                # 保存图片
                snapshot_filename = f"{file_path.stem}_page_{page_num + 1}.png"
                snapshot_path = output_dir / snapshot_filename
                pix.save(str(snapshot_path))
                
                # 创建Snapshot对象
                snapshots.append(Snapshot(
                    page=page_num + 1,
                    path=str(snapshot_path),
                    width=pix.width,
                    height=pix.height
                ))
            
            doc.close()
            
            logger.info(f"PDF快照生成完成，共 {len(snapshots)} 页")
            return snapshots
        
        except ImportError:
            logger.warning("PyMuPDF not available, cannot generate snapshots")
            return []
        
        except Exception as e:
            logger.error(f"快照生成失败: {e}")
            return []


__all__ = ["SnapshotGenerator"]
