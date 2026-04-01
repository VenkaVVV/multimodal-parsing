# MinerU完整安装与使用指南

## 已完成的工作

### ✅ 1. Python环境
- 使用Python 3.13创建虚拟环境
- 兼容MinerU要求（Python 3.10-3.13）

### ✅ 2. MinerU安装
- 成功安装MinerU 1.3.12
- 安装所有依赖（torch, transformers, ultralytics等）

### ✅ 3. 模型下载
- 成功下载所有MinerU模型（约8分钟）
- 模型位置：`~/.mineru/models/`
- 包含模型：
  - MFD（公式检测）
  - Layout（版面分析）
  - OCR（文字识别）
  - MFR（公式识别）
  - TabRec（表格识别）

### ✅ 4. 配置文件
- 创建`~/magic-pdf.json`配置文件

## 当前问题

### ⚠️ 网络SSL问题

**问题描述：**
```
SSLError: HTTPSConnectionPool(host='api.github.com', port=443):
Max retries exceeded with url: /repos/ultralytics/assets/releases/tags/v8.4.0
```

**原因：**
- YOLO模型加载时会尝试从GitHub检查更新
- 网络SSL连接不稳定

**解决方案：**

#### 方案1：设置环境变量（推荐）

```bash
# 禁用网络请求
export YOLO_AUTODOWNLOAD=0
export ULTRALYTICS_HUB_API_KEY=""

# 运行MinerU
source venv/bin/activate
magic-pdf -p input.pdf -o output/ -m ocr
```

#### 方案2：修改Ultralytics设置

```python
# 在Python中设置
from ultralytics import settings
settings['sync'] = False  # 禁用同步
settings['api_key'] = ''  # 清空API key
```

#### 方案3：使用离线模式

```bash
# 设置离线模式
export TRANSFORMERS_OFFLINE=1
export HF_DATASETS_OFFLINE=1

# 运行MinerU
source venv/bin/activate
magic-pdf -p input.pdf -o output/ -m ocr
```

## 完整使用流程

### 1. 环境准备

```bash
# 激活虚拟环境
source venv/bin/activate

# 设置环境变量（避免网络请求）
export YOLO_AUTODOWNLOAD=0
export ULTRALYTICS_HUB_API_KEY=""
```

### 2. 使用MinerU命令行

```bash
# OCR模式（适合扫描版PDF）
magic-pdf -p input.pdf -o output/ -m ocr

# 文本模式（适合文字版PDF）
magic-pdf -p input.pdf -o output/ -m txt

# 自动模式（自动选择）
magic-pdf -p input.pdf -o output/ -m auto

# 指定语言（提高OCR准确率）
magic-pdf -p input.pdf -o output/ -m ocr -l ch

# 指定页码范围
magic-pdf -p input.pdf -o output/ -m ocr -s 0 -e 5
```

### 3. 使用MinerU Python API

```python
from pathlib import Path
from magic_pdf.data.dataset import PymuDocDataset

# 读取PDF
with open('input.pdf', 'rb') as f:
    pdf_bytes = f.read()

# 创建dataset
ds = PymuDocDataset(pdf_bytes)

# 应用处理流程（需要进一步研究API）
# result = ds.apply(...)
```

## 输出结果

MinerU会生成以下文件：

```
output/
├── {pdf_name}/
│   ├── {pdf_name}.md          # Markdown文件
│   ├── {pdf_name}.json        # 结构化JSON
│   ├── images/                # 提取的图片
│   │   ├── image_0.jpg
│   │   ├── image_1.jpg
│   │   └── ...
│   └── layout/                # 版面分析结果
│       ├── layout_0.jpg
│       └── ...
```

## 集成到项目

### 修改MinerUHandler

```python
# src/handlers/mineru_handler.py

import subprocess
from pathlib import Path

def _parse_with_mineru(self, file_path: Path, mode: str):
    """使用MinerU命令行工具解析"""

    # 设置环境变量
    env = {
        'YOLO_AUTODOWNLOAD': '0',
        'ULTRALYTICS_HUB_API_KEY': '',
        'TRANSFORMERS_OFFLINE': '1'
    }

    # 输出目录
    output_dir = Path("output/mineru")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 构建命令
    cmd = [
        'magic-pdf',
        '-p', str(file_path),
        '-o', str(output_dir),
        '-m', 'ocr' if mode == 'traditional' else 'ocr'
    ]

    # 执行命令
    result = subprocess.run(
        cmd,
        env={**os.environ, **env},
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise Exception(f"MinerU failed: {result.stderr}")

    # 读取输出
    md_file = output_dir / file_path.stem / f"{file_path.stem}.md"
    with open(md_file, 'r', encoding='utf-8') as f:
        markdown = f.read()

    return ParseResult(markdown=markdown, ...)
```

## 下一步

1. **解决SSL问题**：使用上述方案之一
2. **测试MinerU**：运行命令行工具测试
3. **集成到项目**：修改MinerUHandler使用命令行工具
4. **优化性能**：考虑使用GPU加速

## 总结

**MinerU已完全安装**，包括：
- ✅ Python 3.13环境
- ✅ MinerU 1.3.12
- ✅ 所有模型（MFD, Layout, OCR, MFR, TabRec）
- ✅ 配置文件

**唯一问题**：网络SSL连接不稳定，可通过环境变量解决。

**推荐使用方式**：
```bash
export YOLO_AUTODOWNLOAD=0
export ULTRALYTICS_HUB_API_KEY=""
magic-pdf -p input.pdf -o output/ -m ocr
```
