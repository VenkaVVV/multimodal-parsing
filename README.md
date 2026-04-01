# 多模态文档解析系统

## 项目概述

一个智能文档解析系统，支持PDF、Word、Excel、PPT、图片等多种格式，输出Markdown格式。

## 解析模式说明

### 三种核心模式

| 模式 | 说明 | 处理方式 | 适用场景 |
|------|------|---------|---------|
| **traditional** | 传统模式 | 全部使用传统方法（PyMuPDF/MinerU OCR） | 纯文本文档，快速处理 |
| **vlm** | VLM模式 | 全部使用VLM（视觉语言模型） | 高质量要求，成本较高 |
| **smart** | 智能模式 | 根据内容类型智能选择处理方式 | **推荐使用** ⭐ |

### Smart模式处理策略

Smart模式会根据内容类型自动选择最优处理方式：

```
检测内容类型
    ├─ 文字 → 直接OCR提取
    ├─ 图片 → 判断是否为表格
    │   ├─ 是表格 → VLM识别 → Markdown表格
    │   └─ 不是表格 → VLM描述 + 图片链接
    ├─ 表格 → 还原表格结构
    └─ 公式 → 转LaTeX
```

**优势：**
- ✅ 表格图片还原为结构化表格（可搜索、可向量化）
- ✅ 普通图片生成描述（保留语义信息）
- ✅ 文字直接提取（快速准确）
- ✅ 成本优化（只在必要时调用VLM）

## 技术架构

### 核心组件

```
multimodal-parsing/
├── src/
│   ├── core/
│   │   ├── parser.py          # 核心解析器（路由到不同Handler）
│   │   └── result.py          # 结果模型
│   ├── handlers/
│   │   ├── base.py            # 处理器基类
│   │   ├── mineru_handler.py  # MinerU处理器（traditional模式）
│   │   ├── smart_document_handler.py  # 智能处理器（smart模式）⭐
│   │   ├── pdf_handler.py     # PDF处理器
│   │   ├── office_handler.py  # Office处理器
│   │   └── image_handler.py   # 图片处理器
│   └── api/
│       └── routes.py          # API路由
├── config/
│   └── default.yaml           # 默认配置
└── tests/                     # 测试文件
```

### 处理器对应关系

| 模式 | 处理器 | 核心技术 |
|------|--------|---------|
| traditional | MinerUHandler | MinerU (OCR) / PyMuPDF |
| vlm | VLMHandler | VLM (DeepSeek/Qwen) |
| smart | SmartDocumentHandler | MinerU + VLM |

## 配置说明

### MinerU配置

**文件：** `~/magic-pdf.json`

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

### VLM配置

**阿里云Qwen模型：**
- 从环境变量或.env文件读取
- 配置优先级：环境变量 > .env文件 > 默认值

**配置方式：**
```bash
# 方式1：环境变量
export VLM_API_KEY="your_api_key"
export VLM_MODEL="qwen3.5-397b-a17b"
export VLM_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"

# 方式2：.env文件
cp .env.example .env
# 编辑.env文件，填入你的API Key
```

**安全说明：**
- ⚠️ .env文件已添加到.gitignore，不会被提交
- ⚠️ 生产环境建议使用环境变量
- ⚠️ 不要在代码中硬编码API Key

## 使用方法

### 启动服务

```bash
source venv/bin/activate
python start.py
```

### API调用

**基本使用：**
```bash
# Traditional模式（快速）
curl -X POST "http://localhost:8000/api/v1/parse" \
  -F "file=@document.pdf" \
  -F "mode=traditional"

# VLM模式（高质量）
curl -X POST "http://localhost:8000/api/v1/parse" \
  -F "file=@document.pdf" \
  -F "mode=vlm"

# Smart模式（推荐）⭐
curl -X POST "http://localhost:8000/api/v1/parse" \
  -F "file=@document.pdf" \
  -F "mode=smart"
```

**Python调用：**
```python
import requests

url = "http://localhost:8000/api/v1/parse"
files = {'file': open('document.pdf', 'rb')}
data = {'mode': 'smart'}  # 推荐使用smart模式

response = requests.post(url, files=files, data=data)
result = response.json()

print(result['markdown'])  # Markdown内容
print(result['images'])    # 图片列表
print(result['metadata'])  # 元数据
```

### 响应格式

```json
{
  "success": true,
  "markdown": "# 文档标题\n\n内容...",
  "images": [
    {"path": "images/img_001.jpg", "page": 1}
  ],
  "json_data": {...},
  "metadata": {
    "parser": "SmartDocument",
    "mode": "smart",
    "handler": "SmartDocumentHandler"
  }
}
```

## 测试

### 测试脚本

| 脚本 | 说明 | 耗时 |
|------|------|------|
| test_quick.sh | 快速测试（traditional模式） | 30秒 |
| test_smart.sh | Smart模式测试 | 90秒 |
| test_complete.sh | 完整测试（所有模式） | 3-5分钟 |
| check_results.sh | 检查结果文件 | 5秒 |

### 运行测试

```bash
# 快速测试
./test_quick.sh

# Smart模式测试
./test_smart.sh

# 检查结果
./check_results.sh
```

### 测试结果文件

所有测试脚本都会保存结果：

