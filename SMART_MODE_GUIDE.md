# 智能文档解析模式使用指南

## 功能说明

智能文档解析模式（smart）是一个完整的文档解析解决方案，它会：

1. **版面分析**：使用MinerU检测文档中的不同区域类型
2. **类型识别**：识别文字、图片、表格、公式等不同内容
3. **智能处理**：根据内容类型选择最优解析策略
4. **结构还原**：保留原文的层次结构和阅读顺序

## 解析策略

### 1. 文字内容
- **策略**：直接提取文字
- **工具**：MinerU OCR
- **输出**：纯文本

### 2. 图片内容
- **策略A - 表格图片**：
  - 使用VLM识别表格结构
  - 还原为Markdown表格
  - 保留数据完整性

- **策略B - 其他图片**：
  - 使用VLM生成详细描述
  - 分析图片内容（图表、示意图等）
  - 附上图片链接

### 3. 表格内容
- **策略**：还原表格结构
- **工具**：MinerU表格识别
- **输出**：Markdown表格或HTML

### 4. 公式内容
- **策略**：转换为LaTeX
- **工具**：MinerU公式识别
- **输出**：LaTeX公式

## 使用方法

### 基本使用

```bash
curl -X POST "http://localhost:8000/api/v1/parse" \
  -F "file=@document.pdf" \
  -F "mode=smart"
```

### Python代码

```python
import requests

url = "http://localhost:8000/api/v1/parse"
files = {'file': open('document.pdf', 'rb')}
data = {'mode': 'smart'}

response = requests.post(url, files=files, data=data)
result = response.json()

if result['success']:
    print(result['markdown'])
```

## 处理流程

```
输入文档
    ↓
【步骤1】MinerU版面分析
    ├─ 检测区域类型（文字/图片/表格/公式）
    ├─ 确定阅读顺序
    └─ 提取基础内容
    ↓
【步骤2】类型识别与分类
    ├─ 文字区域 → 标记为text
    ├─ 图片区域 → 判断是否为表格
    ├─ 表格区域 → 标记为table
    └─ 公式区域 → 标记为formula
    ↓
【步骤3】智能处理
    ├─ 文字 → 直接提取
    ├─ 表格图片 → VLM识别结构
    ├─ 普通图片 → VLM生成描述
    ├─ 表格 → 还原结构
    └─ 公式 → 转LaTeX
    ↓
【步骤4】结构组装
    ├─ 按阅读顺序排列
    ├─ 保留层次结构
    └─ 生成完整Markdown
    ↓
输出Markdown
```

## 输出示例

### 输入：包含文字、图表、表格的文档

**输出Markdown：**

```markdown
# 文档标题

## 第一章

这是一段文字内容，直接提取。

### 1.1 数据分析

![销售趋势图](images/chart_001.jpg)

**图片描述：**
这是一张折线图，展示了2024年1-12月的销售趋势：
- 1月：120万
- 2月：150万
- ...
- 12月：280万

整体呈上升趋势，Q4达到全年最高。

### 1.2 数据明细

| 月份 | 销售额 | 增长率 |
|------|--------|--------|
| 1月  | 120万  | -      |
| 2月  | 150万  | 25%    |
| ...  | ...    | ...    |

## 第二章

更多内容...
```

## 配置选项

### VLM配置

编辑`.env`文件：

```bash
# VLM配置（用于图片识别）
VLM_MODEL=deepseek-vl2
DEEPSEEK_API_KEY=your_api_key
```

### MinerU配置

编辑`~/magic-pdf.json`：

```json
{
    "models-dir": "/Users/venka/.mineru/models",
    "device": "cpu",
    "layout-config": {
        "model": "doclayout_yolo"
    },
    "table-config": {
        "model": "rapid_table"
    },
    "formula-config": {
        "enable": false
    }
}
```

## 四种模式对比

| 特性 | traditional | vlm | selective | smart |
|------|------------|-----|-----------|-------|
| 版面分析 | ❌ | ❌ | ✅ | ✅ |
| 类型识别 | ❌ | ❌ | ✅ | ✅ |
| 文字提取 | PyMuPDF | VLM | OCR | OCR |
| 图片处理 | 保存 | VLM | VLM | VLM+描述 |
| 表格还原 | ❌ | VLM | StructTable | StructTable |
| 结构保留 | ❌ | ❌ | ⚠️ | ✅ |
| 层次信息 | ❌ | ❌ | ❌ | ✅ |
| 速度 | 快 | 慢 | 中 | 中 |
| 质量 | 低 | 高 | 中 | **高** ⭐ |

## 使用场景

### 推荐使用smart模式

✅ **学术论文**：包含文字、公式、图表
✅ **数据报告**：包含文字、表格、图表
✅ **技术文档**：包含文字、代码、示意图
✅ **产品手册**：包含文字、图片、流程图
✅ **财务报表**：包含文字、表格、图表

### 不推荐使用

❌ **纯文本文档**：用traditional更快
❌ **批量处理**：用traditional效率更高

## 性能参考

| 文档类型 | 页数 | 处理时间 | 说明 |
|---------|------|---------|------|
| 纯文本 | 10页 | 30-40秒 | OCR处理 |
| 图文混排 | 10页 | 40-60秒 | OCR+图片提取 |
| 学术论文 | 10页 | 50-70秒 | OCR+公式 |
| 数据报告 | 10页 | 60-90秒 | OCR+表格+VLM |

## 常见问题

### Q1: smart模式和selective模式有什么区别？

**A:**
- **selective**：只做简单的类型判断，图片统一用VLM
- **smart**：完整的版面分析，图片会判断是否为表格，保留层次结构

### Q2: 需要配置VLM吗？

**A:** 
- 如果文档只有文字和表格：不需要
- 如果文档有图片需要识别：需要配置VLM API

### Q3: 如何知道使用了哪些处理方式？

**A:** 查看响应的metadata：

```json
{
  "metadata": {
    "parser": "SmartDocument",
    "regions": {
      "text": 10,
      "image": 3,
      "table": 2,
      "formula": 5
    }
  }
}
```

### Q4: 输出的Markdown结构准确吗？

**A:** 
- smart模式会保留原文的层次结构
- 标题层级、段落顺序都会保持
- 表格和图片会插入到正确位置

## 最佳实践

### 1. 选择合适的模式

```python
# 纯文本 → traditional
mode = "traditional"

# 复杂文档 → smart
mode = "smart"

# 只需要图片识别 → selective
mode = "selective"
```

### 2. 配置VLM提升图片识别质量

```bash
# 使用DeepSeek VLM
VLM_MODEL=deepseek-vl2
DEEPSEEK_API_KEY=sk-xxx

# 或使用Qwen VLM
VLM_MODEL=qwen2.5-vl
QWEN_API_KEY=sk-xxx
```

### 3. 处理大型文档

```python
# 分批处理
for page_range in [(0, 10), (10, 20), (20, 30)]:
    result = parse_pdf(
        file_path,
        mode="smart",
        start_page=page_range[0],
        end_page=page_range[1]
    )
```

## 总结

**smart模式 = 完整的文档解析解决方案**

- ✅ 版面分析：识别不同内容类型
- ✅ 智能处理：根据类型选择策略
- ✅ 结构保留：保持原文层次
- ✅ 质量最优：MinerU + VLM

**推荐作为默认解析模式！**

使用方法：
```bash
curl -X POST "http://localhost:8000/api/v1/parse" \
  -F "file=@your_file.pdf" \
  -F "mode=smart"
```
