"""
配置管理模块
支持YAML配置文件和环境变量覆盖
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv


class Config:
    """配置管理类"""
    
    def __init__(self, config_path: str = "config/default.yaml"):
        """
        初始化配置
        
        Args:
            config_path: 配置文件路径
        """
        # 加载环境变量
        load_dotenv()
        
        # 加载配置文件
        self.config = self._load_config(config_path)
        
        # 环境变量覆盖
        self._override_from_env()
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        加载YAML配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置字典
        """
        path = Path(config_path)
        
        if not path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        
        return config
    
    def _override_from_env(self):
        """从环境变量覆盖配置"""
        # 应用配置
        if os.getenv("PARSER_MODE"):
            self.config["parser"]["mode"] = os.getenv("PARSER_MODE")
        
        if os.getenv("MAX_FILE_SIZE"):
            self.config["parser"]["max_file_size"] = int(os.getenv("MAX_FILE_SIZE"))
        
        # MinerU配置
        if os.getenv("MINERU_DEVICE"):
            self.config["mineru"]["device"] = os.getenv("MINERU_DEVICE")
        
        if os.getenv("MINERU_MODELS_DIR"):
            self.config["mineru"]["models_dir"] = os.getenv("MINERU_MODELS_DIR")
        
        # LibreOffice配置
        if os.getenv("LIBREOFFICE_PATH"):
            self.config["libreoffice"]["path"] = os.getenv("LIBREOFFICE_PATH")
        
        if os.getenv("LIBREOFFICE_TIMEOUT"):
            self.config["libreoffice"]["timeout"] = int(os.getenv("LIBREOFFICE_TIMEOUT"))
        
        # 分片配置
        if os.getenv("CHUNKING_ENABLED"):
            self.config["chunking"]["enabled"] = os.getenv("CHUNKING_ENABLED").lower() == "true"
        
        if os.getenv("CHUNK_SIZE"):
            self.config["chunking"]["chunk_size"] = int(os.getenv("CHUNK_SIZE"))
        
        # API配置
        if os.getenv("API_HOST"):
            self.config["api"]["host"] = os.getenv("API_HOST")
        
        if os.getenv("API_PORT"):
            self.config["api"]["port"] = int(os.getenv("API_PORT"))
        
        # 日志配置
        if os.getenv("LOG_LEVEL"):
            self.config["logging"]["level"] = os.getenv("LOG_LEVEL")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项（支持点号分隔的嵌套key）
        
        Args:
            key: 配置键，如 "parser.mode"
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split(".")
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """
        设置配置项
        
        Args:
            key: 配置键
            value: 配置值
        """
        keys = key.split(".")
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def __getitem__(self, key: str) -> Any:
        """支持字典式访问"""
        return self.get(key)
    
    def __setitem__(self, key: str, value: Any):
        """支持字典式设置"""
        self.set(key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.config.copy()


# 全局配置实例
_config: Optional[Config] = None


def get_config(config_path: str = "config/default.yaml") -> Config:
    """
    获取全局配置实例（单例模式）
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        Config实例
    """
    global _config
    
    if _config is None:
        _config = Config(config_path)
    
    return _config
