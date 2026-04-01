#!/bin/bash
# 快速测试 - 只测试基本功能

echo "=========================================="
echo "快速测试"
echo "=========================================="

# 激活环境
source venv/bin/activate

# 1. 检查服务
echo ""
echo "【1】检查服务..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
sleep 2
python start.py > logs/startup.log 2>&1 &
sleep 3

if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo "✅ 服务正常"
else
    echo "❌ 服务异常"
    exit 1
fi

# 2. 测试traditional模式（快速）
echo ""
echo "【2】测试traditional模式..."
result=$(curl -s -X POST "http://localhost:8000/api/v1/parse" \
  -F "file=@tests/data/待测试文档.pdf" \
  -F "mode=traditional")

if echo "$result" | jq -e '.success' > /dev/null; then
    length=$(echo "$result" | jq -r '.markdown | length')
    echo "✅ traditional模式成功 (长度: $length)"
    
    # 保存结果
    echo "$result" | jq -r '.markdown' > output/traditional_result.md
    echo "$result" > output/traditional_result.json
    echo "   已保存: output/traditional_result.md"
    echo "   已保存: output/traditional_result.json"
else
    echo "❌ traditional模式失败"
fi

# 3. 检查VLM配置
echo ""
echo "【3】检查VLM配置..."
python3 << 'EOF'
import sys
sys.path.insert(0, '.')
from src.handlers.smart_document_handler import SmartDocumentHandler
h = SmartDocumentHandler({})
print(f"✅ VLM: {h.vlm_model}")
print(f"✅ API Key: {h.vlm_api_key[:20]}...")
EOF

# 4. 检查MinerU
echo ""
echo "【4】检查MinerU..."
if python -c "import magic_pdf; print('✅ MinerU可用')" 2>/dev/null; then
    :
else
    echo "❌ MinerU不可用"
fi

# 清理
lsof -ti:8000 | xargs kill -9 2>/dev/null

echo ""
echo "=========================================="
echo "快速测试完成！"
echo "=========================================="
echo ""
echo "完整测试请运行："
echo "  ./test_complete.sh"
echo ""
echo "使用方法："
echo "  curl -X POST 'http://localhost:8000/api/v1/parse' \\"
echo "    -F 'file=@your_file.pdf' \\"
echo "    -F 'mode=smart'"
