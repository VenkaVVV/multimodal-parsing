#!/bin/bash
# 检查测试结果文件

echo "=========================================="
echo "检查测试结果文件"
echo "=========================================="

echo ""
echo "【Markdown文件】"
echo "----------------------------------------"

if [ -f "output/traditional_result.md" ]; then
    size=$(wc -c < output/traditional_result.md)
    lines=$(wc -l < output/traditional_result.md)
    echo "✅ traditional_result.md: $size 字节, $lines 行"
else
    echo "❌ traditional_result.md: 不存在"
fi

if [ -f "output/smart_result.md" ]; then
    size=$(wc -c < output/smart_result.md)
    lines=$(wc -l < output/smart_result.md)
    echo "✅ smart_result.md: $size 字节, $lines 行"
else
    echo "❌ smart_result.md: 不存在"
fi

echo ""
echo "【JSON文件】"
echo "----------------------------------------"

if [ -f "output/traditional_result.json" ]; then
    size=$(wc -c < output/traditional_result.json)
    echo "✅ traditional_result.json: $size 字节"
    
    # 检查JSON结构
    echo "   内容摘要:"
    jq '{
      success: .success,
      markdown_length: (.markdown | length),
      images_count: (.images | length),
      parser: .metadata.parser
    }' output/traditional_result.json | sed 's/^/   /'
else
    echo "❌ traditional_result.json: 不存在"
fi

if [ -f "output/smart_result.json" ]; then
    size=$(wc -c < output/smart_result.json)
    echo "✅ smart_result.json: $size 字节"
    
    # 检查JSON结构
    echo "   内容摘要:"
    jq '{
      success: .success,
      markdown_length: (.markdown | length),
      images_count: (.images | length),
      parser: .metadata.parser
    }' output/smart_result.json | sed 's/^/   /'
else
    echo "❌ smart_result.json: 不存在"
fi

echo ""
echo "【MinerU输出】"
echo "----------------------------------------"

if [ -d "output/mineru_temp" ]; then
    echo "✅ mineru_temp目录存在"
    
    # 查找PDF名称
    pdf_name=$(ls output/mineru_temp/ 2>/dev/null | head -1)
    if [ -n "$pdf_name" ]; then
        echo "   文档: $pdf_name"
        
        ocr_dir="output/mineru_temp/$pdf_name/ocr"
        
        # 检查Markdown
        if [ -f "$ocr_dir/${pdf_name}.md" ]; then
            size=$(wc -c < "$ocr_dir/${pdf_name}.md")
            echo "   ✅ Markdown: $size 字节"
        fi
        
        # 检查图片
        if [ -d "$ocr_dir/images" ]; then
            count=$(ls "$ocr_dir/images"/*.jpg 2>/dev/null | wc -l)
            echo "   ✅ 图片: $count 张"
        fi
        
        # 检查JSON
        if [ -f "$ocr_dir/${pdf_name}_model.json" ]; then
            size=$(wc -c < "$ocr_dir/${pdf_name}_model.json")
            echo "   ✅ model.json: $size 字节"
        fi
        
        if [ -f "$ocr_dir/${pdf_name}_middle.json" ]; then
            size=$(wc -c < "$ocr_dir/${pdf_name}_middle.json")
            echo "   ✅ middle.json: $size 字节"
        fi
    fi
else
    echo "❌ mineru_temp目录不存在"
fi

echo ""
echo "【文件对比】"
echo "----------------------------------------"

if [ -f "output/traditional_result.md" ] && [ -f "output/smart_result.md" ]; then
    trad_len=$(wc -c < output/traditional_result.md)
    smart_len=$(wc -c < output/smart_result.md)
    
    echo "Traditional: $trad_len 字节"
    echo "Smart:       $smart_len 字节"
    
    if [ "$smart_len" -gt "$trad_len" ]; then
        diff=$((smart_len - trad_len))
        echo "差异:       +$diff 字节 (smart更丰富)"
    elif [ "$smart_len" -lt "$trad_len" ]; then
        diff=$((trad_len - smart_len))
        echo "差异:       -$diff 字节 (traditional更长)"
    else
        echo "差异:       0 字节 (相同)"
    fi
fi

echo ""
echo "=========================================="
echo "检查完成"
echo "=========================================="
