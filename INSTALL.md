# macOS环境安装和使用指南

## 环境已配置完成 ✅

### 已完成的步骤

1. ✅ 创建了Python虚拟环境（venv/）
2. ✅ 安装了所有基础依赖（fastapi、pandas、opencv等）
3. ✅ 所有核心模块导入测试通过

### 下一步操作

#### 1. 安装MinerU（核心依赖）

```bash
# 激活虚拟环境
source venv/bin/activate

# 安装MinerU（这一步可能需要较长时间）
pip install "magic-pdf[full]>=0.6.0"
```

**注意**：MinerU依赖较多，安装可能需要10-20分钟，请耐心等待。

#### 2. 验证MinerU安装

```bash
source venv/bin/activate
python -c "import magic_pdf; print('MinerU安装成功！')"
```

#### 3. 启动服务

```bash
# 方式1：使用启动脚本（推荐）
./run.sh

# 方式2：手动启动
source venv/bin/activate
python start.py
```

#### 4. 测试API

```bash
# 健康检查
curl http://localhost:8000/health

# 查看API文档
# 浏览器打开：http://localhost:8000/docs
```

## 常见问题

### Q1: MinerU安装失败怎么办？

**A**: MinerU依赖较多，如果安装失败，可以尝试：

```bash
# 1. 升级pip
pip install --upgrade pip

# 2. 分步安装
pip install magic-pdf
pip install paddleocr
pip install paddlepaddle

# 3. 如果还是失败，可以使用降级方案
# 项目已经内置了降级方案，即使MinerU不可用也能工作
```

### Q2: macOS不支持CUDA怎么办？

**A**: 项目已经适配了macOS环境：
- 配置文件中已设置使用CPU模式
- LibreOffice路径已配置为macOS路径
- 所有依赖都支持macOS ARM架构

### Q3: 如何测试解析功能？

**A**: 准备一个测试文件，然后：

```bash
# 上传PDF文件测试
curl -X POST "http://localhost:8000/api/v1/parse" \
  -F "file=@your_file.pdf" \
  -F "mode=traditional"
```

### Q4: 如何在其他电脑上使用？

**A**: 整个项目可以打包迁移：

```bash
# 1. 打包项目
tar -czf multimodal-parsing.tar.gz multimodal-parsing/

# 2. 在其他电脑解压
tar -xzf multimodal-parsing.tar.gz

# 3. 创建虚拟环境并安装依赖
cd multimodal-parsing
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install "magic-pdf[full]>=0.6.0"

# 4. 启动服务
./run.sh
```

## 项目状态

✅ 虚拟环境已创建
✅ 基础依赖已安装
✅ 核心模块测试通过
⏳ MinerU待安装（需要手动执行）
⏳ 服务待启动

## 技术支持

如有问题，请查看：
1. 【方案讨论.md】- 完整的设计和实施记录
2. README.md - 项目说明
3. 日志文件 - logs/app.log
