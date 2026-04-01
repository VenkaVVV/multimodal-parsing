# MinerU模型下载说明

## 问题原因

MinerU需要下载模型文件才能使用，但由于网络问题，自动下载失败。

## 解决方案

### 方案1：手动下载模型（推荐）

**步骤：**

1. **访问HuggingFace仓库**
   ```
   https://huggingface.co/opendatalab/PDF-Extract-Kit-1.0
   ```

2. **下载models目录**
   - 点击 "Files and versions"
   - 找到 `models` 目录
   - 下载整个目录（约2-3GB）

3. **解压到指定位置**
   ```bash
   # 创建目录
   mkdir -p ~/.mineru/models

   # 解压下载的文件到该目录
   # 确保目录结构为：
   # ~/.mineru/models/
   #   ├── Layout/
   #   ├── MFD/
   #   ├── MFR/
   #   ├── OCR/
   #   └── TabRec/
   ```

4. **验证模型文件**
   ```bash
   ls ~/.mineru/models/
   # 应该看到: Layout  MFD  MFR  OCR  TabRec
   ```

### 方案2：使用代理下载

如果有代理，可以设置环境变量后重试：

```bash
export HTTP_PROXY=http://your-proxy:port
export HTTPS_PROXY=http://your-proxy:port
source venv/bin/activate
python download_models.py
```

### 方案3：使用镜像站

使用HuggingFace镜像站：

```bash
export HF_ENDPOINT=https://hf-mirror.com
source venv/bin/activate
python download_models.py
```

## 所需模型文件

根据MinerU的配置，需要以下模型：

```
~/.mineru/models/
├── Layout/
│   ├── YOLO/
│   │   └── doclayout_yolo_docstructbench_imgsz1280_2501.pt
│   └── LayoutLMv3/
│       └── model_final.pth
├── MFD/
│   └── YOLO/
│       └── yolo_v8_ft.pt
├── MFR/
│   └── unimernet_hf_small_2503/
├── OCR/
│   └── paddleocr_torch/
│       ├── ch_PP-OCRv5_det_infer.pth
│       ├── ch_PP-OCRv5_rec_infer.pth
│       └── ...
└── TabRec/
    ├── RapidTable/
    └── StructEqTable/
```

## 下载完成后

模型下载完成后，就可以使用MinerU了：

```bash
# 测试MinerU
source venv/bin/activate
magic-pdf -p tests/data/待测试文档.pdf -o output/mineru_test -m ocr
```

## 当前状态

- ✅ Python 3.13环境已配置
- ✅ MinerU已安装
- ✅ 配置文件已创建
- ❌ 模型文件未下载（需要手动下载）

## 临时方案

在模型下载完成前，系统会自动降级使用PyMuPDF：

```bash
curl -X POST "http://localhost:8000/api/v1/parse" \
  -F "file=@sample.pdf" \
  -F "mode=selective"
```

虽然使用的是PyMuPDF，但功能正常，可以提取文本和图片。
