# 测试指南

## 快速测试（推荐）

测试基本功能，30秒内完成：

```bash
./test_quick.sh
```

**测试内容：**
- ✅ 服务启动
- ✅ traditional模式
- ✅ VLM配置
- ✅ MinerU可用性

## 完整测试

测试所有功能，需要3-5分钟：

```bash
./test_complete.sh
```

**测试内容：**
- ✅ 环境检查
- ✅ 配置检查
- ✅ 服务启动
- ✅ traditional模式
- ✅ smart模式（MinerU）
- ✅ VLM配置
- ✅ 结果对比

## Smart模式测试

单独测试smart模式（MinerU + VLM）：

```bash
./test_smart.sh
```

**预计时间：** 60-90秒

## 手动测试

### 1. 启动服务

```bash
source venv/bin/activate
python start.py
```

### 2. 测试健康检查

```bash
curl http://localhost:8000/health
```

**预期输出：**
```json
{"status":"healthy","version":"0.1.0"}
```

### 3. 测试traditional模式

```bash
curl -X POST "http://localhost:8000/api/v1/parse" \
  -F "file=@tests/data/待测试文档.pdf" \
  -F "mode=traditional" | jq .
```

**预期时间：** 5-10秒

### 4. 测试smart模式

```bash
curl -X POST "http://localhost:8000/api/v1/parse" \
  -F "file=@tests/data/待测试文档.pdf" \
  -F "mode=smart" | jq .
```

**预期时间：** 60-90秒

### 5. 查看结果

**查看Markdown：**
```bash
curl -s -X POST "http://localhost:8000/api/v1/parse" \
  -F "file=@tests/data/待测试文档.pdf" \
  -F "mode=smart" | jq -r '.markdown' > result.md

cat result.md
```

**查看图片：**
```bash
ls -la output/mineru_temp/*/ocr/images/
```

**查看JSON：**
```bash
cat output/mineru_temp/*/ocr/*_model.json | jq .
```

## Python测试

### 测试解析器

```python
import sys
sys.path.insert(0, '.')
from pathlib import Path
from src.core.parser import DocumentParser

# 创建解析器
config = {'parser': {'mode': 'smart'}}
parser = DocumentParser(config)

# 解析文档
result = parser.parse(Path('tests/data/待测试文档.pdf'))

print(f"成功: {result.success}")
print(f"Markdown长度: {len(result.markdown)}")
print(f"图片数量: {len(result.images)}")
print(f"解析器: {result.metadata.get('parser')}")
```

### 测试VLM

```python
import sys
sys.path.insert(0, '.')
from pathlib import Path
from src.handlers.smart_document_handler import SmartDocumentHandler

# 创建处理器
handler = SmartDocumentHandler({})

# 检查配置
print(f"VLM Model: {handler.vlm_model}")
print(f"VLM Base URL: {handler.vlm_base_url}")
print(f"API Key: {handler.vlm_api_key[:20]}...")

# 测试表格识别（需要图片）
# result = handler._recognize_table_with_vlm(Path('table.jpg'))
# print(result)
```

## 测试不同文件格式

### PDF

```bash
curl -X POST "http://localhost:8000/api/v1/parse" \
  -F "file=@document.pdf" \
  -F "mode=smart"
```

### Word

```bash
curl -X POST "http://localhost:8000/api/v1/parse" \
  -F "file=@document.docx" \
  -F "mode=smart"
```

### Excel

```bash
curl -X POST "http://localhost:8000/api/v1/parse" \
  -F "file=@spreadsheet.xlsx" \
  -F "mode=smart"
```

### PPT

```bash
curl -X POST "http://localhost:8000/api/v1/parse" \
  -F "file=@presentation.pptx" \
  -F "mode=smart"
```

### 图片

```bash
curl -X POST "http://localhost:8000/api/v1/parse" \
  -F "file=@image.jpg" \
  -F "mode=smart"
```

## 性能测试

### 测试处理时间

```bash
time curl -s -X POST "http://localhost:8000/api/v1/parse" \
  -F "file=@tests/data/待测试文档.pdf" \
  -F "mode=smart" > /dev/null
```

### 测试并发

```bash
# 并发5个请求
for i in {1..5}; do
  curl -s -X POST "http://localhost:8000/api/v1/parse" \
    -F "file=@tests/data/待测试文档.pdf" \
    -F "mode=traditional" > /dev/null &
done
wait
```

## 检查日志

### 查看实时日志

```bash
tail -f logs/app.log
```

### 查看错误日志

```bash
grep ERROR logs/app.log
```

### 查看VLM调用日志

```bash
grep VLM logs/app.log
```

### 查看MinerU日志

```bash
grep MinerU logs/app.log
```

## 常见问题排查

### 1. 服务启动失败

```bash
# 查看启动日志
cat logs/startup.log

# 检查端口占用
lsof -i:8000

# 检查Python版本
python --version  # 应该是3.13
```

### 2. MinerU失败

```bash
# 检查MinerU配置
cat ~/magic-pdf.json

# 检查模型文件
ls -la ~/.mineru/models/

# 测试MinerU命令
magic-pdf -p tests/data/待测试文档.pdf -o output/test -m ocr
```

### 3. VLM调用失败

```bash
# 检查API Key
echo $VLM_API_KEY

# 测试VLM连接
python3 << 'EOF'
import openai
client = openai.OpenAI(
    api_key='<your api key>',
    base_url='https://dashscope.aliyuncs.com/compatible-mode/v1'
)
print(client.models.list())
EOF
```

### 4. 内存不足

```bash
# 查看内存使用
top -o MEM

# 减少worker数量
# 编辑 config/default.yaml
# api:
#   workers: 1
```

## 测试检查清单

运行快速测试后，检查以下项目：

- [ ] 服务正常启动
- [ ] 健康检查通过
- [ ] traditional模式成功
- [ ] VLM配置正确
- [ ] MinerU可用

运行完整测试后，额外检查：

- [ ] smart模式成功
- [ ] Markdown输出正常
- [ ] 图片提取成功
- [ ] JSON数据完整
- [ ] 表格识别正常（如果有表格图片）

## 测试报告模板

```
测试时间：2024-XX-XX
测试人员：XXX

环境信息：
- Python版本：3.13.x
- 操作系统：macOS/Linux
- MinerU版本：1.3.12

测试结果：
✅ 服务启动：通过
✅ traditional模式：通过（耗时：XX秒）
✅ smart模式：通过（耗时：XX秒）
✅ VLM配置：通过
✅ MinerU集成：通过

输出质量：
- Markdown长度：XXXX字符
- 图片数量：XX张
- 表格识别：XX个

问题记录：
1. [问题描述]
2. [问题描述]

建议：
- [改进建议]
```

## 总结

**推荐测试流程：**

1. **首次测试：** 运行 `./test_quick.sh`
2. **完整测试：** 运行 `./test_complete.sh`
3. **单独测试：** 运行 `./test_smart.sh`

**日常测试：**
```bash
# 快速检查
./test_quick.sh

# 完整验证
./test_complete.sh
```

**测试通过标准：**
- ✅ 所有检查项通过
- ✅ Markdown输出正常
- ✅ 表格识别正确
- ✅ 图片提取完整
