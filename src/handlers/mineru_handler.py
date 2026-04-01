"""
MinerU处理器
使用MinerU命令行工具进行文档解析
"""
from pathlib import Path
from typing import Literal, Dict, Any, List
from loguru import logger
import subprocess
import os
import json

from .base import BaseHandler
from ..core.result import ParseResult, Image


class MinerUHandler(BaseHandler):
    """MinerU处理器 - 使用MinerU命令行工具"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        logger.info("MinerUHandler initialized")
    
    def parse(
        self,
        file_path: Path,
        mode: Literal["traditional", "vlm"] = "traditional"
    ) -> ParseResult:
        """
        使用MinerU解析文档
        
        Args:
            file_path: 文件路径
            mode: 解析模式
            
        Returns:
            ParseResult: 解析结果
        """
        logger.info(f"MinerU开始解析: {file_path}")
        
        self._validate_file(file_path)
        
        try:
            # 使用MinerU命令行工具
            result = self._run_mineru_cli(file_path)
            
            logger.info(f"MinerU解析完成: {file_path}")
            
            return result
        
        except Exception as e:
            logger.error(f"MinerU解析失败: {e}，使用PyMuPDF降级处理")
            return self._fallback_parse(file_path, mode)
    
    def _run_mineru_cli(self, file_path: Path) -> ParseResult:
        """使用MinerU命令行工具解析"""
        output_dir = Path("output/mineru")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置环境变量（禁用网络请求）
        env = os.environ.copy()
        env['YOLO_AUTODOWNLOAD'] = '0'
        env['ULTRALYTICS_HUB_API_KEY'] = ''
        
        # 构建命令
        cmd = [
            'magic-pdf',
            '-p', str(file_path),
            '-o', str(output_dir),
            '-m', 'ocr'
        ]
        
        logger.info(f"执行MinerU: {' '.join(cmd)}")
        
        # 执行MinerU
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode != 0:
            logger.error(f"MinerU执行失败: {result.stderr}")
            raise Exception(f"MinerU failed: {result.stderr}")
        
        # 读取输出文件
        pdf_name = file_path.stem
        result_dir = output_dir / pdf_name / "ocr"
        
        # 读取Markdown
        md_file = result_dir / f"{pdf_name}.md"
        if md_file.exists():
            with open(md_file, 'r', encoding='utf-8') as f:
                markdown = f.read()
        else:
            markdown = ""
            logger.warning(f"Markdown文件不存在: {md_file}")
        
        # 读取JSON数据
        model_json = result_dir / f"{pdf_name}_model.json"
        if model_json.exists():
            with open(model_json, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
        else:
            json_data = {}
        
        # 收集图片
        images = []
        images_dir = result_dir / "images"
        if images_dir.exists():
            for img_file in images_dir.glob("*.jpg"):
                images.append(Image(
                    path=str(img_file),
                    page=1,
                    bbox=[]
                ))
        
        return ParseResult(
            markdown=markdown,
            json_data=json_data,
            images=images,
            metadata=self._get_metadata(
                file_path,
                parser="MinerU",
                mode="ocr"
            )
        )
    
    def _fallback_parse(
        self,
        file_path: Path,
        mode: str
    ) -> ParseResult:
        """降级处理：使用PyMuPDF"""
        logger.info(f"使用PyMuPDF降级处理: {file_path}")
        
        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise ImportError("PyMuPDF not installed")
        
        # 打开PDF
        doc = fitz.open(str(file_path))
        
        markdown_parts = []
        images = []
        
        # 逐页处理
        for page_num, page in enumerate(doc):
            # 提取文本
            text = page.get_text()
            if text.strip():
                markdown_parts.append(f"## Page {page_num + 1}\n\n{text}")
            
            # 提取图片
            image_list = page.get_images()
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                
                # 保存图片
                image_path = f"output/images/page{page_num}_img{img_index}.png"
                os.makedirs(os.path.dirname(image_path), exist_ok=True)
                with open(image_path, "wb") as f:
                    f.write(image_bytes)
                
                images.append(Image(
                    path=image_path,
                    page=page_num + 1,
                    bbox=[]
                ))
                
                # 添加图片引用
                markdown_parts.append(f"\n![图片](../{image_path})\n")
        
        doc.close()
        
        markdown = "\n".join(markdown_parts)
        
        return ParseResult(
            markdown=markdown,
            images=images,
            metadata=self._get_metadata(
                file_path,
                parser="PyMuPDF",
                mode=mode,
                fallback=True
            )
        )


__all__ = ["MinerUHandler"]
