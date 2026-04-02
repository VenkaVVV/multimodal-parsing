"""
智能型VLM模式处理器（v3）
核心改动：
1. 两阶段 VLM 调用（分类 + 提取）
2. 模型路由：文档/表格 → qwen-vl-ocr，图表/流程图 → qwen3-vl-plus
3. 截断自动续写
4. enable_thinking 统一关闭
"""
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from loguru import logger
import json
import subprocess
import os
import re
import base64

from .base import BaseHandler
from ..core.result import ParseResult, Image


# ============================================================
# 模型路由配置
# ============================================================
# 文档类（OCR 密集）→ 用专用 OCR 模型，精度高
OCR_MODEL_TYPES = {"FORM", "TABLE", "DOCUMENT"}
# 图表类（需要理解语义关系）→ 用通用 VL 模型
VL_MODEL_TYPES = {"FLOWCHART", "CHART", "ARCHITECTURE", "MINDMAP", "UML", "INFOGRAPHIC", "OTHER"}


# ============================================================
# 第一阶段：轻量分类 Prompt（~200 tokens 输出）
# ============================================================
CLASSIFY_PROMPT = """判断这张图片的类型，只返回一个 JSON 对象，不要其他内容。

类型定义：
- FORM：有表格，且表格外还有关键元数据（发票号、日期、印章、签名、编号、二维码等）→ 发票、申请表、合同、登记表
- TABLE：纯数据表格，周围无额外元数据
- FLOWCHART：含节点和箭头的流程逻辑图
- CHART：柱状图、折线图、饼图等数据可视化
- ARCHITECTURE：系统架构图、拓扑图、分层结构图
- MINDMAP：中心发散的树状/脑图结构
- DOCUMENT：多段落文档、报告、PPT 截图
- UML：类图、时序图、用例图等
- INFOGRAPHIC：混合文字数据和装饰元素的信息图
- OTHER：以上都不匹配

返回格式（严格 JSON，无 markdown 包裹）：
{"type": "FORM", "reason": "有发票代码、日期、印章等表格外元数据"}"""


# ============================================================
# 第二阶段：按类型定制的提取 Prompt
# ============================================================
EXTRACT_PROMPTS = {

    "FORM": """请将图片中的表单文档完整转换为 HTML，要求：

1. 直接输出 HTML 代码，不要用 ```html ``` 代码块包裹，不要输出任何解释文字
2. 用一个 <div class="form-doc"> 作为最外层容器
3. 表格外的元数据（标题、编号、日期、校验码等）用 <div> + <p> 组织
4. 表格内容用 <table border="1" cellpadding="4" style="border-collapse:collapse;width:100%">
5. 合并单元格必须用 rowspan/colspan
6. 印章/签名区域用文字标注：<span style="color:red">[印章: XXX]</span>
7. 每一个可见的文字和数据都必须出现在输出中，不得省略

注意：宁可输出冗余，也不要遗漏任何内容。""",

    "TABLE": """请将图片中的表格完整转换为 HTML table，要求：

1. 直接输出 <table> 标签，不要用 ```html ``` 代码块包裹，不要输出任何解释文字
2. 使用 <thead>/<tbody> 区分表头和数据
3. 合并单元格用 rowspan/colspan
4. 加上 border="1" cellpadding="4" style="border-collapse:collapse;width:100%"
5. 每个单元格内容完整提取，不要省略

只输出 HTML，不要其他内容。""",

    "FLOWCHART": """请将图片中的流程图转换为 Mermaid 代码，要求：

1. 直接输出 mermaid 代码，不要解释
2. 根据图片方向选择 flowchart TD 或 flowchart LR
3. 节点 ID 用英文缩写，节点文本保持原文
4. 菱形判断节点用 {判断内容}
5. 分支条件标注在箭头上：-- 是 --> / -- 否 -->
6. 如有子流程用 subgraph

只输出 Mermaid 代码。""",

    "CHART": """请提取图片中数据图表的完整信息，要求：

1. 直接输出，不要代码块包裹
2. 先写一行：图表类型 | 标题 | X轴 | Y轴
3. 然后用 HTML <table> 输出数据表（每个系列一列）
4. 数值尽可能精确，不确定的标注 ≈

只输出上述内容，不要其他解释。""",

    "ARCHITECTURE": """请将图片中的架构图转换为结构化描述 + Mermaid 代码，要求：

1. 直接输出，不要代码块包裹
2. 先用缩进列表描述分层结构（每层包含哪些组件）
3. 然后输出 Mermaid graph TD 代码，用 subgraph 表示分层
4. 所有跨层连接都要标注

只输出上述内容。""",

    "MINDMAP": """请将图片中的思维导图转换为缩进列表，要求：

1. 直接输出，不要代码块包裹
2. 用 Markdown 缩进列表表示层级（- 和缩进）
3. 保持所有节点的原始文本
4. 如节点有特殊标记（颜色、图标）在括号中注明

只输出缩进列表。""",

    "DOCUMENT": """请将图片中的文档内容转换为 Markdown 格式，要求：

1. 直接输出 Markdown，不要代码块包裹
2. 标题用 # / ## / ### 对应层级
3. 正文保持段落划分
4. 如有表格，用 HTML <table> 内嵌（不要用 markdown 表格语法）
5. 如有图片区域，标注 <!-- [图片: 描述] -->
6. 保留加粗、斜体等格式

只输出 Markdown 内容。""",

    "UML": """请将图片中的 UML 图转换为 Mermaid 代码，要求：

1. 直接输出 Mermaid 代码，不要解释
2. 时序图用 sequenceDiagram，类图用 classDiagram，等等
3. 保持所有参与者/类名、消息标签、关系类型
4. 循环/条件片段用 loop / alt / opt 标注

只输出 Mermaid 代码。""",

    "INFOGRAPHIC": """请提取图片中信息图的完整内容，要求：

1. 直接输出，不要代码块包裹
2. 按空间位置分区描述（顶部/中部/底部，或左/中/右）
3. 每个区域：标注类型（标题区/数据区/图表区/图片区）+ 完整文字内容
4. 数据和要点整理为列表

只输出上述内容。""",

    "OTHER": """请完整描述这张图片中的所有内容，要求：

1. 直接输出，不要代码块包裹
2. 所有可见的文字都要提取
3. 描述布局结构和视觉元素
4. 如有表格，用 HTML <table> 输出
5. 如有图表，提取数据

尽可能完整，不要遗漏。"""
}

