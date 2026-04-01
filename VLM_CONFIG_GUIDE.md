# VLM配置说明

## 配置方式

VLM API Key支持三种配置方式，按优先级排序：

### 1. 环境变量（最高优先级）

```bash
export VLM_API_KEY="your_api_key"
export VLM_MODEL="qwen3.5-397b-a17b"
export VLM_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
```

### 2. .env配置文件（中等优先级）

创建`.env`文件：

```bash
VLM_API_KEY=your_api_key
VLM_MODEL=qwen3.5-397b-a17b
VLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

**注意：** `.env`文件已添加到`.gitignore`，不会被提交到git。

### 3. 默认值（最低优先级）

如果未配置，会使用默认值（仅用于开发测试）：

```python
VLM_API_KEY = 'sk-xxxx  # 示例key
VLM_MODEL = 'qwen3.5-397b-a17b'
VLM_BASE_URL = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
```

## 配置优先级

```
环境变量 > .env文件 > 默认值
```

## 使用方法

### 开发环境

1. 复制示例配置：
```bash
cp .env.example .env
```

2. 编辑`.env`文件，填入你的API Key：
```bash
VLM_API_KEY=your_real_api_key
```

### 生产环境

使用环境变量：

```bash
export VLM_API_KEY="your_production_api_key"
python start.py
```

或在Docker中：

```bash
docker run -e VLM_API_KEY="your_api_key" your_image
```

## 安全说明

### ⚠️ 重要提示

1. **不要提交API Key到git**
   - `.env`文件已在`.gitignore`中
   - 不要在代码中硬编码API Key

2. **生产环境使用环境变量**
   - 更安全
   - 便于管理
   - 支持容器化部署

3. **API Key权限控制**
   - 设置合理的API调用限制
   - 定期轮换API Key
   - 监控API使用情况

## 配置验证

运行测试脚本验证配置：

```python
from src.handlers.smart_document_handler import SmartDocumentHandler

handler = SmartDocumentHandler({})
print(f"API Key: {handler.vlm_api_key[:20]}...")
print(f"Model: {handler.vlm_model}")
print(f"Base URL: {handler.vlm_base_url}")
```

## 常见问题

### Q1: 如何查看当前使用的配置？

**A:** 查看日志：
```bash
tail -f logs/app.log | grep "SmartDocumentHandler initialized"
```

### Q2: 配置文件找不到？

**A:** 确保`.env`文件在项目根目录：
```
multimodal-parsing/
├── .env          # 配置文件
├── src/
├── config/
└── ...
```

### Q3: 如何切换不同的VLM模型？

**A:** 修改`.env`文件：
```bash
# 使用DeepSeek
VLM_MODEL=deepseek-vl2
VLM_BASE_URL=https://api.deepseek.com/v1

# 或使用Qwen
VLM_MODEL=qwen3.5-397b-a17b
VLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

## 示例配置

### 阿里云Qwen（推荐）

```bash
VLM_API_KEY=sk-xxxxxxxxxxxxx
VLM_MODEL=qwen3.5-397b-a17b
VLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

### DeepSeek

```bash
VLM_API_KEY=sk-xxxxxxxxxxxxx
VLM_MODEL=deepseek-vl2
VLM_BASE_URL=https://api.deepseek.com/v1
```

### OpenAI

```bash
VLM_API_KEY=sk-xxxxxxxxxxxxx
VLM_MODEL=gpt-4-vision-preview
VLM_BASE_URL=https://api.openai.com/v1
```

## 文件说明

- `.env` - 实际配置文件（不提交到git）
- `.env.example` - 配置示例（提交到git）
- `.gitignore` - 包含`.env`，防止敏感信息泄露

---

**配置已安全处理，API Key从配置文件读取！** ✅
