#!/bin/bash
# 激活虚拟环境并启动服务

echo "激活虚拟环境..."
source venv/bin/activate

echo "启动服务..."
python start.py
