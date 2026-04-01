"""
异常定义模块
定义项目中所有自定义异常
"""


class MultimodalParserError(Exception):
    """基础异常类"""
    pass


# ==================== 文件相关异常 ====================

class FileError(MultimodalParserError):
    """文件错误基类"""
    pass


class FileNotFoundError(FileError):
    """文件不存在"""
    def __init__(self, file_path: str):
        self.file_path = file_path
        super().__init__(f"文件不存在: {file_path}")


class FileTooLargeError(FileError):
    """文件过大"""
    def __init__(self, file_path: str, size: int, max_size: int):
        self.file_path = file_path
        self.size = size
        self.max_size = max_size
        super().__init__(f"文件过大: {file_path} ({size} > {max_size})")


class UnsupportedFormatError(FileError):
    """不支持的文件格式"""
    def __init__(self, format: str):
        self.format = format
        super().__init__(f"不支持的文件格式: {format}")


# ==================== 解析相关异常 ====================

class ParseError(MultimodalParserError):
    """解析错误基类"""
    pass


class ConversionError(ParseError):
    """格式转换错误"""
    def __init__(self, source_format: str, target_format: str, reason: str = ""):
        self.source_format = source_format
        self.target_format = target_format
        message = f"格式转换失败: {source_format} -> {target_format}"
        if reason:
            message += f", 原因: {reason}"
        super().__init__(message)


class OCRError(ParseError):
    """OCR识别错误"""
    def __init__(self, reason: str = ""):
        message = "OCR识别失败"
        if reason:
            message += f", 原因: {reason}"
        super().__init__(message)


class TableRecognitionError(ParseError):
    """表格识别错误"""
    def __init__(self, reason: str = ""):
        message = "表格识别失败"
        if reason:
            message += f", 原因: {reason}"
        super().__init__(message)


class LayoutDetectionError(ParseError):
    """版面检测错误"""
    def __init__(self, reason: str = ""):
        message = "版面检测失败"
        if reason:
            message += f", 原因: {reason}"
        super().__init__(message)


# ==================== 处理器相关异常 ====================

class HandlerError(MultimodalParserError):
    """处理器错误基类"""
    pass


class HandlerNotFoundError(HandlerError):
    """处理器未找到"""
    def __init__(self, format: str):
        self.format = format
        super().__init__(f"未找到处理器: {format}")


class HandlerInitializationError(HandlerError):
    """处理器初始化错误"""
    def __init__(self, handler_name: str, reason: str = ""):
        self.handler_name = handler_name
        message = f"处理器初始化失败: {handler_name}"
        if reason:
            message += f", 原因: {reason}"
        super().__init__(message)


# ==================== 配置相关异常 ====================

class ConfigError(MultimodalParserError):
    """配置错误基类"""
    pass


class ConfigNotFoundError(ConfigError):
    """配置文件不存在"""
    def __init__(self, config_path: str):
        self.config_path = config_path
        super().__init__(f"配置文件不存在: {config_path}")


class ConfigValidationError(ConfigError):
    """配置验证错误"""
    def __init__(self, key: str, value: any, reason: str = ""):
        self.key = key
        self.value = value
        message = f"配置验证失败: {key}={value}"
        if reason:
            message += f", 原因: {reason}"
        super().__init__(message)


# ==================== API相关异常 ====================

class APIError(MultimodalParserError):
    """API错误基类"""
    pass


class RequestValidationError(APIError):
    """请求验证错误"""
    def __init__(self, reason: str = ""):
        message = "请求验证失败"
        if reason:
            message += f", 原因: {reason}"
        super().__init__(message)


class TaskNotFoundError(APIError):
    """任务不存在"""
    def __init__(self, task_id: str):
        self.task_id = task_id
        super().__init__(f"任务不存在: {task_id}")


# ==================== 导出所有异常 ====================

__all__ = [
    "MultimodalParserError",
    "FileError",
    "FileNotFoundError",
    "FileTooLargeError",
    "UnsupportedFormatError",
    "ParseError",
    "ConversionError",
    "OCRError",
    "TableRecognitionError",
    "LayoutDetectionError",
    "HandlerError",
    "HandlerNotFoundError",
    "HandlerInitializationError",
    "ConfigError",
    "ConfigNotFoundError",
    "ConfigValidationError",
    "APIError",
    "RequestValidationError",
    "TaskNotFoundError",
]
