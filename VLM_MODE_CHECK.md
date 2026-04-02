# mode=vlm 实现检查报告

## 检查结果

### 1. VLM Handler不存在

**发现：** 没有独立的VLMHandler类

**现有Handler：**
- BaseHandler
- MinerUHandler
- PPTHandler
- ExcelHandler
- SmartDocumentHandler

### 2. MinerUHandler的vlm模式

**代码分析：**

```python
def parse(
    self,
    file_path: Path,
    mode: Literal["traditional", "vlm"] = "traditional"
) -> ParseResult:
    # mode参数被接受，但完全没有使用！
    result = self._run_mineru_cli(file_path)  # 只调用MinerU
    return result
```

**问题：**
- ❌ mode参数被忽略
- ❌ 没有调用VLM模型
- ❌ 只是调用MinerU进行OCR

### 3. parser.py的_get_handler方法

**代码分析：**

```python
def _get_handler(self, file_path: Path, mode: str = "traditional"):
    # 只有smart模式有特殊处理
    if mode == "smart":
        return self._get_smart_document_handler()

    # vlm模式没有特殊处理，返回MinerUHandler
    if suffix in [".pdf", ...]:
        return self._get_mineru_handler()
```

**问题：**
- ❌ mode=vlm没有特殊处理
- ❌ 返回的是MinerUHandler
- ❌ MinerUHandler不支持VLM

### 4. 实际测试结果

```
Mode: vlm
Parser: PyMuPDF  ← 降级了
Handler: MinerUHandler
```

**问题：**
- MinerUHandler调用magic-pdf失败（找不到命令）
- 降级到PyMuPDF
- 完全没有调用VLM

## 问题总结

### mode=vlm的当前实现

```
API调用 mode=vlm
    ↓
parser.parse(mode='vlm')
    ↓
_get_handler(mode='vlm')
    ↓
返回MinerUHandler（没有特殊处理）
    ↓
MinerUHandler.parse(mode='vlm')
    ↓
_run_mineru_cli()  ← mode参数被忽略
    ↓
subprocess.run(['magic-pdf', ...])  ← 找不到命令
    ↓
抛出异常
    ↓
降级到PyMuPDF
    ↓
返回PyMuPDF的结果
```

**结论：mode=vlm目前完全没有实现VLM功能！**

## 正确的mode=vlm应该做什么

### 方案1：创建独立的VLMHandler

```python
class VLMHandler(BaseHandler):
    """VLM处理器 - 全部使用VLM模型"""

    def parse(self, file_path: Path, mode: str = "vlm") -> ParseResult:
        # 1. 将PDF转换为图片
        images = self._pdf_to_images(file_path)

        # 2. 对每一页使用VLM
        results = []
        for img in images:
            result = self._vlm_parse_page(img)
            results.append(result)

        # 3. 合并结果
        return self._merge_results(results)
```

### 方案2：在MinerUHandler中实现vlm模式

```python
def parse(self, file_path: Path, mode: str = "traditional") -> ParseResult:
    if mode == "vlm":
        return self._parse_with_vlm(file_path)
    else:
        return self._run_mineru_cli(file_path)

def _parse_with_vlm(self, file_path: Path) -> ParseResult:
    # 1. 使用MinerU进行基础解析
    mineru_result = self._run_mineru_cli(file_path)

    # 2. 对所有内容使用VLM增强
    enhanced = self._enhance_with_vlm(mineru_result)

    return enhanced
```

### 方案3：复用SmartDocumentHandler

```python
def _get_handler(self, file_path: Path, mode: str = "traditional"):
    if mode == "smart":
        return self._get_smart_document_handler()

    if mode == "vlm":
        # vlm模式也使用SmartDocumentHandler，但配置不同
        handler = self._get_smart_document_handler()
        handler.config['vlm_all'] = True  # 全部使用VLM
        return handler

    return self._get_mineru_handler()
```

## 建议的实现方案

**推荐方案3：复用SmartDocumentHandler**

**理由：**
1. SmartDocumentHandler已经有VLM调用逻辑
2. 只需要添加一个配置选项控制VLM的使用范围
3. 代码复用，避免重复

**实现步骤：**

1. 在SmartDocumentHandler中添加`vlm_mode`配置
2. 当`vlm_mode=True`时，对所有区域使用VLM
3. 在parser.py中，mode=vlm返回配置了`vlm_mode=True`的SmartDocumentHandler

## 当前三种模式的实际效果

| mode | Handler | VLM调用 | 实际效果 |
|------|---------|---------|----------|
| traditional | MinerUHandler | ❌ 无 | MinerU OCR |
| vlm | MinerUHandler | ❌ 无 | MinerU OCR（降级到PyMuPDF）|
| smart | SmartDocumentHandler | ✅ 有 | MinerU + VLM（图片）|

**结论：只有smart模式真正使用了VLM！**

---

**生成时间：** 2026-04-02
