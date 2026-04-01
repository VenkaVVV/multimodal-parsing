#!/usr/bin/env python3
"""
MinerU模型下载脚本 - 从正确的HuggingFace仓库下载
"""
import os
import sys
from pathlib import Path
from huggingface_hub import snapshot_download

def download_mineru_models():
    """下载MinerU所需的模型"""

    # 模型目录
    models_dir = Path.home() / ".mineru" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    print(f"模型目录: {models_dir}")
    print("\n开始下载MinerU模型...")

    try:
        # MinerU的模型在 opendatalab/PDF-Extract-Kit-1.0 仓库
        print("\n从 opendatalab/PDF-Extract-Kit-1.0 下载模型...")

        model_dir = snapshot_download(
            repo_id="opendatalab/PDF-Extract-Kit-1.0",
            local_dir=models_dir,
            allow_patterns=["models/*"]
        )

        print(f"\n✅ 模型下载完成: {model_dir}")

        # 列出下载的模型
        print("\n已下载的模型:")
        for item in models_dir.rglob("*.pt"):
            print(f"  - {item.relative_to(models_dir)}")
        for item in models_dir.rglob("*.pth"):
            print(f"  - {item.relative_to(models_dir)}")
        for item in models_dir.rglob("*.onnx"):
            print(f"  - {item.relative_to(models_dir)}")

        return True

    except Exception as e:
        print(f"\n❌ 下载失败: {e}")
        print("\n备用方案：")
        print("1. 访问 https://huggingface.co/opendatalab/PDF-Extract-Kit-1.0")
        print("2. 下载 models 目录")
        print(f"3. 解压到 {models_dir}")
        return False

if __name__ == "__main__":
    success = download_mineru_models()
    sys.exit(0 if success else 1)
