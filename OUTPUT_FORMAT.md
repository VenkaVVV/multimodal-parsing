# 解析结果说明

## 解析结果的形式

解析完成后，**不会直接生成markdown文件**，而是通过API返回JSON格式的结果，其中包含Markdown内容。

## 结果结构

### API响应格式

```json
{
  "success": true,
  "markdown": "# 文档标题\n\n## 第一章\n\n这是正文内容...\n\n<table>\n<tr><td>表格内容</td></tr>\n</table>",
  "json_data": {
    "sheets": [
      {
        "name": "Sheet1",
        "rows": 100,
        "columns": ["列1", "列2"],
        "data": [...]
      }
    ]
  },
  "images": [
    {
      "path": "output/images/img_001.png",
      "page": 1,
      "bbox": [100, 200, 300, 400]
    }
  ],
  "chunks": [
    {
      "id": 0,
      "content": "第一个分片内容...",
      "tokens": 150
    }
  ],
  "snapshots": [
    {
      "page": 1,
      "path": "output/snapshots/sample_page_1.png",
      "width": 1240,
      "height": 1754
    }
  ],
  "metadata": {
    "source": "/path/to/input.pdf",
    "format": "pdf",
    "handler": "MinerU",
    "mode": "traditional"
  },
  "processing_time": 2.5
}
```

## 各部分说明

### 1. markdown（核心结果）

**这是主要的解析结果**，包含完整的Markdown格式内容。

**特点：**
- 纯文本格式，可以直接保存为.md文件
- 保留文档结构（标题、段落、列表等）
- 复杂表格用HTML格式嵌入
- 图片用Markdown引用语法：`![描述](路径)`

**示例：**
```markdown
# 项目报告

## 第一章 引言

这是一段正文内容。

### 1.1 背景

更多内容...

## 第二章 数据分析

<table>
<thead>
<tr>
<th>列1</th>
<th>列2</th>
</tr>
</thead>
<tbody>
<tr>
<td>数据1</td>
<td>数据2</td>
</tr>
</tbody>
</table>

![图表1](output/images/chart_001.png)

## 第三章 结论

这是结论部分。
```

### 2. json_data（结构化数据）

**Excel文件专用**，包含表格的结构化数据。

**用途：**
- 可以直接用于数据分析
- 保留原始数据类型
- 支持多sheet

### 3. images（提取的图片）

**文档中提取的图片列表**。

**保存位置：** `output/images/`

**包含信息：**
- 图片路径
- 所在页码
- 边界框坐标

### 4. chunks（语义分片）

**用于RAG的语义分片结果**（需要启用`enable_chunking=true`）。

**用途：**
- 向量化存储
- 语义检索
- 问答系统

### 5. snapshots（文档快照）

**文档页面的图片快照**（需要启用`enable_snapshot=true`）。

**保存位置：** `output/snapshots/`

**用途：**
- 预览文档
- 溯源查看
- UI展示

## 如何保存为Markdown文件

### 方法1：使用curl + jq

```bash
# 解析并保存Markdown
curl -X POST "http://localhost:8000/api/v1/parse" \
  -F "file=@sample.pdf" \
  -o result.json

# 提取Markdown内容
cat result.json | jq -r '.markdown' > output.md

# 查看结果
cat output.md
```

### 方法2：使用Python

```python
import requests

# 解析文件
url = "http://localhost:8000/api/v1/parse"
files = {'file': open('sample.pdf', 'rb')}
response = requests.post(url, files=files)
result = response.json()

if result['success']:
    # 保存Markdown文件
    with open('output.md', 'w', encoding='utf-8') as f:
        f.write(result['markdown'])
    
    print(f"Markdown已保存到 output.md")
    print(f"提取图片: {len(result['images'])} 张")
    print(f"处理时间: {result['processing_time']:.2f}秒")
```

### 方法3：使用测试脚本

```bash
# 运行测试脚本，会自动保存
./test_api.sh

# 结果会保存到：
# - parsed_result.md (Markdown内容)
# - test_result.json (完整响应)
```

## 实际文件保存情况

### 解析过程中会生成的文件：

```
output/
├── images/              # 提取的图片
│   ├── img_001.png
│   ├── img_002.png
│   └── ...
├── snapshots/           # 文档快照
│   ├── sample_page_1.png
│   ├── sample_page_2.png
│   └── ...
└── (Markdown不自动保存，需要手动提取)
```

### 为什么不自动保存Markdown？

**设计原因：**
1. **灵活性**：用户可以选择是否保存、保存位置、文件名等
2. **API设计**：作为API服务，返回数据比生成文件更通用
3. **避免冲突**：多次解析不会覆盖之前的结果
4. **集成友好**：便于其他系统调用和处理

## 完整使用示例

### 示例1：解析PDF并保存所有结果

```python
import requests
import json
from pathlib import Path

def parse_and_save(file_path, output_dir='output'):
    # 解析文件
    url = "http://localhost:8000/api/v1/parse"
    files = {'file': open(file_path, 'rb')}
    data = {
        'mode': 'traditional',
        'enable_chunking': True,
        'enable_snapshot': True
    }
    
    response = requests.post(url, files=files, data=data)
    result = response.json()
    
    if not result['success']:
        print(f"解析失败: {result['error']}")
        return
    
    # 创建输出目录
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # 1. 保存Markdown
    md_file = output_path / f"{Path(file_path).stem}.md"
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(result['markdown'])
    print(f"✅ Markdown保存到: {md_file}")
    
    # 2. 保存完整JSON结果
    json_file = output_path / f"{Path(file_path).stem}_full.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"✅ 完整结果保存到: {json_file}")
    
    # 3. 保存分片结果（如果有）
    if result['chunks']:
        chunks_file = output_path / f"{Path(file_path).stem}_chunks.json"
        with open(chunks_file, 'w', encoding='utf-8') as f:
            json.dump(result['chunks'], f, ensure_ascii=False, indent=2)
        print(f"✅ 分片结果保存到: {chunks_file}")
    
    # 4. 打印统计信息
    print(f"\n统计信息：")
    print(f"  - Markdown长度: {len(result['markdown'])} 字符")
    print(f"  - 提取图片: {len(result['images'])} 张")
    print(f"  - 语义分片: {len(result['chunks'])} 个")
    print(f"  - 文档快照: {len(result['snapshots'])} 页")
    print(f"  - 处理时间: {result['processing_time']:.2f} 秒")

# 使用
parse_and_save('sample.pdf')
```

### 示例2：批量处理并保存

```bash
#!/bin/bash
# batch_process.sh

for file in *.pdf; do
    echo "处理: $file"
    
    # 解析
    curl -s -X POST "http://localhost:8000/api/v1/parse" \
        -F "file=@$file" \
        -o "${file%.pdf}_result.json"
    
    # 提取Markdown
    cat "${file%.pdf}_result.json" | jq -r '.markdown' > "${file%.pdf}.md"
    
    echo "✅ 完成: ${file%.pdf}.md"
done
```

## 总结

### 解析结果包含：

1. **Markdown内容**（在响应的`markdown`字段）✅
2. **提取的图片**（保存在`output/images/`）✅
3. **文档快照**（保存在`output/snapshots/`）✅
4. **结构化数据**（Excel专用）✅
5. **语义分片**（可选）✅

### 如何获取Markdown文件：

**方法1：** 使用`jq`提取：`cat result.json | jq -r '.markdown' > output.md`
**方法2：** 使用Python保存：`open('output.md', 'w').write(result['markdown'])`
**方法3：** 使用测试脚本：`./test_api.sh`（自动保存）

**Markdown内容在API响应中，需要手动提取保存！**
