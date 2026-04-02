#!/bin/bash
# 测试新的VLM提示词

echo "=== 测试新的VLM提示词 ==="
echo "提示词已更新，包含："
echo "  - 图片类型识别（TABLE/FLOWCHART/CHART等）"
echo "  - 结构化输出（HTML/Mermaid/Markdown等）"
echo "  - 自检机制"
echo ""

# 测试API调用
echo "调用API（mode=smart）..."
curl -s -X POST "http://localhost:8000/api/v1/parse" \
  -F "file=@tests/data/待测试文档.pdf" \
  -F "mode=smart" > output/result-new-prompt.json

# 提取结果
python3 << 'EOF'
import json
with open('output/result-new-prompt.json') as f:
    d = json.load(f)

# 保存markdown
with open('output/result-new-prompt.md', 'w') as f:
    f.write(d['markdown'])

print(f"✅ 结果已保存")
print(f"   Parser: {d['metadata'].get('parser')}")
print(f"   VLM Regions: {d['metadata'].get('vlm_regions')}")
EOF

echo ""
echo "=== 检查新提示词的效果 ==="
echo "查找'图片类型'标识："
grep -c "图片类型" output/result-new-prompt.md

echo ""
echo "显示第一个VLM输出："
grep -A 20 "图片类型" output/result-new-prompt.md | head -25
