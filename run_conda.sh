#!/bin/bash
# 使用conda环境启动服务

echo "激活conda环境..."
conda activate multimodal-parsing

echo "启动服务..."
python start.py
