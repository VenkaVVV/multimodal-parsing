#!/bin/bash
# 选择性VLM模式测试脚本

echo "================================"
echo "选择性VLM模式测试"
echo "================================"
echo ""

# 检查服务是否运行
echo "1. 检查服务状态..."
HEALTH=$(curl -s http://localhost:8000/health)
if [ $? -ne 0 ]; then
    echo "❌ 服务未运行，请先启动服务："
    echo "   python start.py"
    exit 1
fi
echo "✅ 服务运行正常"
echo ""

# 测试文件
TEST_FILE="tests/data/待测试文档.md"

if [ ! -f "$TEST_FILE" ]; then
    echo "⚠️  测试文件不存在: $TEST_FILE"
    echo "   请准备一个测试PDF文件"
    exit 1
fi

echo "2. 测试传统模式..."
echo "   命令: curl -X POST ... -F mode=traditional"
TRADITIONAL_RESULT=$(curl -s -X POST "http://localhost:8000/api/v1/parse" \
    -F "file=@$TEST_FILE" \
    -F "mode=traditional")
TRADITIONAL_TIME=$(echo "$TRADITIONAL_RESULT" | jq -r '.metadata.processing_time // 0')
echo "   ✅ 完成，耗时: ${TRADITIONAL_TIME}s"
echo ""

echo "3. 测试VLM模式..."
echo "   命令: curl -X POST ... -F mode=vlm"
VLM_RESULT=$(curl -s -X POST "http://localhost:8000/api/v1/parse" \
    -F "file=@$TEST_FILE" \
    -F "mode=vlm")
VLM_TIME=$(echo "$VLM_RESULT" | jq -r '.metadata.processing_time // 0')
echo "   ✅ 完成，耗时: ${VLM_TIME}s"
echo ""

echo "4. 测试选择性VLM模式..."
echo "   命令: curl -X POST ... -F mode=selective"
SELECTIVE_RESULT=$(curl -s -X POST "http://localhost:8000/api/v1/parse" \
    -F "file=@$TEST_FILE" \
    -F "mode=selective")
SELECTIVE_TIME=$(echo "$SELECTIVE_RESULT" | jq -r '.metadata.processing_time // 0')
REGIONS_COUNT=$(echo "$SELECTIVE_RESULT" | jq -r '.metadata.regions_count // 0')
echo "   ✅ 完成，耗时: ${SELECTIVE_TIME}s"
echo "   📊 检测到区域数: ${REGIONS_COUNT}"
echo ""

echo "================================"
echo "测试结果对比"
echo "================================"
echo ""
echo "模式              | 耗时    | 说明"
echo "-----------------|---------|------------------"
echo "traditional      | ${TRADITIONAL_TIME}s  | 快速稳定"
echo "vlm              | ${VLM_TIME}s  | 理解力强"
echo "selective        | ${SELECTIVE_TIME}s  | 智能策略 ⭐"
echo ""

# 保存结果
echo "5. 保存结果到文件..."
echo "$SELECTIVE_RESULT" | jq -r '.markdown' > output/selective_result.md
echo "   ✅ 已保存到: output/selective_result.md"
echo ""

echo "================================"
echo "测试完成！"
echo "================================"
echo ""
echo "推荐使用选择性VLM模式："
echo "  curl -X POST 'http://localhost:8000/api/v1/parse' \\"
echo "    -F 'file=@your_file.pdf' \\"
echo "    -F 'mode=selective'"