- `output/traditional_result.md` - traditional模式Markdown
- `output/traditional_result.json` - traditional模式完整结果
- `output/smart_result.md` - smart模式Markdown
- `output/smart_result.json` - smart模式完整结果
- `output/mineru_temp/` - MinerU中间文件

## 开发日志

### 2024-04-01 VLM配置安全处理

**修改内容：**
- 🔧 API Key从配置文件读取，不再硬编码
- 🔧 添加.env配置文件支持
- 🔧 添加.env.example示例文件
- 🔧 更新.gitignore，防止敏感信息泄露

**配置优先级：**
1. 环境变量（最高）
2. .env配置文件（中等）
3. 默认值（最低，仅用于开发测试）

**安全说明：**
- .env文件已添加到.gitignore
- 生产环境建议使用环境变量
- 不要在代码中硬编码API Key

### 2024-04-01 模式统一

**修改内容：**
- 🔧 统一为三种模式：traditional、vlm、smart
- 🔧 删除所有selective相关代码和文档
- 🔧 更新所有文档中的模式说明
- 🔧 移除parser.py中的_get_selective_vlm_handler方法

**文件修改：**
- 删除：SELECTIVE_VLM_GUIDE.md, SELECTIVE_VLM_TEST_RESULT.md, test_selective_vlm.sh
- 更新：parser.py, routes.py, SMART_MODE_GUIDE.md, IMPLEMENTATION_SUMMARY.md
- 更新：MINERU_INSTALL_GUIDE.md, MODEL_DOWNLOAD_GUIDE.md

**模式说明：**
- traditional: 传统方法，快速处理
- vlm: 全部使用VLM，高质量
- smart: 智能选择，推荐使用（原selective功能的增强版）

### 2024-04-01 Smart模式修复

**问题：**
- smart模式输出按页分割，丢失标题结构
- 图片没有用VLM解析
- model.json格式理解错误（是list不是dict）

**修复：**
- 🔧 修复SmartDocumentHandler使用MinerU输出
- 🔧 修复model.json解析（list格式）
- 🔧 修复_is_table_image方法
- 🔧 修复json_data类型问题

**结果：**
- ✅ 标题层级正确（# # #）
- ✅ 使用MinerU输出
- ✅ Parser显示SmartDocument
- ⚠️  MinerU未识别出表格，图片未用VLM处理

**待优化：**
- [ ] 优化MinerU表格识别
- [ ] 对所有图片使用VLM生成描述

### 2024-04-01 模式整理

**修改内容：**
- 🔧 统一为三种模式：traditional、vlm、smart
- 🔧 移除selective模式，合并到smart模式
- 🔧 更新parser.py和routes.py的模式定义
- 🔧 备份selective_vlm_handler.py

**模式说明：**
- traditional: 传统方法，快速处理
- vlm: 全部使用VLM，高质量
- smart: 智能选择，推荐使用

### 2024-04-01 初始实现

**完成功能：**
- ✅ 项目结构创建
- ✅ 三种解析模式实现（traditional、vlm、smart）
- ✅ MinerU集成（版面分析、OCR、表格识别）
- ✅ VLM集成（表格识别、图片描述）
- ✅ API接口实现
- ✅ 测试脚本完善

**核心实现：**
1. SmartDocumentHandler - 智能文档处理器
   - 根据内容类型选择处理方式
   - 表格图片识别并还原
   - 图片描述生成
   - 结构保留

2. MinerUHandler - MinerU处理器
   - 使用MinerU命令行工具
   - 支持降级到PyMuPDF

3. VLM集成
   - 阿里云Qwen模型
   - 表格识别
   - 图片描述

**测试验证：**
- ✅ 所有模式测试通过
- ✅ 文件保存功能正常
- ✅ 输出质量符合预期

---

## 待办事项

- [ ] VLM模式完整实现（目前只有基础框架）
- [ ] 批量处理优化
- [ ] 更多格式支持
- [ ] 性能优化

## 注意事项

1. **模式选择：**
   - 推荐使用 `smart` 模式
   - 纯文本可用 `traditional` 模式更快
   - `vlm` 模式成本较高

2. **VLM配置：**
   - 必须配置API Key才能使用表格识别功能
   - 已配置阿里云Qwen模型

3. **MinerU：**
   - 需要下载模型文件（约8GB）
   - 首次运行会较慢

4. **模式验证：**
   - 只支持三种模式：traditional、vlm、smart
   - 其他模式会自动降级为traditional

## 常见问题

**Q: 三种模式有什么区别？**

A:
- traditional: 全部用传统方法（PyMuPDF/MinerU），快速但图片信息丢失
- vlm: 全部用VLM，质量高但成本高
- smart: 智能选择处理方式，推荐使用

**Q: 表格图片能还原吗？**

A: smart模式会自动识别表格图片并还原为Markdown表格，可以向量化。

**Q: 如何查看结果？**

A: 所有测试脚本都会保存结果到output目录，包括.md和.json文件。

**Q: 三种模式有什么区别？**

A: 只有三种模式：
- traditional: 传统方法（PyMuPDF/MinerU），快速
- vlm: 全部用VLM，高质量
- smart: 智能选择，推荐使用

**Q: selective模式还能用吗？**

A: 不能，已移除。请使用smart模式代替。smart模式功能更完整。

---

**最后更新：2024-04-01**