# 截断续写 prompt
CONTINUE_PROMPT = """你上次的输出在以下位置被截断了，请从截断处继续输出，不要重复已有内容，不要添加解释：

{tail}"""


class SmartDocumentHandler(BaseHandler):
    """智能型VLM模式处理器 - 两阶段调用 + 模型路由"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        # ---- 读取配置 ----
        self.vlm_api_key = os.getenv('VLM_API_KEY')
        self.vlm_base_url = os.getenv(
            'VLM_BASE_URL',
            'https://dashscope.aliyuncs.com/compatible-mode/v1'
        )

        # 模型配置：分两个角色
        self.vlm_model_ocr = os.getenv('VLM_MODEL_OCR', 'qwen-vl-ocr')
        self.vlm_model_vl = os.getenv('VLM_MODEL_VL', 'qwen3-vl-plus')
        # 分类阶段用 VL 模型（需要理解图片语义来判断类型）
        self.vlm_model_classify = os.getenv('VLM_MODEL_CLASSIFY', 'qwen3-vl-plus')

        if not self.vlm_api_key:
            self.vlm_api_key = self._read_api_key_from_env_file()

        if not self.vlm_api_key:
            self.vlm_api_key = 'sk-c9f6dc06a96b4ca9aba27f169a0fa641'
            logger.warning("未配置VLM_API_KEY，使用默认值（仅用于开发测试）")

        # 初始化 OpenAI client（复用连接）
        import openai
        self._client = openai.OpenAI(
            api_key=self.vlm_api_key,
            base_url=self.vlm_base_url
        )

        logger.info(
            f"SmartDocumentHandler initialized | "
            f"OCR模型: {self.vlm_model_ocr} | "
            f"VL模型: {self.vlm_model_vl} | "
            f"分类模型: {self.vlm_model_classify}"
        )

    def _read_api_key_from_env_file(self) -> Optional[str]:
        try:
            env_file = Path('.env')
            if env_file.exists():
                with open(env_file, 'r') as f:
                    for line in f:
                        if line.startswith('VLM_API_KEY='):
                            return line.strip().split('=', 1)[1]
        except Exception as e:
            logger.warning(f"读取配置文件失败: {e}")
        return None

    def _select_model(self, img_type: str) -> str:
        """根据图片类型选择最佳模型"""
        if img_type in OCR_MODEL_TYPES:
            return self.vlm_model_ocr
        return self.vlm_model_vl

    # ============================================================
    # 核心：VLM 调用
    # ============================================================

    def _call_vlm(
        self,
        img_base64: str,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.1,
    ) -> Tuple[str, str]:
        """
        统一的 VLM 调用方法

        Args:
            img_base64: 图片 base64
            prompt: 提示词
            model: 指定模型（None 则用分类模型）
            max_tokens: 最大输出 token
            temperature: 温度

        Returns:
            (content, finish_reason)
        """
        use_model = model or self.vlm_model_classify

        try:
            response = self._client.chat.completions.create(
                model=use_model,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_base64}"
                            }
                        }
                    ]
                }],
                stream=True,
                max_tokens=max_tokens,
                temperature=temperature,
                extra_body={"enable_thinking": False}
            )

            chunks = []
            finish_reason = "unknown"

            for chunk in response:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        chunks.append(delta.content)
                    if chunk.choices[0].finish_reason:
                        finish_reason = chunk.choices[0].finish_reason
                        break

            content = "".join(chunks)
            logger.debug(
                f"VLM调用完成 | model={use_model} | "
                f"len={len(content)} | finish={finish_reason}"
            )
            return content, finish_reason

        except Exception as e:
            logger.error(f"VLM 调用失败 (model={use_model}): {e}")
            return "", "error"

    def _call_vlm_text_only(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.1,
    ) -> Tuple[str, str]:
        """
        纯文本 VLM 调用（用于续写，不需要再传图片）
        """
        use_model = model or self.vlm_model_vl

        try:
            response = self._client.chat.completions.create(
                model=use_model,
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                stream=True,
                max_tokens=max_tokens,
                temperature=temperature,
                extra_body={"enable_thinking": False}
            )

            chunks = []
            finish_reason = "unknown"

            for chunk in response:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        chunks.append(delta.content)
                    if chunk.choices[0].finish_reason:
                        finish_reason = chunk.choices[0].finish_reason
                        break

            return "".join(chunks), finish_reason

        except Exception as e:
            logger.error(f"VLM 续写调用失败: {e}")
            return "", "error"

    # ============================================================
    # 第一阶段：分类
    # ============================================================

    def _classify_image(self, img_base64: str) -> str:
        """轻量分类（~200 tokens 输出）"""
        content, reason = self._call_vlm(
            img_base64,
            CLASSIFY_PROMPT,
            model=self.vlm_model_classify,
            max_tokens=256,
            temperature=0.05
        )

        logger.info(f"分类原始返回: {content.strip()[:200]}")

        # 解析 JSON
        try:
            cleaned = content.strip()
            cleaned = re.sub(r'^```json\s*', '', cleaned)
            cleaned = re.sub(r'\s*```$', '', cleaned)
            result = json.loads(cleaned)
            img_type = result.get("type", "OTHER").upper()
            reason_text = result.get("reason", "")
            logger.info(f"图片分类: {img_type} | 原因: {reason_text}")
            return img_type
        except json.JSONDecodeError:
            for t in ["FORM", "TABLE", "FLOWCHART", "CHART", "ARCHITECTURE",
                       "MINDMAP", "DOCUMENT", "UML", "INFOGRAPHIC"]:
                if t in content.upper():
                    logger.warning(f"JSON解析失败，fallback提取到类型: {t}")
                    return t
            logger.warning(f"分类失败，默认 OTHER。原始返回: {content[:200]}")
            return "OTHER"

    # ============================================================
    # 第二阶段：结构化提取（含截断续写）
    # ============================================================

    def _extract_structure(self, img_base64: str, img_type: str) -> str:
        """按类型提取结构化内容，截断时自动续写"""
        prompt = EXTRACT_PROMPTS.get(img_type, EXTRACT_PROMPTS["OTHER"])
        model = self._select_model(img_type)

        logger.info(f"结构化提取开始 | 类型={img_type} | 模型={model}")

        content, finish_reason = self._call_vlm(
            img_base64,
            prompt,
            model=model,
            max_tokens=8192,
            temperature=0.1
        )

        # ---- 截断续写（最多重试 2 次） ----
        max_retries = 2
        retry = 0
        while finish_reason == "length" and retry < max_retries:
            retry += 1
            logger.warning(
                f"输出被截断，开始续写 (第{retry}次) | "
                f"当前长度={len(content)}"
            )

            # 取最后 500 字符作为上下文
            tail = content[-500:]
            continue_prompt = CONTINUE_PROMPT.format(tail=tail)

            # 续写用同一个模型，但不需要再传图片
            more_content, more_reason = self._call_vlm_text_only(
                continue_prompt,
                model=model,
                max_tokens=4096,
                temperature=0.1
            )

            if more_content:
                content += more_content
            finish_reason = more_reason

        if finish_reason == "length":
            logger.error(
                f"⚠️ 经过{max_retries}次续写仍被截断 | "
                f"类型={img_type} | 最终长度={len(content)}"
            )
        else:
            logger.info(
                f"✅ 结构化提取完成 | 类型={img_type} | "
                f"长度={len(content)} | 续写次数={retry} | finish={finish_reason}"
            )

        # 清理代码块包裹
        content = self._strip_code_fences(content, img_type)

        return content

    def _strip_code_fences(self, content: str, img_type: str) -> str:
        """去掉模型可能添加的代码块包裹"""
        content = content.strip()

        # 去掉开头的 ```xxx
        content = re.sub(r'^```(?:html|mermaid|markdown|json|xml)\s*\n?', '', content)
        # 去掉结尾的 ```
        content = re.sub(r'\n?```\s*$', '', content)

        # Mermaid 类型需要重新包裹（markdown 渲染器需要 ```mermaid 标记）
        if img_type in ("FLOWCHART", "UML", "ARCHITECTURE"):
            if not content.startswith("```mermaid"):
                mermaid_keywords = [
                    "flowchart", "graph", "sequenceDiagram",
                    "classDiagram", "stateDiagram", "erDiagram",
                    "gantt", "pie", "mindmap"
                ]
                if any(content.startswith(kw) for kw in mermaid_keywords):
                    content = f"```mermaid\n{content}\n```"

        return content

    # ============================================================
    # 对外接口：整合两阶段
    # ============================================================

    def _describe_image_with_vlm(self, img_path: Path) -> Optional[str]:
        """两阶段 VLM 图片解析"""
        if not self.vlm_api_key or not img_path.exists():
            return None

        try:
            with open(img_path, 'rb') as f:
                img_base64 = base64.b64encode(f.read()).decode()

            logger.info(f"开始两阶段 VLM 解析: {img_path.name}")

            # 第一阶段：分类
            img_type = self._classify_image(img_base64)

            # 第二阶段：结构化提取（自动选模型 + 自动续写）
            structure = self._extract_structure(img_base64, img_type)

            if not structure:
                logger.warning(f"结构化提取返回为空: {img_path.name}")
                return None

            # 组装输出
            output = f"<!-- VLM解析 | 类型: {img_type} | 模型: {self._select_model(img_type)} -->\n{structure}"

            logger.info(
                f"两阶段解析完成: {img_path.name} | "
                f"类型={img_type} | 模型={self._select_model(img_type)} | "
                f"输出长度={len(output)}"
            )
            return output

        except Exception as e:
            logger.error(f"VLM描述图片失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    # ============================================================
    # 主流程（与原版结构相同）
    # ============================================================

    def parse(self, file_path: Path, mode: str = "smart") -> ParseResult:
        """智能解析文档"""
        logger.info(f"SmartDocument开始解析: {file_path}")
        self._validate_file(file_path)

        try:
            mineru_result = self._parse_with_mineru(file_path)
            model_data = mineru_result.get('model_data', [])
            markdown_content = mineru_result['markdown']
            output_dir = mineru_result['output_dir']

            self._log_layout_analysis(model_data)

            enhanced_markdown, stats = self._enhance_by_region_type(
                markdown_content, model_data, output_dir
            )

            logger.info(f"SmartDocument解析完成: {file_path}")
            logger.info(
                f"处理统计: OCR={stats['ocr_count']}, VLM={stats['vlm_count']}, "
                f"TABLE={stats['table_count']}, FORMULA={stats['formula_count']}"
            )

            return ParseResult(
                markdown=enhanced_markdown,
                images=mineru_result.get('images', []),
                json_data={
                    "pages": model_data,
                    "stats": stats
                } if isinstance(model_data, list) else model_data,
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

        env = os.environ.copy()
        env['YOLO_AUTODOWNLOAD'] = '0'
        env['ULTRALYTICS_HUB_API_KEY'] = ''

        venv_path = Path(__file__).parent.parent.parent / "venv" / "bin" / "magic-pdf"
        magic_pdf_cmd = str(venv_path) if venv_path.exists() else "magic-pdf"

        cmd = [magic_pdf_cmd, '-p', str(file_path), '-o', str(output_dir), '-m', 'ocr']
        logger.info(f"执行MinerU: {' '.join(cmd)}")

        result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=300)

        if result.returncode != 0:
            logger.error(f"MinerU执行失败: {result.stderr}")
            raise Exception(f"MinerU failed: {result.stderr}")

        pdf_name = file_path.stem
        result_dir = output_dir / pdf_name / "ocr"

        md_file = result_dir / f"{pdf_name}.md"
        markdown = md_file.read_text(encoding='utf-8') if md_file.exists() else ""

        model_json = result_dir / f"{pdf_name}_model.json"
        model_data = json.loads(
            model_json.read_text(encoding='utf-8')
        ) if model_json.exists() else []

        images = []
        images_dir = result_dir / "images"
        if images_dir.exists():
            for img_file in images_dir.glob("*.jpg"):
                images.append(Image(path=str(img_file), page=1, bbox=[]))

        return {
            'markdown': markdown,
            'model_data': model_data,
            'images': images,
            'output_dir': result_dir
        }

    def _log_layout_analysis(self, model_data: List):
        """输出版面分析结果摘要"""
        if not model_data:
            logger.warning("版面分析数据为空")
            return

        type_names = {
            0: 'unknown', 1: 'text', 2: 'interline_equation', 3: 'title',
            4: 'interline_equation', 5: 'figure', 6: 'figure_caption',
            7: 'table', 8: 'table_caption', 9: 'formula', 10: 'text',
            11: 'text', 13: 'interline_equation', 14: 'interline_equation',
            15: 'caption', 16: 'interline_equation'
        }

        total_regions = 0
        total_by_type = {}

        for page_idx, page_data in enumerate(model_data):
            if not isinstance(page_data, dict):
                continue
            layout_dets = page_data.get('layout_dets', [])
            page_info = page_data.get('page_info', {})

            page_by_type = {}
            for det in layout_dets:
                category = det.get('category_id', -1)
                page_by_type[category] = page_by_type.get(category, 0) + 1
                total_by_type[category] = total_by_type.get(category, 0) + 1
                total_regions += 1

            logger.info(
                f"Page {page_idx + 1}: {len(layout_dets)} regions, "
                f"size={page_info.get('width', 0)}x{page_info.get('height', 0)}"
            )
            type_strs = [
                f"{type_names.get(c, f'cat_{c}')}({c})={n}"
                for c, n in sorted(page_by_type.items())
            ]
            logger.info(f"  Types: {', '.join(type_strs)}")

        logger.info(f"Total: {len(model_data)} pages, {total_regions} regions")

    def _enhance_by_region_type(
        self, markdown: str, model_data: List, output_dir: Path
    ) -> tuple:
        """根据区域类型增强处理"""
        stats = {
            'total_count': 0, 'ocr_count': 0,
            'vlm_count': 0, 'table_count': 0, 'formula_count': 0
        }

        if not isinstance(model_data, list):
            return markdown, stats

        for page_data in model_data:
            if not isinstance(page_data, dict):
                continue
            for item in page_data.get('layout_dets', []):
                cid = item.get('category_id', 0)
                stats['total_count'] += 1
                if cid in [1, 3, 15]:
                    stats['ocr_count'] += 1
                elif cid == 5:
                    stats['vlm_count'] += 1
                elif cid == 7:
                    stats['table_count'] += 1
                elif cid == 9:
                    stats['formula_count'] += 1

        image_pattern = r'!\[.*?\]\((.*?)\)'
        images = re.findall(image_pattern, markdown)

        if not images:
            logger.info("未检测到图片，无需VLM处理")
            return markdown, stats

        logger.info(f"检测到 {len(images)} 张图片，使用两阶段VLM解析...")

        enhanced_markdown = markdown
        for img_path in images:
            full_img_path = output_dir / img_path
            if not full_img_path.exists():
                logger.warning(f"图片不存在: {full_img_path}")
                continue

            description = self._describe_image_with_vlm(full_img_path)
            if description:
                enhanced_markdown = enhanced_markdown.replace(
                    f"]({img_path})",
                    f"]({img_path})\n\n{description}"
                )
                logger.info(f"已为图片添加VLM解析: {img_path}")

        return enhanced_markdown, stats


__all__ = ["SmartDocumentHandler"]