# 版面分析与VLM调用说明

## 当前实现情况

### 1. 版面分析（已实现 ✅）

**MinerU内置了完整的版面分析能力：**

```
文档输入
    ↓
DocLayout-YOLO（版面检测）
    ↓
检测出13种区域类型：
├── text（文本段落）
├── table（表格）
├── title（标题）
├── figure（图片/图表）
├── formula（公式）
├── list（列表）
├── code_block（代码块）
├── caption（图表说明）
├── header（页眉）
├── footer（页脚）
├── page_number（页码）
├── footnote（脚注）
└── watermark（水印）
    ↓
XY-Cut++（阅读顺序排序）
    ↓
分区域识别
```

**版面分析是自动进行的**，不需要额外配置。

### 2. VLM调用情况（部分实现 ⚠️）

#### 当前实现方式

**方式1：全局VLM模式**

```python
# 在API调用时指定mode=vlm
curl -X POST "http://localhost:8000/api/v1/parse" \
  -F "file=@sample.pdf" \
  -F "mode=vlm"
```

**工作原理：**
- 整个文档使用MinerU的VLM模式处理
- MinerU 2.5+内置了VLM能力
- 如果MinerU不支持VLM，会自动降级到传统模式

**代码位置：** `src/handlers/mineru_handler.py:109-119`

```python
if mode == "traditional":
    # 传统模式：使用MinerU默认管线
    infer_result = ds.apply_ocr()
else:
    # VLM模式：尝试使用MinerU的VLM能力
    try:
        infer_result = ds.apply_ocr_with_vlm()
    except AttributeError:
        logger.warning("VLM mode not available, fallback to traditional mode")
        infer_result = ds.apply_ocr()
```

#### 未实现的功能

**❌ 按区域类型选择性调用VLM**

例如：
- 检测到图片 → 调用VLM生成描述
- 检测到表格 → 使用传统模型
- 检测到文本 → 使用OCR

**这个功能目前没有实现**，原因是：
1. MinerU已经内置了智能的区域识别逻辑
2. 需要深度修改MinerU的源码
3. 增加了复杂度，但收益不明显

## 详细说明

### 传统模式（mode=traditional）

**流程：**
```
文档 → DocLayout-YOLO检测 → 分区域
    ↓
文本区域 → PaddleOCR识别
表格区域 → StructTable识别 → HTML
公式区域 → UniMERNet识别 → LaTeX
图片区域 → 直接提取保存
    ↓
整合 → Markdown输出
```

**特点：**
- ✅ 速度快（单页1-3秒）
- ✅ 稳定可靠
- ✅ 适合大多数场景
- ❌ 复杂图表理解能力弱

### VLM模式（mode=vlm）

**流程：**
```
文档 → DocLayout-YOLO检测 → 分区域
    ↓
所有区域 → VLM统一处理
    ↓
整合 → Markdown输出
```

**特点：**
- ✅ 理解能力强
- ✅ 能处理复杂版式
- ✅ 图表理解更好
- ❌ 速度慢（单页5-10秒）
- ❌ 需要VLM API（可能收费）

## 图片处理的具体逻辑

### 当前实现

**检测到图片区域后：**

```python
# 1. DocLayout-YOLO检测到figure区域
# 2. 裁剪图片
crop = page_image.crop(figure_bbox)

# 3. 保存图片
image_path = save_image(crop)

# 4. 生成Markdown引用
markdown = f"![图片描述]({image_path})"
```

**不会调用VLM生成描述**，只是保存图片并生成引用。

### 如果需要VLM描述图片

**需要额外实现：**

```python
# 伪代码：检测到图片后调用VLM
if region.type == "figure":
    # 裁剪图片
    crop = page_image.crop(region.bbox)
    
    # 调用VLM生成描述
    description = vlm_client.generate_description(crop)
    
    # 生成Markdown
    markdown = f"![{description}]({image_path})"
```

**这个功能目前没有实现**，但可以很容易添加。

## 如何实现"检测到图片调用VLM"

### 方案1：修改MinerU处理器

```python
# src/handlers/mineru_handler.py

def _parse_with_mineru(self, file_path, mode):
    # ... 现有代码 ...
    
    # 如果是VLM模式，对图片区域特殊处理
    if mode == "vlm":
        # 获取检测到的区域
        regions = infer_result.get_regions()
        
        for region in regions:
            if region.type == "figure":
                # 调用VLM生成描述
                description = self._generate_image_description(region)
                region.description = description
    
    # ... 后续处理 ...
```

### 方案2：添加独立的VLM处理器

```python
# src/handlers/vlm_handler.py

class VLMHandler:
    def describe_image(self, image):
        """使用VLM描述图片"""
        prompt = "请描述这张图片的内容"
        return vlm_client.chat(image, prompt)
    
    def analyze_chart(self, image):
        """使用VLM分析图表"""
        prompt = "分析这个图表的数据和趋势"
        return vlm_client.chat(image, prompt)
```

## 实际使用建议

### 场景1：普通文档（推荐传统模式）

```bash
# 大多数文档用传统模式就够了
curl -X POST "http://localhost:8000/api/v1/parse" \
  -F "file=@document.pdf" \
  -F "mode=traditional"
```

**适用：**
- 文字为主的文档
- 简单表格
- 标准版式

### 场景2：复杂文档（推荐VLM模式）

```bash
# 复杂版式用VLM模式
curl -X POST "http://localhost:8000/api/v1/parse" \
  -F "file=@complex.pdf" \
  -F "mode=vlm"
```

**适用：**
- 复杂图表
- 特殊版式
- 需要深度理解的内容

### 场景3：混合处理（需要自定义）

如果需要：
- 文本用传统模式（快）
- 图片用VLM生成描述（理解深）

**需要修改代码实现**，目前不支持。

## 总结

### 当前实现

✅ **版面分析**：完整实现，自动检测13种区域类型
✅ **传统模式**：完整实现，快速稳定
⚠️ **VLM模式**：部分实现，依赖MinerU的VLM能力
❌ **选择性VLM**：未实现，检测到图片不会自动调用VLM

### 图片处理

**当前行为：**
- 检测到图片 → 保存图片 → 生成Markdown引用
- **不会调用VLM生成描述**

**如果需要VLM描述图片：**
- 需要修改代码
- 或使用全局VLM模式（mode=vlm）

### 建议

1. **大多数情况用传统模式**：速度快，效果好
2. **复杂文档用VLM模式**：理解能力强
3. **如需选择性VLM**：需要二次开发

**版面分析是自动的，但VLM调用是全局的，不会针对特定区域类型选择性调用。**
