# VLM配置说明

## 已配置的VLM信息

**阿里云Qwen模型：**
- API Key: `sk-xxxx`
- Model: `qwen3.5-397b-a17b`
- Base URL: `https://dashscope.aliyuncs.com/compatible-mode/v1`

## 配置方式

### 方式1：环境变量（推荐）

创建`.env`文件：

```bash
# VLM配置
VLM_API_KEY=sk-xxxx
VLM_MODEL=qwen3.5-397b-a17b
VLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

### 方式2：代码中直接配置

已在`SmartDocumentHandler`中配置默认值：

```python
self.vlm_api_key = os.getenv('VLM_API_KEY', 'sk-xxxx')
self.vlm_model = os.getenv('VLM_MODEL', 'qwen3.5-397b-a17b')
self.vlm_base_url = os.getenv('VLM_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
```

## 使用方法

### 1. 启动服务

```bash
source venv/bin/activate
python start.py
```

### 2. 使用smart模式解析

```bash
curl -X POST "http://localhost:8000/api/v1/parse" \
  -F "file=@document.pdf" \
  -F "mode=smart"
```

### 3. 处理流程

```
PDF文档
    ↓
MinerU解析（版面分析 + OCR）
    ↓
检测到图片
    ├─ 判断是否为表格
    │   ├─ 是表格 → Qwen VLM识别 → Markdown表格
    │   └─ 不是表格 → Qwen VLM描述 + 图片链接
    ↓
输出增强的Markdown
```

## VLM调用示例

### 表格识别

```python
import openai
import base64

# 读取图片
with open('table.jpg', 'rb') as f:
    image_data = base64.b64encode(f.read()).decode()

# 调用Qwen VLM
client = openai.OpenAI(
    api_key='sk-xxxx',
    base_url='https://dashscope.aliyuncs.com/compatible-mode/v1'
)

response = client.chat.completions.create(
    model='qwen3.5-397b-a17b',
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "请识别这张表格图片，转换为Markdown表格格式。"},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
        ]
    }],
    max_tokens=2000
)

print(response.choices[0].message.content)
```

**输出示例：**
```markdown
| 项目 | 1月 | 2月 | 3月 |
|------|-----|-----|-----|
| 销售额 | 100 | 150 | 200 |
| 成本 | 60 | 80 | 100 |
| 利润 | 40 | 70 | 100 |
```

### 图片描述

```python
response = client.chat.completions.create(
    model='qwen3.5-397b-a17b',
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "请简要描述这张图片的内容。"},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
        ]
    }],
    max_tokens=200
)

print(response.choices[0].message.content)
```

**输出示例：**
```
这是一张折线图，展示了2024年1-12月的销售趋势，整体呈上升趋势。
```

## 功能说明

### Smart模式会：

1. **版面分析**：MinerU检测文档中的不同区域
2. **类型识别**：识别文字、图片、表格、公式
3. **智能处理**：
   - 文字：直接提取
   - 表格图片：VLM识别 → Markdown表格
   - 普通图片：VLM描述 + 图片链接
   - 表格：还原结构
   - 公式：转LaTeX
4. **结构保留**：保持原文层次结构

### 输出对比

**原始（只有图片链接）：**
```markdown
![](images/table_001.jpg)
```

**增强后（表格已还原）：**
```markdown
| 月份 | 销售额 | 增长率 |
|------|--------|--------|
| 1月  | 120万  | -      |
| 2月  | 150万  | 25%    |
| 3月  | 180万  | 20%    |
```

## 性能说明

| 操作 | 时间 | 说明 |
|------|------|------|
| MinerU解析 | 30-60秒 | OCR + 版面分析 |
| 表格识别 | 2-5秒/张 | VLM API调用 |
| 图片描述 | 1-2秒/张 | VLM API调用 |

**总时间 = MinerU + 表格数×3秒 + 图片数×1.5秒**

## 注意事项

1. **API调用限制**：阿里云有QPS限制，大量图片可能需要排队
2. **超时设置**：VLM调用默认60秒超时
3. **失败处理**：VLM识别失败时，保留原图片链接
4. **成本控制**：每次VLM调用都会产生费用

## 测试VLM配置

运行测试脚本：

```bash
python test_vlm.py
```

会显示：
- VLM配置信息
- 测试表格识别
- 测试图片描述

## 常见问题

### Q1: VLM调用超时怎么办？

**A:** 
- 检查网络连接
- 确认API Key有效
- 减少max_tokens参数

### Q2: 表格识别不准确？

**A:**
- 图片质量要清晰
- 表格不要太复杂
- 可以尝试不同的Prompt

### Q3: 如何查看VLM调用日志？

**A:** 查看日志文件：
```bash
tail -f logs/app.log | grep VLM
```

## 总结

**VLM已配置完成：**
- ✅ API Key: 已配置
- ✅ Model: qwen3.5-397b-a17b
- ✅ Base URL: 阿里云DashScope
- ✅ 功能：表格识别 + 图片描述

**使用方法：**
```bash
curl -X POST "http://localhost:8000/api/v1/parse" \
  -F "file=@document.pdf" \
  -F "mode=smart"
```

**效果：**
- 表格图片 → Markdown表格（可搜索、可向量化）
- 普通图片 → VLM描述 + 图片链接
- 保留文档结构
