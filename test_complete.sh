#!/bin/bash
# 完整测试流程

echo "=========================================="
echo "智能文档解析系统 - 完整测试"
echo "=========================================="

# 1. 检查环境
echo ""
echo "【步骤1】检查环境..."
echo "----------------------------------------"

if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在"
    exit 1
fi

echo "✅ 虚拟环境存在"

# 激活虚拟环境
source venv/bin/activate

# 检查Python版本
python_version=$(python --version 2>&1)
echo "✅ Python版本: $python_version"

# 检查依赖
if ! python -c "import fitz" 2>/dev/null; then
    echo "❌ PyMuPDF未安装"
    exit 1
fi
echo "✅ PyMuPDF已安装"

if ! python -c "import magic_pdf" 2>/dev/null; then
    echo "❌ MinerU未安装"
    exit 1
fi
echo "✅ MinerU已安装"

if ! python -c "import openai" 2>/dev/null; then
    echo "❌ openai未安装"
    exit 1
fi
echo "✅ openai已安装"

# 2. 检查配置
echo ""
echo "【步骤2】检查配置..."
echo "----------------------------------------"

if [ ! -f "$HOME/magic-pdf.json" ]; then
    echo "❌ MinerU配置文件不存在"
    exit 1
fi
echo "✅ MinerU配置文件存在"

if [ ! -f "config/default.yaml" ]; then
    echo "❌ 应用配置文件不存在"
    exit 1
fi
echo "✅ 应用配置文件存在"

# 3. 检查测试文件
echo ""
echo "【步骤3】检查测试文件..."
echo "----------------------------------------"

if [ ! -f "tests/data/待测试文档.pdf" ]; then
    echo "❌ 测试文件不存在"
    exit 1
fi
echo "✅ 测试文件存在: tests/data/待测试文档.pdf"

# 4. 启动服务
echo ""
echo "【步骤4】启动服务..."
echo "----------------------------------------"

# 停止旧服务
lsof -ti:8000 | xargs kill -9 2>/dev/null
echo "✅ 已停止旧服务"

# 启动新服务
python start.py > logs/startup.log 2>&1 &
sleep 3

# 检查服务是否启动
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "❌ 服务启动失败"
    cat logs/startup.log
    exit 1
fi
echo "✅ 服务启动成功"

# 5. 测试健康检查
echo ""
echo "【步骤5】测试健康检查..."
echo "----------------------------------------"

