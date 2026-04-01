# 选择性VLM模式使用指南

## 功能说明

选择性VLM模式是一种智能解析策略，它会：
1. **先进行版面分析**：检测文档中的不同区域类型
2. **智能选择策略**：根据区域类型选择最优的解析方法
3. **分别处理**：不同类型内容用不同工具处理
4. **整合输出**：将所有结果整合为完整的Markdown

## 解析策略

### 默认策略

| 区域类型 | 解析方法 | 说明 |
|---------|---------|------|
| text（文本） | OCR | 快速提取文字 |
| title（标题） | OCR | 提取标题文本 |
| table（表格） | StructTable | 识别表格结构，输出HTML |
| figure（图片） | **VLM** | 使用VLM生成描述和分析 |
| formula（公式） | UniMERNet | 转换为LaTeX格式 |
| caption（说明） | OCR | 提取说明文字 |

### 核心优势

**图片处理（VLM）：**
- ✅ 自动识别图片类型（照片/图表/示意图）
- ✅ 生成详细的图片描述
- ✅ 分析图表数据和趋势
- ✅ 理解图片语义内容

**文本处理（OCR）：**
- ✅ 速度快（毫秒级）
- ✅ 准确率高
- ✅ 适合大量文本

**表格处理（StructTable）：**
- ✅ 保持表格结构
- ✅ 处理合并单元格
- ✅ 输出HTML格式

## 使用方法

### 1. 基本使用

```bash
# 使用选择性VLM模式
curl -X POST "http://localhost:8000/api/v1/parse" \
  -F "file=@sample.pdf" \
  -F "mode=selective"
```

### 2. 配置VLM API（可选）

如果要使用外部VLM API（更强的理解能力）：

```bash
# 编辑.env文件
echo "VLM_MODEL=deepseek-vl2" >> .env
echo "DEEPSEEK_API_KEY=your_api_key" >> .env

# 重启服务
python start.py
```

### 3. Python代码使用

```python
import requests

# 使用选择性VLM模式
url = "http://localhost:8000/api/v1/parse"
files = {'file': open('sample.pdf', 'rb')}
data = {'mode': 'selective'}

response = requests.post(url, files=files, data=data)
result = response.json()

if result['success']:
    print(result['markdown'])
    
    # 查看处理详情
    print(f"处理区域数: {result['metadata']['regions_count']}")
```

## 三种模式对比

| 特性 | traditional | vlm | selective |
|------|------------|-----|-----------|
| 速度 | 快 | 慢 | 中等 |
| 文本处理 | OCR | VLM | OCR |
| 图片处理 | 保存图片 | VLM理解 | **VLM理解** |
| 表格处理 | StructTable | VLM | StructTable |
| 公式处理 | UniMERNet | VLM | UniMERNet |
| 理解能力 | 中 | 高 | **高（图片）** |
| 成本 | 低 | 高 | **中** |
| 适用场景 | 普通文档 | 复杂文档 | **图文混排** |

## 实际示例

### 示例1：处理包含图表的文档

```bash
# 文档包含：文字 + 图表 + 表格
curl -X POST "http://localhost:8000/api/v1/parse" \
  -F "file=@report.pdf" \
  -F "mode=selective" \
  -o result.json

# 结果：
# - 文字部分：OCR快速提取
# - 图表部分：VLM分析数据和趋势
# - 表格部分：StructTable保持结构
```

### 示例2：处理学术论文

```bash
# 论文包含：文字 + 公式 + 图表
curl -X POST "http://localhost:8000/api/v1/parse" \
  -F "file=@paper.pdf" \
  -F "mode=selective"

# 结果：
# - 文字：OCR提取
# - 公式：UniMERNet转LaTeX
# - 图表：VLM生成描述
```

## 配置选项

### 自定义解析策略

编辑配置文件 `config/default.yaml`：

```yaml
selective_vlm:
  # 文本处理策略
  text: ocr          # 或 vlm
  
  # 表格处理策略
  table: structtable # 或 vlm
  
  # 图片处理策略（推荐VLM）
  figure: vlm        # 或 ocr
  
  # 公式处理策略
  formula: unimernet # 或 vlm
  
  # 标题处理策略
  title: ocr         # 或 vlm
```

