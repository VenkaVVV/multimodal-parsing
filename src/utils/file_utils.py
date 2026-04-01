"""
文件工具模块
提供文件操作相关的工具函数
"""
import os
import uuid
import shutil
from pathlib import Path
from typing import Union, Optional


def get_file_suffix(file_path: Union[str, Path]) -> str:
    """
    获取文件后缀（小写）
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件后缀，如 ".pdf"
    """
    return Path(file_path).suffix.lower()


def is_supported_format(file_path: Union[str, Path], supported_formats: list) -> bool:
    """
    检查文件格式是否支持
    
    Args:
        file_path: 文件路径
        supported_formats: 支持的格式列表
        
    Returns:
        是否支持
    """
    suffix = get_file_suffix(file_path)
    return suffix.lstrip(".") in supported_formats


def generate_unique_filename(original_filename: str) -> str:
    """
    生成唯一文件名
    
    Args:
        original_filename: 原始文件名
        
    Returns:
        唯一文件名
    """
    file_id = str(uuid.uuid4())
    suffix = Path(original_filename).suffix
    return f"{file_id}{suffix}"


def save_upload_file(
    file_content: bytes,
    original_filename: str,
    upload_dir: Union[str, Path]
) -> Path:
    """
    保存上传文件
    
    Args:
        file_content: 文件内容
        original_filename: 原始文件名
        upload_dir: 上传目录
        
    Returns:
        保存后的文件路径
    """
    upload_path = Path(upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)
    
    unique_filename = generate_unique_filename(original_filename)
    file_path = upload_path / unique_filename
    
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    return file_path


def clean_temp_file(file_path: Union[str, Path]):
    """
    清理临时文件
    
    Args:
        file_path: 文件路径
    """
    path = Path(file_path)
    if path.exists():
        path.unlink()


def clean_temp_dir(dir_path: Union[str, Path]):
    """
    清理临时目录
    
    Args:
        dir_path: 目录路径
    """
    path = Path(dir_path)
    if path.exists():
        shutil.rmtree(path)


def ensure_dir(dir_path: Union[str, Path]) -> Path:
    """
    确保目录存在
    
    Args:
        dir_path: 目录路径
        
    Returns:
        目录路径
    """
    path = Path(dir_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_size(file_path: Union[str, Path]) -> int:
    """
    获取文件大小（字节）
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件大小
    """
    return Path(file_path).stat().st_size


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小
    
    Args:
        size_bytes: 文件大小（字节）
        
    Returns:
        格式化后的字符串，如 "1.5 MB"
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


__all__ = [
    "get_file_suffix",
    "is_supported_format",
    "generate_unique_filename",
    "save_upload_file",
    "clean_temp_file",
    "clean_temp_dir",
    "ensure_dir",
    "get_file_size",
    "format_file_size",
]
