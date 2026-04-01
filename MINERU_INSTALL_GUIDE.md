# MinerU安装与使用指南

## 问题解决过程

### 1. Python版本问题 ✅ 已解决

**问题：** MinerU需要Python 3.10-3.13，但系统使用Python 3.14

**解决：**
```bash
# 使用Python 3.13重新创建虚拟环境
mv venv venv_py314_backup
/opt/homebrew/bin/python3.13 -m venv venv
source venv/bin/activate
```

**验证：**
```bash
python --version
# Python 3.13.12 ✅
```

### 2. MinerU安装 ✅ 已解决

**安装命令：**
```bash
source venv/bin/activate
pip install "magic-pdf[full]>=0.6.0"
```

**验证：**
```bash
python -c "from magic_pdf.data.dataset import PymuDocDataset; print('✅ MinerU安装成功')"
```

### 3. MinerU配置 ✅ 已解决

**问题：** MinerU需要配置文件 `~/magic-pdf.json`

**解决：**
创建配置文件 `/Users/venka/magic-pdf.json`：
```json
{
    "bucket-name-1": [
        "s3://bucket-name-1/path-to-pdf/"
    ],
    "models-dir": "/Users/venka/.mineru/models",
    "device": "cpu"
}
```

## MinerU API变化

### 新版API（1.3.12）

**创建Dataset：**
```python
from magic_pdf.data.dataset import PymuDocDataset

# 读取PDF为bytes
with open('file.pdf', 'rb') as f:
    pdf_bytes = f.read()

# 创建dataset
ds = PymuDocDataset(pdf_bytes)
```

**可用方法：**
- `apply(proc, *args, **kwargs)` - 应用处理流程
- `classify()` - 分类
- `get_page(page_num)` - 获取指定页
- `dump_to_file(path)` - 保存到文件

**注意：** 旧版API（`apply_ocr()`, `apply_ocr_with_vlm()`）已不存在！

## 当前状态

### ✅ 已完成
1. Python 3.13环境
2. MinerU安装成功
3. MinerU配置文件创建
4. 基础导入测试通过

### ⚠️ 待解决
1. **MinerU新版API使用**：需要了解如何使用`apply()`方法
2. **处理流程配置**：需要配置OCR、表格识别等处理流程
3. **模型下载**：首次使用需要下载模型

## 下一步

### 方案1：使用MinerU命令行工具

MinerU提供了命令行工具，可以直接使用：

```bash
# 查看帮助
magic-pdf --help

# 解析PDF
magic-pdf -p input.pdf -o output/
```

### 方案2：研究MinerU新版API

需要查看MinerU的官方文档或源码，了解如何使用新版API：

```python
# 可能的使用方式
from magic_pdf.data.dataset import PymuDocDataset
from magic_pdf.operators import pipes

# 创建dataset
ds = PymuDocDataset(pdf_bytes)

# 应用处理流程
result = ds.apply(some_pipe_function)
```

### 方案3：使用PyMuPDF作为主要解析器

由于MinerU API变化较大，可以：
1. 继续使用PyMuPDF作为主要解析器
2. 等待MinerU文档更新
3. 或参考MinerU源码实现

## 临时解决方案

**当前可用功能：**
- ✅ PDF文本提取（PyMuPDF）
- ✅ PDF图片提取（PyMuPDF）
- ✅ Markdown输出
- ✅ 多页处理

**使用方式：**
```bash
curl -X POST "http://localhost:8000/api/v1/parse" \
  -F "file=@sample.pdf" \
  -F "mode=selective"
```

## 总结

**MinerU已安装成功**，但API发生了重大变化：
- 旧版API：`ds.apply_ocr()` ❌
- 新版API：`ds.apply(proc)` ✅

需要进一步研究新版API的使用方法，或使用MinerU的命令行工具。

**当前建议：**
1. 继续使用PyMuPDF作为主要解析器（已可用）
2. 研究MinerU新版API
3. 或使用MinerU命令行工具
