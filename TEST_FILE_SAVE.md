# 测试脚本文件保存说明

## 三个测试脚本都会保存结果文件

### 1. test_quick.sh（快速测试）

**保存文件：**
- `output/traditional_result.md` - traditional模式的Markdown结果
- `output/traditional_result.json` - traditional模式的完整JSON结果

**测试内容：**
- ✅ 服务启动
- ✅ traditional模式解析
- ✅ VLM配置检查
- ✅ MinerU可用性检查

**耗时：** 约30秒

### 2. test_complete.sh（完整测试）

**保存文件：**
- `output/traditional_result.md` - traditional模式的Markdown结果
- `output/traditional_result.json` - traditional模式的完整JSON结果
- `output/smart_result.md` - smart模式的Markdown结果
- `output/smart_result.json` - smart模式的完整JSON结果
- `output/mineru_temp/` - MinerU的中间文件

**测试内容：**
- ✅ 环境检查
- ✅ 配置检查
- ✅ traditional模式解析
- ✅ smart模式解析（MinerU）
- ✅ VLM配置检查
- ✅ 结果对比

**耗时：** 约3-5分钟

### 3. test_smart.sh（Smart模式测试）

**保存文件：**
- `output/smart_result.md` - smart模式的Markdown结果
- `output/smart_result.json` - smart模式的完整JSON结果
- `output/mineru_temp/` - MinerU的中间文件

**测试内容：**
- ✅ MinerU解析
- ✅ VLM表格识别
- ✅ 图片处理

**耗时：** 约60-90秒

## 文件说明

### Markdown文件（.md）

**内容：** 纯Markdown格式的文档内容

**用途：**
- 直接查看解析结果
- 用于向量化处理
- 用于文档展示

**示例：**
```markdown
# 文档标题

## 第一章

这是文档内容...

| 列1 | 列2 | 列3 |
|-----|-----|-----|
| A   | B   | C   |
```

### JSON文件（.json）

**内容：** 完整的解析结果，包含：

```json
{
  "success": true,
  "markdown": "完整的Markdown内容...",
  "images": [
    {
      "path": "images/img_001.jpg",
      "page": 1,
      "bbox": []
    }
  ],
  "json_data": {
    // MinerU的结构化数据
  },
  "metadata": {
    "source": "原始文件路径",
    "filename": "文件名",
    "format": "pdf",
    "handler": "使用的处理器",
    "parser": "使用的解析器",
    "mode": "解析模式"
  }
}
```

**用途：**
- 获取完整信息
- 查看解析元数据
- 获取图片列表
- 获取结构化数据

### MinerU中间文件

**位置：** `output/mineru_temp/文档名/ocr/`

**文件列表：**
- `文档名.md` - MinerU生成的Markdown
- `文档名_model.json` - 版面检测结果
- `文档名_middle.json` - 中间处理数据
- `文档名_content_list.json` - 内容列表
- `images/` - 提取的图片
  - `img_001.jpg`
  - `img_002.jpg`
  - ...

**用途：**
- 查看MinerU原始输出
- 分析版面检测结果
- 获取提取的图片
- 调试和优化

## 检查结果文件

运行检查脚本：

```bash
./check_results.sh
```

**检查内容：**
- ✅ Markdown文件是否存在
- ✅ JSON文件是否存在
- ✅ MinerU输出是否存在
- ✅ 文件大小和行数
- ✅ JSON结构验证
- ✅ 结果对比

**输出示例：**
```
【Markdown文件】
✅ traditional_result.md: 11585 字节, 354 行
✅ smart_result.md: 8234 字节, 289 行

【JSON文件】
✅ traditional_result.json: 13541 字节
   内容摘要:
   {
     "success": true,
     "markdown_length": 4982,
     "images_count": 4,
     "parser": "PyMuPDF"
   }

【MinerU输出】
✅ mineru_temp目录存在
   文档: 待测试文档
   ✅ Markdown: 3458 字节
   ✅ 图片: 9 张
   ✅ model.json: 87535 字节
```

## 使用流程

### 推荐流程

```bash
# 1. 快速测试（验证基本功能）
./test_quick.sh

# 2. 检查结果
./check_results.sh

# 3. 完整测试（验证所有功能）
./test_complete.sh

# 4. 检查结果
./check_results.sh
```

### 单独测试Smart模式

```bash
# 测试smart模式
./test_smart.sh

# 检查结果
./check_results.sh
```

## 查看结果

### 查看Markdown

```bash
# 查看traditional结果
cat output/traditional_result.md

# 查看smart结果
cat output/smart_result.md

# 对比两个结果
diff output/traditional_result.md output/smart_result.md
```

### 查看JSON

```bash
# 查看完整JSON
cat output/smart_result.json | jq .

# 查看元数据
cat output/smart_result.json | jq '.metadata'

# 查看图片列表
cat output/smart_result.json | jq '.images'

# 查看Markdown长度
cat output/smart_result.json | jq '.markdown | length'
```

### 查看MinerU输出

```bash
# 查看MinerU的Markdown
cat output/mineru_temp/*/ocr/*.md

# 查看版面检测结果
cat output/mineru_temp/*/ocr/*_model.json | jq .

# 查看图片
ls -la output/mineru_temp/*/ocr/images/
```

## 文件对比

### 对比不同模式的结果

```bash
# 对比文件大小
wc -c output/*_result.md

# 对比Markdown长度
echo "Traditional: $(cat output/traditional_result.json | jq -r '.markdown | length') 字符"
echo "Smart: $(cat output/smart_result.json | jq -r '.markdown | length') 字符"

# 对比图片数量
echo "Traditional: $(cat output/traditional_result.json | jq -r '.images | length') 张"
echo "Smart: $(cat output/smart_result.json | jq -r '.images | length') 张"
```

## 总结

**所有测试脚本都会保存结果文件：**

| 脚本 | Markdown | JSON | MinerU输出 |
|------|----------|------|-----------|
| test_quick.sh | ✅ traditional | ✅ traditional | ❌ |
| test_complete.sh | ✅ traditional + smart | ✅ traditional + smart | ✅ |
| test_smart.sh | ✅ smart | ✅ smart | ✅ |

**文件位置：**
- `output/traditional_result.md` - traditional模式Markdown
- `output/traditional_result.json` - traditional模式JSON
- `output/smart_result.md` - smart模式Markdown
- `output/smart_result.json` - smart模式JSON
- `output/mineru_temp/` - MinerU中间文件

**检查方法：**
```bash
./check_results.sh
```

**所有测试脚本已完善，都会保存完整的结果文件！** ✅
