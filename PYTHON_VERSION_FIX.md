# Python版本问题解决方案

## 问题说明

当前系统Python版本：**Python 3.14.3**

MinerU要求：**Python 3.10-3.12**

错误原因：pydantic-core不支持Python 3.14（太新了）

## 解决方案

### 方案1：使用pyenv安装Python 3.10（推荐）

```bash
# 1. 安装pyenv（如果没有）
brew install pyenv

# 2. 安装Python 3.10
pyenv install 3.10.13

# 3. 在项目目录使用Python 3.10
cd /Users/venka/Documents/code/project/multimodal-parsing
pyenv local 3.10.13

# 4. 重新创建虚拟环境
rm -rf venv
python3 -m venv venv
source venv/bin/activate

# 5. 安装依赖
pip install --upgrade pip
pip install -r requirements.txt
pip install "magic-pdf[full]>=0.6.0"
```

### 方案2：使用conda（推荐）

```bash
# 1. 安装miniconda（如果没有）
brew install --cask miniconda

# 2. 创建Python 3.10环境
conda create -n multimodal-parsing python=3.10 -y
conda activate multimodal-parsing

# 3. 安装依赖
pip install -r requirements.txt
pip install "magic-pdf[full]>=0.6.0"
```

### 方案3：使用Homebrew安装Python 3.10

```bash
# 1. 安装Python 3.10
brew install python@3.10

# 2. 使用Python 3.10创建虚拟环境
/usr/local/opt/python@3.10/bin/python3 -m venv venv
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt
pip install "magic-pdf[full]>=0.6.0"
```

### 方案4：使用Docker（最简单）

如果不想折腾Python版本，可以直接使用Docker：

```bash
# 1. 构建Docker镜像
cd /Users/venka/Documents/code/project/multimodal-parsing
docker build -t multimodal-parser -f docker/Dockerfile .

# 2. 运行容器
docker run -p 8000:8000 multimodal-parser
```

## 推荐方案

**推荐使用方案2（conda）**，原因：
1. 安装简单
2. 环境隔离好
3. Python版本管理方便
4. 不会影响系统Python

## 快速开始（使用conda）

```bash
# 1. 安装miniconda
brew install --cask miniconda

# 2. 初始化conda
conda init "$(basename "${SHELL}")"
source ~/.zshrc  # 或 source ~/.bashrc

# 3. 创建环境
conda create -n multimodal-parsing python=3.10 -y
conda activate multimodal-parsing

# 4. 安装依赖
cd /Users/venka/Documents/code/project/multimodal-parsing
pip install -r requirements.txt
pip install "magic-pdf[full]>=0.6.0"

# 5. 启动服务
python start.py
```

## 注意事项

1. **不要使用系统Python 3.14**，它太新了，很多包还不支持
2. **推荐Python 3.10**，这是目前最稳定的版本
3. **使用conda或pyenv**管理Python版本，避免污染系统环境

## 当前项目状态

✅ 项目代码已完成
✅ 基础依赖已安装（在Python 3.14环境）
❌ MinerU无法安装（Python版本不兼容）

**需要重新创建Python 3.10环境**
