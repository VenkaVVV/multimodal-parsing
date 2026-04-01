#!/bin/bash
# 测试smart模式（MinerU）

echo "=========================================="
echo "测试Smart模式（MinerU + VLM）"
echo "=========================================="

# 激活环境
source venv/bin/activate

# 启动服务
echo ""
echo "启动服务..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
sleep 2
python start.py > logs/startup.log 2>&1 &
sleep 3

if ! curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo "❌ 服务启动失败"
    exit 1
fi
echo "✅ 服务已启动"

# 测试smart模式
echo ""
echo "开始解析（预计需要60-90秒）..."
echo "请耐心等待..."
echo ""

# 执行并保存结果
result=$(curl -s -X POST "http://localhost:8000/api/v1/parse" \
  -F "file=@tests/data/待测试文档.pdf" \
  -F "mode=smart" \
  --max-time 180)

# 显示摘要
echo "$result" | jq '{
  success: .success,
  markdown_length: (.markdown | length),
  images_count: (.images | length),
  parser: .metadata.parser,
  mode: .metadata.mode
}'

# 保存完整结果
if echo "$result" | jq -e '.success' > /dev/null; then
    echo ""
    echo "保存结果..."
    echo "$result" | jq -r '.markdown' > output/smart_result.md
    echo "$result" > output/smart_result.json
    echo "✅ 已保存: output/smart_result.md"
    echo "✅ 已保存: output/smart_result.json"
fi

echo ""
echo "查看完整结果："
echo "  cat output/smart_result.md"
echo ""
echo "查看MinerU输出："
echo "  ls -la output/mineru_temp/*/ocr/"
