#!/bin/bash
# 快速测试脚本

API_URL="http://localhost:8000"

echo "======================================"
echo "文档解析服务 - 快速测试"
echo "======================================"
echo ""

# 1. 健康检查
echo "1. 健康检查..."
curl -s "$API_URL/health" | jq .
echo ""

# 2. 查看API信息
echo "2. API信息..."
curl -s "$API_URL/" | jq .
echo ""

# 3. 测试文件解析
echo "3. 测试文件解析"
echo "请选择要测试的文件："
echo "  a) PDF文件"
echo "  b) Word文档"
echo "  c) Excel文件"
echo "  d) PPT文件"
echo "  e) 图片文件"
echo "  f) 自定义文件路径"
echo ""
read -p "请输入选择 (a/b/c/d/e/f): " choice

case $choice in
    a)
        read -p "请输入PDF文件路径: " file_path
        file_type="pdf"
        ;;
    b)
        read -p "请输入Word文件路径: " file_path
        file_type="docx"
        ;;
    c)
        read -p "请输入Excel文件路径: " file_path
        file_type="xlsx"
        ;;
    d)
        read -p "请输入PPT文件路径: " file_path
        file_type="pptx"
        ;;
    e)
        read -p "请输入图片文件路径: " file_path
        file_type="png"
        ;;
    f)
        read -p "请输入文件路径: " file_path
        ;;
    *)
        echo "无效选择"
        exit 1
        ;;
esac

# 检查文件是否存在
if [ ! -f "$file_path" ]; then
    echo "❌ 文件不存在: $file_path"
    exit 1
fi

echo ""
echo "解析模式："
echo "  1) traditional（传统模式，快速稳定）"
echo "  2) vlm（大模型模式，理解力强）"
echo ""
read -p "请选择模式 (1/2): " mode_choice

case $mode_choice in
    1)
        mode="traditional"
        ;;
    2)
        mode="vlm"
        ;;
    *)
        mode="traditional"
        ;;
esac

echo ""
echo "是否启用语义分片？(y/n)"
read -p "请选择: " chunking_choice

if [ "$chunking_choice" = "y" ]; then
    enable_chunking="true"
else
    enable_chunking="false"
fi

echo ""
echo "======================================"
echo "开始解析..."
echo "文件: $file_path"
echo "模式: $mode"
echo "分片: $enable_chunking"
echo "======================================"
echo ""

# 发送请求
start_time=$(date +%s)

response=$(curl -s -X POST "$API_URL/api/v1/parse" \
    -F "file=@$file_path" \
    -F "mode=$mode" \
    -F "enable_chunking=$enable_chunking")

end_time=$(date +%s)
duration=$((end_time - start_time))

# 保存完整响应
echo "$response" > test_result.json

# 显示结果
echo "解析完成！耗时: ${duration}秒"
echo ""

# 检查是否成功
success=$(echo "$response" | jq -r '.success')

if [ "$success" = "true" ]; then
    echo "✅ 解析成功！"
    echo ""
    
    # 显示统计信息
    markdown_length=$(echo "$response" | jq -r '.markdown | length')
    images_count=$(echo "$response" | jq -r '.images | length')
    chunks_count=$(echo "$response" | jq -r '.chunks | length')
    processing_time=$(echo "$response" | jq -r '.processing_time')
    
    echo "统计信息："
    echo "  - Markdown长度: $markdown_length 字符"
    echo "  - 提取图片: $images_count 张"
    echo "  - 语义分片: $chunks_count 个"
    echo "  - 处理时间: $processing_time 秒"
    echo ""
    
    # 保存Markdown
    echo "$response" | jq -r '.markdown' > parsed_result.md
    echo "✅ Markdown已保存到: parsed_result.md"
    echo "✅ 完整响应已保存到: test_result.json"
    echo ""
    
    # 显示前500字符
    echo "Markdown预览（前500字符）："
    echo "----------------------------------------"
    head -c 500 parsed_result.md
    echo ""
    echo "----------------------------------------"
    echo ""
    
    # 询问是否查看完整Markdown
    read -p "是否查看完整Markdown？(y/n): " view_full
    if [ "$view_full" = "y" ]; then
        less parsed_result.md
    fi
else
    echo "❌ 解析失败！"
    error=$(echo "$response" | jq -r '.error')
    echo "错误信息: $error"
fi

echo ""
echo "======================================"
echo "测试完成"
echo "======================================"
