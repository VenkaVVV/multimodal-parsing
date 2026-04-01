"""
智能文档解析处理器
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
    """智能文档解析处理器 - 根据内容类型选择最优解析策略"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # 从环境变量或配置文件读取VLM配置
        # 优先级：环境变量 > 配置文件 > 默认值
        self.vlm_api_key = os.getenv('VLM_API_KEY')
        self.vlm_model = os.getenv('VLM_MODEL', 'qwen3.5-397b-a17b')
        self.vlm_base_url = os.getenv('VLM_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
        
        # 如果环境变量没有，尝试从配置文件读取
        if not self.vlm_api_key:
            try:
                from pathlib import Path
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
            self.vlm_api_key = 'sk-xxxx'
            logger.warning("未配置VLM_API_KEY，使用默认值（仅用于开发测试）")
        
        logger.info(f"SmartDocumentHandler initialized with VLM: {self.vlm_model}")
    
    def parse(self, file_path: Path, mode: str = "smart") -> ParseResult:
        """
        智能解析文档
        
        Args:
            file_path: 文件路径
            mode: 解析模式
            
        Returns:
            ParseResult: 解析结果
        """
        logger.info(f"SmartDocument开始解析: {file_path}")
        
        self._validate_file(file_path)
        
        try:
            # 使用MinerU进行完整解析
            mineru_result = self._parse_with_mineru(file_path)
            
            # 读取MinerU的model.json，获取详细的版面信息
            model_data = mineru_result.get('model_data', {})
            
            # 处理图片中的表格
            enhanced_markdown = self._process_table_images(
                mineru_result['markdown'],
                model_data,
                mineru_result['output_dir']
            )
            
            logger.info(f"SmartDocument解析完成: {file_path}")
            
            return ParseResult(
                markdown=enhanced_markdown,
                images=mineru_result.get('images', []),
                json_data={"pages": model_data} if isinstance(model_data, list) else model_data,
                metadata=self._get_metadata(
                    file_path,
                    parser="SmartDocument",
                    mode=mode,
                    mineru_output=str(mineru_result['output_dir'])
                )
            )
        
        except Exception as e:
            logger.error(f"SmartDocument解析失败: {e}")
            raise
    
    def _parse_with_mineru(self, file_path: Path) -> Dict[str, Any]:
        """使用MinerU进行基础解析"""
        output_dir = Path("output/mineru_temp")
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
        
        # 读取中间JSON（包含版面信息）
        middle_json = result_dir / f"{pdf_name}_middle.json"
        if middle_json.exists():
            with open(middle_json, 'r', encoding='utf-8') as f:
                middle_data = json.load(f)
        else:
            middle_data = {}
            logger.warning(f"中间JSON不存在: {middle_json}")
        
        # 读取模型JSON（包含检测结果）
        model_json = result_dir / f"{pdf_name}_model.json"
        if model_json.exists():
            with open(model_json, 'r', encoding='utf-8') as f:
                model_data = json.load(f)
        else:
            model_data = {}
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
            'middle_data': middle_data,
            'model_data': model_data,
            'images': images,
            'output_dir': result_dir
        }
    
    def _process_table_images(
        self,
        markdown: str,
        model_data: Dict,
        output_dir: Path
    ) -> str:
        """
        处理图片中的表格
        
        检测到图片时，判断是否为表格：
        - 如果是表格：使用VLM识别并还原为Markdown表格
        - 如果不是表格：保留图片链接 + VLM描述
        
        Args:
            markdown: 原始Markdown
            model_data: MinerU的model.json数据
            output_dir: 输出目录
            
        Returns:
            增强后的Markdown
        """
        import re
        
        # 查找所有图片引用
        image_pattern = r'!\[.*?\]\((.*?)\)'
        images = re.findall(image_pattern, markdown)
        
        if not images:
            return markdown
        
        logger.info(f"检测到 {len(images)} 张图片，开始分析...")
        
        enhanced_markdown = markdown
        
        for img_path in images:
            # 判断图片是否为表格
            is_table = self._is_table_image(img_path, model_data)
            
            if is_table:
                logger.info(f"检测到表格图片: {img_path}")
                
                # 使用VLM识别表格
                table_markdown = self._recognize_table_with_vlm(
                    output_dir / img_path.replace('images/', '')
                )
                
                if table_markdown:
                    # 替换图片链接为表格
                    old_img = f"![.*?]\\({img_path}\\)"
                    enhanced_markdown = re.sub(
                        old_img,
                        f"\n{table_markdown}\n",
                        enhanced_markdown
                    )
                    logger.info(f"表格已还原: {img_path}")
                else:
                    # VLM识别失败，保留图片但添加说明
                    logger.warning(f"表格识别失败，保留图片: {img_path}")
            else:
                # 非表格图片，使用VLM生成描述
                if self.vlm_api_key:
                    description = self._describe_image_with_vlm(
                        output_dir / img_path.replace('images/', '')
                    )
                    if description:
                        # 在图片后添加描述
                        enhanced_markdown = enhanced_markdown.replace(
                            f"]({img_path})",
                            f"]({img_path})\n\n**图片说明：** {description}"
                        )
        
        return enhanced_markdown
    
    def _is_table_image(self, img_path: str, model_data: Dict) -> bool:
        """
        判断图片是否为表格
        
        Args:
            img_path: 图片路径
            model_data: MinerU的model.json数据（list格式）
            
        Returns:
            是否为表格
        """
        # model_data是一个list，每个元素是一页的信息
        if not isinstance(model_data, list):
            return False
        
        # 遍历每一页
        for page_data in model_data:
            if not isinstance(page_data, dict):
                continue
            
            # 检查layout_dets信息
            layout_dets = page_data.get('layout_dets', [])
            for item in layout_dets:
                category_id = item.get('category_id', 0)
                # category_id说明：
                # 1: text, 3: title, 5: figure, 7: table, 9: formula
                # 如果是table (7)，返回True
                if category_id == 7:
                    return True
        
        # 如果model_data中没有明确分类，使用启发式方法
        if 'table' in img_path.lower() or 'chart' in img_path.lower():
            return True
        
        return False
    
    def _recognize_table_with_vlm(self, img_path: Path) -> Optional[str]:
        """
        使用VLM识别表格并还原为Markdown格式
        
        Args:
            img_path: 图片路径
            
        Returns:
            Markdown格式的表格
        """
        if not self.vlm_api_key:
            logger.warning("未配置VLM API，无法识别表格")
            return None
        
        if not img_path.exists():
            logger.warning(f"图片不存在: {img_path}")
            return None
        
        try:
            import openai
            import base64
            
            # 读取图片
            with open(img_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode()
            
            # 调用VLM（阿里云Qwen）
            client = openai.OpenAI(
                api_key=self.vlm_api_key,
                base_url=self.vlm_base_url
            )
            
            response = client.chat.completions.create(
                model=self.vlm_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """请识别这张表格图片，并将其转换为Markdown格式的表格。

要求：
1. 保持表格的完整结构
2. 正确识别所有单元格内容
3. 使用Markdown表格语法（| 分隔）
4. 如果有合并单元格，用HTML表示
5. 只输出表格，不要其他说明

示例输出格式：
| 列1 | 列2 | 列3 |
|-----|-----|-----|
| 数据1 | 数据2 | 数据3 |
| 数据4 | 数据5 | 数据6 |"""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000
            )
            
            table_markdown = response.choices[0].message.content
            
            # 验证输出是否为有效表格
            if '|' in table_markdown and '---' in table_markdown:
                logger.info(f"VLM成功识别表格")
                return table_markdown
            else:
                logger.warning(f"VLM输出不是有效表格格式")
                return None
        
        except Exception as e:
            logger.error(f"VLM识别表格失败: {e}")
            return None
    
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
            
            with open(img_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode()
            
            client = openai.OpenAI(api_key=self.vlm_api_key)
            
            response = client.chat.completions.create(
                model=self.vlm_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "请简要描述这张图片的内容（1-2句话）。"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=200
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            logger.error(f"VLM描述图片失败: {e}")
            return None
        """加载版面分析信息"""
        # 从model.json中提取版面信息
        model_file = output_dir.parent / (output_dir.name + "_model.json")
        
        if not model_file.exists():
            return {'regions': []}
        
        with open(model_file, 'r', encoding='utf-8') as f:
            model_data = json.load(f)
        
        regions = []
        
        # 解析每一页的版面信息
        for page_key, page_data in model_data.items():
            if not isinstance(page_data, dict):
                continue
            
            # 获取layout信息
            layout = page_data.get('layout', [])
            for item in layout:
                region = {
                    'type': item.get('category', 'text'),
                    'bbox': item.get('bbox', []),
                    'page': page_key,
                    '!content': ''
                }
                regions.append(region)
        
        return {'regions': regions}
    
    def _enhance_content(self, layout_info: Dict, mineru_result: Dict) -> List[Dict]:
        """
        根据版面类型增强内容
        
        处理策略：
        1. 文字：直接提取
        2. 图片：
           - 如果是表格图片：还原表格结构
           - 其他图片：VLM识别 + 图片链接
        3. 表格：还原表格结构
        """
        enhanced = []
        regions = layout_info.get('regions', [])
        
        for region in regions:
            region_type = region.get('type', 'text')
            
            if region_type == 'text':
                # 文字：直接提取（MinerU已经处理）
                enhanced.append({
                    'type': 'text',
                    'content': region.get('content', ''),
                    'bbox': region.get('bbox', [])
                })
            
            elif region_type == 'table':
                # 表格：MinerU已经识别，直接使用
                enhanced.append({
                    'type': 'table',
                    'content': region.get('content', ''),
                    'bbox': region.get('bbox', [])
                })
            
            elif region_type in ['image', 'figure', 'chart']:
                # 图片：需要VLM处理
                image_content = self._process_image_with_vlm(
                    region,
                    mineru_result['output_dir']
                )
                enhanced.append(image_content)
            
            else:
                # 其他类型：直接使用
                enhanced.append({
                    'type': region_type,
                    'content': region.get('content', ''),
                    'bbox': region.get('bbox', [])
                })
        
        return enhanced
    
    def _process_image_with_vlm(self, region: Dict, output_dir: Path) -> Dict:
        """
        使用VLM处理图片
        
        Args:
            region: 区域信息
            output_dir: 输出目录
            
        Returns:
            处理后的内容
        """
        # 查找对应的图片文件
        bbox = region.get('bbox', [])
        images_dir = output_dir / "images"
        
        # 简单实现：使用MinerU提取的图片
        # TODO: 根据bbox匹配具体图片
        
        if not self.vlm_api_key:
            # 没有VLM API，返回图片链接
            return {
                'type': 'image',
                'content': '![图片](images/placeholder.jpg)',
                'description': '（需要配置VLM API才能生成描述）',
                'bbox': bbox
            }
        
        try:
            # 使用VLM识别图片
            import openai
            
            client = openai.OpenAI(api_key=self.vlm_api_key)
            
            # TODO: 读取图片并调用VLM
            # 这里需要根据实际图片路径读取
            
            prompt = """请分析这张图片：
1. 判断图片类型（表格/图表/示意图/照片等）
2. 如果是表格或图表，请提取数据并还原结构
3. 如果是其他类型，请详细描述内容

请以Markdown格式输出结果。"""
            
            # 模拟VLM响应（实际需要调用API）
            description = "（VLM分析结果将在这里显示）"
            
            return {
                'type': 'image',
                'content': f"![图片](images/placeholder.jpg)\n\n**图片描述：**\n{description}",
                'description': description,
                'bbox': bbox
            }
        
        except Exception as e:
            logger.error(f"VLM处理失败: {e}")
            return {
                'type': 'image',
                'content': '![图片](images/placeholder.jpg)',
                'bbox': bbox
            }
    
    def _assemble_markdown(self, enhanced_content: List[Dict], layout_info: Dict) -> str:
        """
        组装最终Markdown（保留层次结构）
        
        Args:
            enhanced_content: 增强后的内容
            layout_info: 版面信息
            
        Returns:
            完整的Markdown文本
        """
        markdown_parts = []
        
        for item in enhanced_content:
            content = item.get('content', '')
            item_type = item.get('type', 'text')
            
            if item_type == 'title':
                # 标题
                level = item.get('level', 1)
                markdown_parts.append(f"{'#' * level} {content}\n")
            
            elif item_type == 'table':
                # 表格（已经是Markdown格式）
                markdown_parts.append(f"\n{content}\n")
            
            elif item_type in ['image', 'figure', 'chart']:
                # 图片（包含VLM描述）
                markdown_parts.append(f"\n{content}\n")
            
            elif item_type == 'formula':
                # 公式
                markdown_parts.append(f"\n$$\n{content}\n$$\n")
            
            else:
                # 普通文本
                markdown_parts.append(content)
        
        return '\n'.join(markdown_parts)


__all__ = ["SmartDocumentHandler"]
