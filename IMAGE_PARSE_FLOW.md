# 图片调用parse接口（mode=smart）流程说明

## 测试结果

**输入：** 一张图片（JPG格式，141KB）

**输出：**
- Parser: SmartDocument ✅
- Mode: smart ✅
- Handler: SmartDocumentHandler ✅
- Regions: 1
- VLM Regions: 1 ✅
- Markdown长度: 1823字符

## 执行流程

```
API调用: POST /api/v1/parse
  - file: image.jpg
  - mode: smart
    ↓
routes.py: parse_document()
  - 保存文件到uploads/
  - 调用parser.parse(file_path, mode='smart')
    ↓
parser.py: parse()
  - 调用_get_handler(file_path, mode='smart')
    ↓
parser.py: _get_handler()
  - mode == "smart" → 返回SmartDocumentHandler
    ↓
SmartDocumentHandler: parse()
  - Step 1: 调用MinerU进行版面分析
    ↓
  _parse_with_mineru()
    - 执行: magic-pdf -p image.jpg -o output -m ocr
    - MinerU处理图片：
      * 版面分析（DocLayout-YOLO）
      * OCR（PaddleOCR）
      * 输出Markdown和model.json
    ↓
  - Step 2: 读取版面分析结果
    - model_data: 包含检测到的区域
    - markdown: MinerU生成的Markdown
    ↓
  - Step 3: 输出版面分析摘要
    - 显示每页的区域数量和类型
    ↓
  - Step 4: 根据区域类型增强处理
    ↓
  _enhance_by_region_type()
    - 统计各类型区域数量
    - 对于figure类型（图片）：
      * 调用VLM生成描述
      * 使用新的提示词（包含类型识别、结构化输出、自检）
    ↓
  _describe_image_with_vlm()
    - 读取图片并转为base64
    - 调用VLM API（Qwen3.5-397B）
    - 提示词：
      * Step 1: 识别图片类型（TABLE/FLOWCHART/CHART等）
      * Step 2: 描述内容
      * Step 3: 结构化输出（HTML/Mermaid/Markdown）
      * Step 4: 自检
    ↓
  - Step 5: 返回结果
    - markdown: 包含图片链接和VLM描述
    - metadata: 包含统计信息
```

## 得到的结果

### 1. 图片链接

```markdown
![](images/f561c734904942050ff88014c4f3589f274dee8b25902859a62511062c825c20.jpg)
```

### 2. VLM分析结果

```markdown
---
**图片类型**: TABLE

**内容描述**:
图片展示了一个表格的局部截图，主要涉及费用分摊的规则说明。
- **表头**：分为四列，分别是"分摊场景"、"分摊说明"、"分摊规则"、"示例及说明"。
- **第一行数据**：
    - 前三列为空白。
    - 第四列包含一段详细的"注"释...
- **第二行数据**：
    - 第二列显示文本"费、EBS按量计费。"
    - 第三列显示文本"摊金额=费用账单明细金额；"
    - 第四列显示文本"细金额；日结、月结同理..."

**结构化输出**:
```html
<table>
  <thead>
    <tr>
      <th>分摊场景</th>
      <th>分摊说明</th>
      <th>分摊规则</th>
      <th>示例及说明</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td></td>
      <td></td>
      <td></td>
      <td>
        <b>注：</b><br><br>
        <b>1）</b>每日分摊金额保留的的小数位与费用账单明细对齐...
        <b>2）</b>新购、更配等场景下，当日不足24小时也将计入分摊有效期...
      </td>
    </tr>
    ...
  </tbody>
</table>
```

**自检结果**:
- 已完整提取表头信息
- 已完整提取"注"中的两条详细说明
- 已提取底部可见的表格行内容
- 确认HTML结构正确
- 无遗漏可见元素
---
```

## 关键特性

### 1. MinerU支持图片格式

**支持的格式：**
- PDF
- PPT, PPTX
- DOC, DOCX
- **PNG, JPG** ✅

### 2. 版面分析

**对图片进行版面分析：**
- 使用DocLayout-YOLO检测区域
- 识别区域类型（text/figure/table等）
- 输出区域坐标和置信度

### 3. VLM增强

**对图片使用VLM：**
- 识别图片类型（TABLE/CHART/FLOWCHART等）
- 详细描述内容
- 生成结构化输出（HTML表格）
- 自检确保完整性

### 4. 新提示词的效果

**输出格式：**
```
---
**图片类型**: [TYPE]
**内容描述**: ...
**结构化输出**: ...
**自检结果**: ...
---
```

**优势：**
- 明确的图片类型识别
- 结构化的内容描述
- 可直接使用的HTML/Markdown输出
- 自检机制确保完整性

## 与PDF处理的对比

| 特性 | PDF | 图片 |
|------|-----|------|
| MinerU处理 | ✅ 支持 | ✅ 支持 |
| 版面分析 | ✅ 多页多区域 | ✅ 单页少区域 |
| OCR | ✅ PaddleOCR | ✅ PaddleOCR |
| VLM增强 | ✅ 对figure区域 | ✅ 对整个图片 |
| 输出格式 | Markdown + 图片 | Markdown + VLM描述 |

## 使用场景

### 1. 单张图片解析

```bash
curl -X POST "http://localhost:8000/api/v1/parse" \
  -F "file=@image.jpg" \
  -F "mode=smart"
```

**适用场景：**
- 表格截图
- 数据图表
- 流程图
- 架构图
- 文档截图

### 2. 批量图片处理

```python
import requests
from pathlib import Path

for img_file in Path('images').glob('*.jpg'):
    with open(img_file, 'rb') as f:
        response = requests.post(
            'http://localhost:8000/api/v1/parse',
            files={'file': f},
            data={'mode': 'smart'}
        )
        result = response.json()
        # 保存结果
```

## 性能指标

**测试图片：** 141KB JPG

**处理时间：**
- MinerU版面分析: ~3秒
- VLM调用: ~5秒
- **总计: ~8秒**

**输出质量：**
- 图片类型识别: ✅ 准确
- 内容描述: ✅ 详细
- 结构化输出: ✅ 可用
- 自检: ✅ 完整

## 总结

**对图片调用parse接口（mode=smart）：**

1. ✅ **MinerU可以处理图片** - 支持PNG/JPG格式
2. ✅ **进行版面分析** - 检测区域类型
3. ✅ **调用VLM模型** - 使用新的专业提示词
4. ✅ **生成结构化输出** - HTML表格/Markdown
5. ✅ **包含自检机制** - 确保完整性

**得到的结果：**
- 图片链接
- 图片类型识别
- 详细内容描述
- 结构化输出（可直接使用）
- 自检结果

---

**测试时间：** 2026-04-02
**测试图片：** 141KB JPG
**处理时间：** ~8秒