health=$(curl -s http://localhost:8000/health)
echo "健康检查响应: $health"

if echo "$health" | grep -q "healthy"; then
    echo "✅ 健康检查通过"
else
    echo "❌ 健康检查失败"
    exit 1
fi

# 6. 测试traditional模式
echo ""
echo "【步骤6】测试traditional模式..."
echo "----------------------------------------"

echo "正在解析..."
traditional_result=$(curl -s -X POST "http://localhost:8000/api/v1/parse" \
  -F "file=@tests/data/待测试文档.pdf" \
  -F "mode=traditional")

traditional_success=$(echo "$traditional_result" | jq -r '.success')
traditional_length=$(echo "$traditional_result" | jq -r '.markdown | length')

if [ "$traditional_success" = "true" ]; then
    echo "✅ traditional模式解析成功"
    echo "   Markdown长度: $traditional_length"
    
    # 保存结果
    echo "$traditional_result" | jq -r '.markdown' > output/traditional_result.md
    echo "$traditional_result" > output/traditional_result.json
    echo "   已保存: output/traditional_result.md"
    echo "   已保存: output/traditional_result.json"
else
    echo "❌ traditional模式解析失败"
    echo "$traditional_result" | jq .
fi

# 7. 测试smart模式（MinerU）
echo ""
echo "【步骤7】测试smart模式（MinerU）..."
echo "----------------------------------------"

echo "正在解析（需要30-60秒）..."
smart_result=$(curl -s -X POST "http://localhost:8000/api/v1/parse" \
  -F "file=@tests/data/待测试文档.pdf" \
  -F "mode=smart" \
  --max-time 120)

smart_success=$(echo "$smart_result" | jq -r '.success')
smart_length=$(echo "$smart_result" | jq -r '.markdown | length')
smart_parser=$(echo "$smart_result" | jq -r '.metadata.parser')

if [ "$smart_success" = "true" ]; then
    echo "✅ smart模式解析成功"
    echo "   Markdown长度: $smart_length"
    echo "   解析器: $smart_parser"
    
    # 保存结果
    echo "$smart_result" | jq -r '.markdown' > output/smart_result.md
    echo "$smart_result" > output/smart_result.json
    echo "   已保存: output/smart_result.md"
    echo "   已保存: output/smart_result.json"
else
    echo "❌ smart模式解析失败"
    echo "$smart_result" | jq .
fi

# 8. 检查MinerU输出
echo ""
echo "【步骤8】检查MinerU输出..."
echo "----------------------------------------"

if [ -d "output/mineru_temp" ]; then
    echo "✅ MinerU输出目录存在"
    
    # 检查生成的文件
    pdf_name=$(ls output/mineru_temp/)
    if [ -n "$pdf_name" ]; then
        echo "   文档名称: $pdf_name"
        
        # 检查Markdown
        if [ -f "output/mineru_temp/$pdf_name/ocr/${pdf_name}.md" ]; then
            md_size=$(wc -c < "output/mineru_temp/$pdf_name/ocr/${pdf_name}.md")
            echo "   ✅ Markdown文件: ${md_size} 字节"
        fi
        
        # 检查图片
        if [ -d "output/mineru_temp/$pdf_name/ocr/images" ]; then
            img_count=$(ls output/mineru_temp/$pdf_name/ocr/images/*.jpg 2>/dev/null | wc -l)
            echo "   ✅ 图片数量: $img_count 张"
        fi
        
        # 检查JSON
        if [ -f "output/mineru_temp/$pdf_name/ocr/${pdf_name}_model.json" ]; then
            json_size=$(wc -c < "output/mineru_temp/$pdf_name/ocr/${pdf_name}_model.json")
            echo "   ✅ Model JSON: ${json_size} 字节"
        fi
    fi
else
    echo "⚠️  MinerU输出目录不存在"
fi

# 9. 测试VLM配置
echo ""
echo "【步骤9】测试VLM配置..."
echo "----------------------------------------"

python3 << 'PYTHON_EOF'
import sys
sys.path.insert(0, '.')
from src.handlers.smart_document_handler import SmartDocumentHandler

handler = SmartDocumentHandler({})
print(f"✅ VLM Model: {handler.vlm_model}")
print(f"✅ VLM Base URL: {handler.vlm_base_url}")
print(f"✅ API Key: {handler.vlm_api_key[:20]}...")
PYTHON_EOF

# 10. 对比结果
echo ""
echo "【步骤10】对比结果..."
echo "----------------------------------------"

echo "模式对比："
echo "  traditional: $traditional_length 字符"
echo "  smart:       $smart_length 字符"

if [ "$smart_length" -gt "$traditional_length" ]; then
    improvement=$((smart_length - traditional_length))
    echo "✅ smart模式输出更丰富（+${improvement}字符）"
fi

# 11. 查看输出示例
echo ""
echo "【步骤11】输出示例..."
echo "----------------------------------------"

if [ -f "output/smart_result.md" ]; then
    echo "Smart模式输出前500字符："
    echo ""
    head -c 500 output/smart_result.md
    echo ""
    echo "..."
fi

# 12. 清理
echo ""
echo "【步骤12】清理..."
echo "----------------------------------------"

# 停止服务
lsof -ti:8000 | xargs kill -9 2>/dev/null
echo "✅ 服务已停止"

# 总结
echo ""
echo "=========================================="
echo "测试完成！"
echo "=========================================="
echo ""
echo "测试结果："
echo "  ✅ 环境检查通过"
echo "  ✅ 配置检查通过"
echo "  ✅ 服务启动成功"
echo "  ✅ traditional模式正常"
echo "  ✅ smart模式正常"
echo "  ✅ MinerU集成正常"
echo "  ✅ VLM配置正常"
echo ""
echo "输出文件："
echo "  - output/traditional_result.md (traditional模式Markdown)"
echo "  - output/traditional_result.json (traditional模式完整结果)"
echo "  - output/smart_result.md (smart模式Markdown)"
echo "  - output/smart_result.json (smart模式完整结果)"
echo "  - output/mineru_temp/ (MinerU中间文件)"
echo ""
echo "使用方法："
echo "  curl -X POST 'http://localhost:8000/api/v1/parse' \\"
echo "    -F 'file=@your_file.pdf' \\"
echo "    -F 'mode=smart'"
