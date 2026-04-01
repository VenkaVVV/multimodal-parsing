#!/bin/bash
# 自动安装Python 3.10并配置环境

echo "======================================"
echo "多格式文档解析工具 - 环境配置脚本"
echo "======================================"
echo ""

# 检查conda是否已安装
if command -v conda &> /dev/null; then
    echo "✅ conda已安装"
else
    echo "❌ conda未安装"
    echo ""
    echo "请选择安装方式："
    echo "1. 安装miniconda（推荐）"
    echo "2. 安装pyenv"
    echo "3. 手动安装（查看PYTHON_VERSION_FIX.md）"
    echo ""
    read -p "请输入选择 (1/2/3): " choice
    
    case $choice in
        1)
            echo ""
            echo "正在安装miniconda..."
            brew install --cask miniconda
            
            echo ""
            echo "请运行以下命令完成配置："
            echo "  conda init \"\$(basename \"\${SHELL}\")\""
            echo "  source ~/.zshrc  # 或 source ~/.bashrc"
            echo "  ./setup_env.sh"
            ;;
        2)
            echo ""
            echo "正在安装pyenv..."
            brew install pyenv
            
            echo ""
            echo "请运行以下命令完成配置："
            echo "  pyenv install 3.10.13"
            echo "  pyenv local 3.10.13"
            echo "  ./setup_env.sh"
            ;;
        3)
            echo ""
            echo "请查看 PYTHON_VERSION_FIX.md 文件中的详细说明"
            exit 0
            ;;
        *)
            echo "无效选择"
            exit 1
            ;;
    esac
    exit 0
fi

# conda已安装，创建环境
echo ""
echo "正在创建Python 3.10环境..."
conda create -n multimodal-parsing python=3.10 -y

echo ""
echo "正在激活环境..."
conda activate multimodal-parsing

echo ""
echo "正在安装依赖..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "正在安装MinerU（这可能需要10-20分钟）..."
pip install "magic-pdf[full]>=0.6.0"

echo ""
echo "======================================"
echo "✅ 环境配置完成！"
echo "======================================"
echo ""
echo "启动服务："
echo "  conda activate multimodal-parsing"
echo "  python start.py"
echo ""
echo "或使用："
echo "  ./run_conda.sh"
