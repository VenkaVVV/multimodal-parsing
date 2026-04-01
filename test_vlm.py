#!/usr/bin/env python3
"""
测试VLM表格识别功能
"""
import sys
sys.path.insert(0, '/Users/venka/Documents/code/project/multimodal-parsing')

from pathlib import Path
from src.handlers.smart_document_handler import SmartDocumentHandler

def test_vlm_config():
    """测试VLM配置"""
    handler = SmartDocumentHandler({})
    
    print("=" * 60)
    print("VLM配置信息：")
    print(f"  API Key: {handler.vlm_api_key[:20]}...")
    print(f"  Model: {handler.vlm_model}")
    print(f"  Base URL: {handler.vlm_base_url}")
    print("=" * 60)
    
    return handler

def test_table_recognition(handler, image_path):
    """测试表格识别"""
    print(f"\n测试表格识别: {image_path}")
    
    img_path = Path(image_path)
    if not img_path.exists():
        print(f"❌ 图片不存在: {image_path}")
        return
    
    result = handler._recognize_table_with_vlm(img_path)
    
    if result:
        print("✅ 表格识别成功！")
        print("\n识别结果：")
        print("-" * 60)
        print(result)
        print("-" * 60)
    else:
        print("❌ 表格识别失败")

def test_image_description(handler, image_path):
    """测试图片描述"""
    print(f"\n测试图片描述: {image_path}")
    
    img_path = Path(image_path)
    if not img_path.exists():
        print(f"❌ 图片不存在: {image_path}")
        return
    
    result = handler._describe_image_with_vlm(img_path)
    
    if result:
        print("✅ 图片描述成功！")
        print(f"\n描述: {result}")
    else:
        print("❌ 图片描述失败")

if __name__ == "__main__":
    # 测试VLM配置
    handler = test_vlm_config()
    
    # 查找测试图片
    output_dir = Path("output/mineru_temp/待测试文档/ocr/images")
    
    if output_dir.exists():
        images = list(output_dir.glob("*.jpg"))
        print(f"\n找到 {len(images)} 张图片")
        
        if images:
            # 测试第一张图片
            test_image = images[0]
            print(f"\n使用测试图片: {test_image}")
            
            # 测试表格识别
            test_table_recognition(handler, test_image)
            
            # 测试图片描述
            test_image_description(handler, test_image)
    else:
        print(f"\n⚠️  输出目录不存在: {output_dir}")
        print("请先运行MinerU生成图片")
