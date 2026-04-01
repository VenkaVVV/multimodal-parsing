"""
智能型VLM模式处理器
根据版面分析结果，对不同类型内容使用不同解析策略
"""
from pathlib import Path
from typing import Dict, Any, List, Optional
from loguru import logger
import json
import subprocess
import os

from .base import BaseHandler
from ..core.result import ParseResult, Image


class SmartDocumentHandler(BaseHandler):
    """智能型VLM模式处理器 - 智能选择解析策略"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # 从环境变量或配置文件读取VLM配置
        self.vlm_api_key = os.getenv('VLM_API_KEY')
        self.vlm_model = os.getenv('VLM_MODEL', 'qwen3.5-397b-a17b')
        self.vlm_base_url = os.getenv('VLM_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
        
        # 如果环境变量没有，尝试从配置文件读取
        if not self.vlm_api_key:
            try:
                env_file = Path('.env')
                if env_file.exists():
                    with open(env_file, 'r') as f:
                        for line in f:
                            if line.startswith('VLM_API_KEY='):
                                self.vlm_api_key = line.strip().split('=', 1)[1]
                                break
            except Exception as e:
                logger.warning(f"读取配置文件失败: {e}")
        
        # 如果还是没有，使用默认值（仅用于开发测试）
        if not self.vlm_api_key:
            self.vlm_api_key = 'sk-c9f6dc06a96b4ca9aba27f169a0fa641'
            logger.warning("未配置VLM_API_KEY，使用默认值（仅用于开发测试）")
        
        logger.info(f"SmartDocumentHandler initialized with VLM: {self.vlm_model}")
    
    def parse(self, file_path: Path, mode: str = "smart") -> ParseResult:
        """
        智能解析文档
        
        流程：
        1. MinerU版面分析（检测区域类型）
        2. 根据区域类型选择处理策略
        3. 整合结果输出
        
        Args:
            file_path: 文件路径
            mode: 解析模式
            
        Returns:
            ParseResult: 解析结果
        """
        logger.info(f"SmartDocument开始解析: {file_path}")
        
        self._validate_file(file_path)
        
        try:
            # 1. 使用MinerU进行版面分析和基础解析
            mineru_result = self._parse_with_mineru(file_path)
            
            # 2. 读取版面分析结果
            model_data = mineru_result.get('model_data', [])
            markdown_content = mineru_result['markdown']
            output_dir = mineru_result['output_dir']
            
            # 3. 根据版面类型进行增强处理
            enhanced_markdown, stats = self._enhance_by_region_type(
                markdown_content,
                model_data,
                output_dir
            )
            
            logger.info(f"SmartDocument解析完成: {file_path}")
            logger.info(f"处理统计: OCR区域={stats['ocr_count']}, VLM区域={stats['vlm_count']}")
            
            return ParseResult(
                markdown=enhanced_markdown,
                images=mineru_result.get('images', []),
                json_data={"pages": model_data, "stats": stats} if isinstance(model_data, list) else model_data,
                metadata=self._get_metadata(
                    file_path,
                    parser="SmartDocument",
                    mode=mode,
                    mineru_output=str(output_dir),
                    regions_count=stats['total_count'],
                    vlm_regions=stats['vlm_count'],
                    ocr_regions=stats['ocr_count']
                )
            )
        
        except Exception as e:
            logger.error(f"SmartDocument解析失败: {e}")
            raise
    
    def _parse_with_mineru(self, file_path: Path) -> Dict[str, Any]:
        """使用MinerU进行版面分析和基础解析"""
        output_dir = Path("output/mineru_temp")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置环境变量（禁用网络请求）
        env = os.environ.copy()
        env['YOLO_AUTODOWNLOAD'] = '0'
        env['ULTRALYTICS_HUB_API_KEY'] = ''
        
        # 构建命令（使用venv中的magic-pdf）
        venv_path = Path(__file__).parent.parent.parent / "venv" / "bin" / "magic-pdf"
        if venv_path.exists():
            magic_pdf_cmd = str(venv_path)
        else:
            magic_pdf_cmd = "magic-pdf"  # fallback to system command
        
        cmd = [
            magic_pdf_cmd,
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
        
        # 读取模型JSON（包含版面检测结果）
        model_json = result_dir / f"{pdf_name}_model.json"
        if model_json.exists():
            with open(model_json, 'r', encoding='utf-8') as f:
                model_data = json.load(f)
        else:
            model_data = []
            logger.warning(f"模型JSON不存在: {model_json}")
        
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
        
        return {
            'markdown': markdown,
            'model_data': model_data,
            'images': images,
            'output_dir': result_dir
        }
    
    def _enhance_by_region_type(
        self,
        markdown: str,
        model_data: List,
        output_dir: Path
    ) -> tuple[str, Dict]:
        """
        根据区域类型增强处理
        
        区域类型：
        - 1: text（文本） → OCR（已完成）
        - 3: title（标题） → OCR（已完成）
        - 5: figure（图片） → VLM生成描述
        - 7: table（表格） → StructTable（已完成）
        - 9: formula（公式） → UniMERNet（已完成）
        - 15: caption（说明） → OCR（已完成）
        """
        import re
        
        stats = {
            'total_count': 0,
            'ocr_count': 0,
            'vlm_count': 0,
            'table_count': 0,
            'formula_count': 0
        }
        
        if not isinstance(model_data, list):
            return markdown, stats
        
        # 统计各类型区域数量
        for page_data in model_data:
            if not isinstance(page_data, dict):
                continue
            
            layout_dets = page_data.get('layout_dets', [])
            for item in layout_dets:
                category_id = item.get('category_id', 0)
                stats['total_count'] += 1
                
                if category_id in [1, 3, 15]:  # text, title, caption
                    stats['ocr_count'] += 1
                elif category_id == 5:  # figure
                    stats['vlm_count'] += 1
                elif category_id == 7:  # table
                    stats['table_count'] += 1
                elif category_id == 9:  # formula
                    stats['formula_count'] += 1
        
        # 查找所有图片引用
        image_pattern = r'!\[.*?\]\((.*?)\)'
        images = re.findall(image_pattern, markdown)
        
        if not images:
            logger.info("未检测到图片，无需VLM处理")
            return markdown, stats
        
        logger.info(f"检测到 {len(images)} 张图片，使用VLM生成描述...")
        
        enhanced_markdown = markdown
        
        # 对每张图片使用VLM生成描述
        for img_path in images:
            # 获取完整图片路径
            full_img_path = output_dir / img_path
            
            if not full_img_path.exists():
                logger.warning(f"图片不存在: {full_img_path}")
                continue
            
            # 使用VLM生成图片描述
            description = self._describe_image_with_vlm(full_img_path)
            
            if description:
                # 在图片后添加VLM生成的描述
                enhanced_markdown = enhanced_markdown.replace(
                    f"]({img_path})",
                    f"]({img_path})\n\n{description}"
                )
                logger.info(f"已为图片添加VLM描述: {img_path}")
        
        return enhanced_markdown, stats
    
    def _describe_image_with_vlm(self, img_path: Path) -> Optional[str]:
        """
        使用VLM描述图片内容
        
        Args:
            img_path: 图片路径
            
        Returns:
            图片描述
        """
        if not self.vlm_api_key or not img_path.exists():
            return None
        
        try:
            import openai
            import base64
            
            # 读取图片
            with open(img_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode()
            
            # 调用VLM
            client = openai.OpenAI(
                api_key=self.vlm_api_key,
                base_url=self.vlm_base_url
            )
            
            response = client.chat.completions.create(
                model=self.vlm_model,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """请详细描述这张图片的内容。

要求：
1. 如果是图表（柱状图、折线图、饼图等），请说明：
   - 图表类型
   - 数据内容
   - 趋势分析

2. 如果是示意图或流程图，请说明：
   - 图示内容
   - 关键要素
   - 逻辑关系

3. 如果是照片，请说明：
   - 图片主体
   - 场景描述
   - 重要细节

请用简洁清晰的语言描述，便于理解。"""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        }
                    ]
                }],
                max_tokens=1000
            )
            
            description = response.choices[0].message.content
            logger.info(f"VLM成功生成图片描述")
            return description
        
        except Exception as e:
            logger.error(f"VLM描述图片失败: {e}")
            return None


__all__ = ["SmartDocumentHandler"]
