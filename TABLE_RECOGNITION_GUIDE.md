# 表格图片识别与还原功能说明

## 问题

原始实现中，图片中的表格只保留了图片链接，导致：
- ❌ 向量化时丢失表格信息
- ❌ 无法搜索表格内容
- ❌ 无法对表格进行结构化处理

## 解决方案

### 智能识别流程

```
检测到图片
    ↓
判断图片类型
    ├─ 是表格？
    │   ├─ 是 → VLM识别 → 还原为Markdown表格
    │   └─ 否 → VLM描述 + 保留图片链接
    ↓
输出增强的Markdown
```

### 实现细节

#### 1. 表格判断

**方法A：从MinerU的model.json判断**
```python
# MinerU会将图片分类为不同类型
for item in layout:
    category = item.get('category', '')
    if category in ['table', 'chart', 'table_chart']:
        return True  # 是表格
```

**方法B：启发式判断**
```python
# 根据文件名判断
if 'table' in img_path.lower() or 'chart' in img_path.lower():
    return True
```

#### 2. 表格识别

**使用VLM识别表格：**

```python
# 调用VLM API
response = client.chat.completions.create(
    model="deepseek-vl2",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "请识别这张表格图片，转换为Markdown表格格式。"},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
        ]
    }]
)

# 输出示例：
# | 月份 | 销售额 | 增长率 |
# |------|--------|--------|
# | 1月  | 120万  | -      |
# | 2月  | 150万  | 25%    |
```

#### 3. 非表格图片处理

**使用VLM生成描述：**

```python
# 调用VLM生成描述
response = client.chat.completions.create(
    model="deepseek-vl2",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "请简要描述这张图片的内容。"},
            {"type": "image_url", "image_url": {"url": image_url}}
        ]
    }]
)

# 输出示例：
# ![销售趋势图](images/chart.jpg)
# 
# **图片说明：** 这是一张折线图，展示了2024年1-12月的销售趋势，整体呈上升趋势。
```

## 使用方法

### 1. 配置VLM API

编辑`.env`文件：

```bash
# 使用DeepSeek VLM
VLM_MODEL=deepseek-vl2
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxx

# 或使用Qwen VLM
VLM_MODEL=qwen2.5-vl
QWEN_API_KEY=sk-xxxxxxxxxxxxx
```

### 2. 使用smart模式

```bash
curl -X POST "http://localhost:8000/api/v1/parse" \
  -F "file=@document.pdf" \
  -F "mode=smart"
```

### 3. 查看结果

**原始Markdown（只有图片链接）：**
```markdown
![](images/table_001.jpg)
```

**增强后的Markdown（表格已还原）：**
```markdown
| 项目 | 1月 | 2月 | 3月 | 4月 |
|------|-----|-----|-----|-----|
| 销售额 | 120万 | 150万 | 180万 | 200万 |
| 成本 | 80万 | 90万 | 100万 | 110万 |
| 利润 | 40万 | 60万 | 80万 | 90万 |
```

## 效果对比

### 传统方式（PyMuPDF）

```markdown
## Page 1

这是一段文字。

![图片](images/image_0.jpg)

这是另一段文字。
```

**问题：**
- ❌ 表格信息丢失
- ❌ 无法搜索表格内容
- ❌ 向量化时丢失结构信息

### 智能方式（Smart模式）

```markdown
## Page 1

这是一段文字。

| 项目 | 数值 | 说明 |
|------|------|------|
| A    | 100  | 第一个项目 |
| B    | 200  | 第二个项目 |
| C    | 300  | 第三个项目 |

这是另一段文字。
```

**优势：**
- ✅ 表格结构完整保留
- ✅ 可以搜索表格内容
- ✅ 向量化时保留结构信息
- ✅ 支持表格查询和分析

## 配置选项

### VLM选择

| VLM | 优势 | 劣势 | 推荐场景 |
|-----|------|------|---------|
| DeepSeek VL2 | 中文支持好 | 需要API Key | 中文文档 |
| Qwen2.5-VL | 多语言支持 | 需要API Key | 多语言文档 |
| GPT-4 Vision | 效果最好 | 价格较高 | 高质量要求 |

### 表格识别Prompt优化

```python
# 默认Prompt
prompt = "请识别这张表格图片，转换为Markdown表格格式。"

# 优化Prompt（提高准确率）
prompt = """请识别这张表格图片，并将其转换为Markdown格式的表格。

要求：
1. 保持表格的完整结构
2. 正确识别所有单元格内容
3. 使用Markdown表格语法（| 分隔）
4. 如果有合并单元格，用HTML表示
5. 只输出表格，不要其他说明"""
```

## 性能影响

| 操作 | 时间 | 说明 |
|------|------|------|
| MinerU基础解析 | 30-60秒 | OCR + 版面分析 |
| 表格识别（每张） | 2-5秒 | VLM API调用 |
| 图片描述（每张） | 1-2秒 | VLM API调用 |

**总时间 = 基础解析 + 表格数 × 3秒 + 图片数 × 1.5秒**

## 常见问题

### Q1: 没有配置VLM API会怎样？

**A:** 表格不会被识别，只保留图片链接。建议配置VLM API以获得最佳效果。

### Q2: VLM识别表格不准确怎么办？

**A:** 
1. 尝试不同的VLM模型（DeepSeek、Qwen、GPT-4）
2. 优化Prompt，提供更明确的指令
3. 对于复杂表格，可能需要人工校验

### Q3: 识别速度太慢怎么办？

**A:**
1. 使用GPU加速
2. 选择更快的VLM模型
3. 批量处理时使用异步调用

### Q4: 如何验证表格识别效果？

**A:** 查看生成的Markdown，检查：
- 表格结构是否完整
- 单元格内容是否正确
- 是否有遗漏或错误

## 最佳实践

### 1. 选择合适的VLM

```python
# 中文文档 → DeepSeek VL2
VLM_MODEL=deepseek-vl2

# 多语言文档 → Qwen2.5-VL
VLM_MODEL=qwen2.5-vl

# 高质量要求 → GPT-4 Vision
VLM_MODEL=gpt-4-vision
```

### 2. 处理大型文档

```python
# 分批处理，避免超时
for page_range in [(0, 10), (10, 20), (20, 30)]:
    result = parse_pdf(
        file_path,
        mode="smart",
        start_page=page_range[0],
        end_page=page_range[1]
    )
```

### 3. 验证和校对

```python
# 检查表格识别结果
if '|' in markdown and '---' in markdown:
    print("✅ 表格识别成功")
else:
    print("⚠️ 表格识别可能失败，请人工检查")
```

## 总结

**表格图片识别功能解决了：**
- ✅ 表格信息丢失问题
- ✅ 向量化时结构信息缺失
- ✅ 表格内容无法搜索

**使用方法：**
1. 配置VLM API
2. 使用smart模式解析
3. 检查表格识别效果

**推荐配置：**
```bash
# .env
VLM_MODEL=deepseek-vl2
DEEPSEEK_API_KEY=sk-xxx

# 使用
curl -X POST "http://localhost:8000/api/v1/parse" \
  -F "file=@document.pdf" \
  -F "mode=smart"
```