### VLM配置

```yaml
vlm:
  model: deepseek-vl2
  api_key: ${DEEPSEEK_API_KEY}
  max_tokens: 4096
  temperature: 0.7
```

## 处理流程详解

### 完整流程

```
输入文档（PDF/图片）
    ↓
【步骤1】版面分析（DocLayout-YOLO）
    ├─ 检测到文本区域 × 10
    ├─ 检测到图片区域 × 3
    ├─ 检测到表格区域 × 2
    └─ 检测到公式区域 × 5
    ↓
【步骤2】阅读顺序排序（XY-Cut++）
    ↓
【步骤3】分区域处理
    ├─ 文本区域 → OCR → 纯文本
    ├─ 图片区域 → VLM → 描述+分析
    ├─ 表格区域 → StructTable → HTML
    └─ 公式区域 → UniMERNet → LaTeX
    ↓
【步骤4】整合结果
    └─ 拼接为完整Markdown
    ↓
输出Markdown
```

### 图片处理示例

**输入：** 一张柱状图

**VLM处理：**
```
这是一张柱状图，展示了2024年Q1-Q4的销售数据：

1. 图表类型：柱状图
2. 数据内容：
   - Q1: 120万
   - Q2: 150万
   - Q3: 180万
   - Q4: 200万
3. 趋势分析：销售额呈持续增长趋势，Q4达到全年最高值
```

**输出Markdown：**
```markdown
![销售数据图表](output/images/chart_001.png)

这是一张柱状图，展示了2024年Q1-Q4的销售数据：

1. 图表类型：柱状图
2. 数据内容：
   - Q1: 120万
   - Q2: 150万
   - Q3: 180万
   - Q4: 200万
3. 趋势分析：销售额呈持续增长趋势，Q4达到全年最高值
```

## 性能参考

| 文档类型 | 页数 | 处理时间 | 说明 |
|---------|------|---------|------|
| 纯文本文档 | 10页 | 3-5秒 | 主要用OCR |
| 图文混排 | 10页 | 8-15秒 | 图片用VLM |
| 学术论文 | 10页 | 10-20秒 | 公式+图表 |
| 数据报告 | 10页 | 15-25秒 | 多图表+表格 |

## 常见问题

### Q1: 选择性VLM和全局VLM有什么区别？

**A:**
- **全局VLM**：所有内容都用VLM处理，速度慢，成本高
- **选择性VLM**：智能选择，文本用OCR（快），图片用VLM（准），性价比高

### Q2: 图片一定会用VLM吗？

**A:** 默认是的，但可以配置：
```yaml
selective_vlm:
  figure: ocr  # 改为OCR，不使用VLM
```

### Q3: 需要配置VLM API吗？

**A:** 两种选择：
1. **使用MinerU内置VLM**：免费，无需API Key
2. **使用外部VLM API**：能力更强，需要API Key

### Q4: 如何知道哪些区域用了VLM？

**A:** 查看日志：
```bash
tail -f logs/app.log | grep "VLM"
```

或查看响应的metadata：
```json
{
  "metadata": {
    "regions_count": 15,
    "vlm_regions": 3,  // 使用VLM的区域数
    "ocr_regions": 10  // 使用OCR的区域数
  }
}
```

## 最佳实践

### 推荐使用场景

✅ **图文混排文档**：报告、论文、说明书
✅ **包含图表的文档**：数据报告、分析报告
✅ **需要图片理解**：产品手册、技术文档

### 不推荐使用场景

❌ **纯文本文档**：用traditional模式更快
❌ **批量处理**：用traditional模式效率更高
❌ **无GPU环境**：VLM需要GPU加速

## 总结

**选择性VLM模式 = 智能策略选择**

- 文本 → OCR（快）
- 图片 → VLM（准）
- 表格 → StructTable（结构化）
- 公式 → UniMERNet（LaTeX）

**最佳性价比：既快速又准确！**

使用方法：
```bash
curl -X POST "http://localhost:8000/api/v1/parse" \
  -F "file=@your_file.pdf" \
  -F "mode=selective"
```
