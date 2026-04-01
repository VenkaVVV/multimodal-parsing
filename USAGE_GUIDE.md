# API使用指南

## 服务已启动 ✅

恭喜！文档解析服务已经成功运行。

## API端点

### 1. 健康检查

```bash
curl http://localhost:8000/health
```

**响应示例：**
```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

### 2. 查看API文档

在浏览器中打开：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 3. 解析文档（核心功能）

#### 基本用法

```bash
# 解析PDF文件
curl -X POST "http://localhost:8000/api/v1/parse" \
  -F "file=@your_file.pdf"

# 解析Word文档
curl -X POST "http://localhost:8000/api/v1/parse" \
  -F "file=@your_file.docx"

# 解析Excel文件
curl -X POST "http://localhost:8000/api/v1/parse" \
  -F "file=@your_file.xlsx"

# 解析PPT文件
curl -X POST "http://localhost:8000/api/v1/parse" \
  -F "file=@your_file.pptx"

# 解析图片
curl -X POST "http://localhost:8000/api/v1/parse" \
  -F "file=@your_image.png"
```

#### 高级用法

```bash
# 使用VLM模式（大模型模式，理解力更强）
curl -X POST "http://localhost:8000/api/v1/parse" \
  -F "file=@your_file.pdf" \
  -F "mode=vlm"

# 启用语义分片（用于RAG）
curl -X POST "http://localhost:8000/api/v1/parse" \
  -F "file=@your_file.pdf" \
  -F "enable_chunking=true"

# 生成文档快照
curl -X POST "http://localhost:8000/api/v1/parse" \
  -F "file=@your_file.pdf" \
  -F "enable_snapshot=true"

# 组合使用
curl -X POST "http://localhost:8000/api/v1/parse" \
  -F "file=@your_file.pdf" \
  -F "mode=traditional" \
  -F "enable_chunking=true" \
  -F "enable_snapshot=true"
```

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| file | file | 必填 | 要解析的文件 |
| mode | string | "traditional" | 解析模式：traditional（传统模式，快速稳定）或 vlm（大模型模式，理解力强） |
| enable_chunking | boolean | false | 是否启用语义分片 |
| enable_snapshot | boolean | true | 是否生成文档快照 |

## 响应格式

```json
{
  "success": true,
  "markdown": "# 文档标题\n\n文档内容...",
  "json_data": {
    "sheets": [...]
  },
  "images": [
    {
      "path": "output/images/image1.png",
      "page": 1,
      "bbox": [x1, y1, x2, y2]
    }
  ],
  "chunks": [
    {
      "id": 0,
      "content": "分片内容",
      "tokens": 100
    }
  ],
  "snapshots": [
    {
      "page": 1,
      "path": "output/snapshots/page_1.png",
      "width": 1240,
      "height": 1754
    }
  ],
  "metadata": {
    "source": "/path/to/file.pdf",
    "format": "pdf",
    "handler": "MinerU",
    "mode": "traditional"
  },
  "processing_time": 2.5
}
```

## 使用Python调用

### 方法1：使用requests库

```python
import requests

# 解析文件
url = "http://localhost:8000/api/v1/parse"
files = {'file': open('your_file.pdf', 'rb')}
data = {
    'mode': 'traditional',
    'enable_chunking': True
}

response = requests.post(url, files=files, data=data)
result = response.json()

if result['success']:
    print("解析成功！")
    print(result['markdown'])
else:
    print("解析失败：", result['error'])
```

### 方法2：使用httpx库（异步）

```python
import httpx
import asyncio

async def parse_document(file_path):
    async with httpx.AsyncClient() as client:
        with open(file_path, 'rb') as f:
            files = {'file': (file_path, f, 'application/pdf')}
            data = {'mode': 'traditional'}
            
            response = await client.post(
                "http://localhost:8000/api/v1/parse",
                files=files,
                data=data
            )
            
            return response.json()

# 使用
result = asyncio.run(parse_document('your_file.pdf'))
print(result['markdown'])
```

## 使用JavaScript调用

```javascript
// 使用fetch
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('mode', 'traditional');
formData.append('enable_chunking', 'true');

fetch('http://localhost:8000/api/v1/parse', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        console.log('解析成功！');
        console.log(data.markdown);
    } else {
        console.log('解析失败：', data.error);
    }
});
```

## 实际示例

### 示例1：解析PDF并保存Markdown

```bash
# 解析PDF
curl -X POST "http://localhost:8000/api/v1/parse" \
  -F "file=@sample.pdf" \
  -o result.json

# 提取Markdown内容（需要jq工具）
cat result.json | jq -r '.markdown' > output.md

# 查看结果
cat output.md
```

### 示例2：批量处理文件

```bash
# 创建处理脚本
cat > batch_process.sh << 'EOF'
#!/bin/bash
for file in *.pdf; do
    echo "处理文件: $file"
    curl -X POST "http://localhost:8000/api/v1/parse" \
        -F "file=@$file" \
        -o "${file%.pdf}_result.json"
done
EOF

chmod +x batch_process.sh
./batch_process.sh
```

### 示例3：解析Excel并查看表格

```bash
# 解析Excel
curl -X POST "http://localhost:8000/api/v1/parse" \
  -F "file=@data.xlsx" \
  | jq '.markdown' > tables.md

# 查看Markdown表格
cat tables.md
```

## 常见问题

### Q1: 如何查看解析进度？

A: 目前是同步处理，大文件可能需要等待。后续会添加异步处理接口。

### Q2: 支持哪些文件格式？

A: 支持以下格式：
- PDF (.pdf)
- Word (.docx, .doc)
- Excel (.xlsx, .xls)
- PowerPoint (.pptx, .ppt)
- 图片 (.png, .jpg, .jpeg, .bmp)

### Q3: 解析结果保存在哪里？

A: 
- Markdown内容：在响应的`markdown`字段中
- 提取的图片：保存在`output/images/`目录
- 文档快照：保存在`output/snapshots/`目录
- 日志文件：保存在`logs/app.log`

### Q4: 如何处理大文件？

A: 
- 建议文件大小不超过100MB
- 大文件可能需要较长时间，请耐心等待
- 可以使用异步接口（待实现）

### Q5: 解析质量不理想怎么办？

A: 
- 尝试使用VLM模式：`mode=vlm`
- 检查文件质量（扫描件需要清晰的图片）
- 查看日志文件了解具体问题

## 性能参考

| 文件类型 | 页数/大小 | 处理时间 | 模式 |
|---------|----------|---------|------|
| PDF（数字化） | 10页 | 2-5秒 | traditional |
| PDF（扫描件） | 10页 | 10-20秒 | traditional |
| Word文档 | 10页 | 1-3秒 | traditional |
| Excel表格 | 5个sheet | 1-2秒 | traditional |
| PPT演示文稿 | 20页 | 5-10秒 | traditional |
| 图片 | 1张 | 1-3秒 | traditional |

## 下一步

1. **准备测试文件**：找一些PDF、Word、Excel文件进行测试
2. **查看API文档**：访问 http://localhost:8000/docs
3. **集成到应用**：参考上面的示例代码集成到你的应用中

**开始使用吧！** 🚀
