"""
Excel处理器
直接读取Excel文件并转换为Markdown表格
"""
from pathlib import Path
from typing import Literal, Dict, Any
from loguru import logger

from .base import BaseHandler
from ..core.result import ParseResult


class ExcelHandler(BaseHandler):
    """Excel处理器 - 直接读取结构化数据"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化Excel处理器
        
        Args:
            config: 配置字典
        """
        super().__init__(config)
        
        # 检查pandas和openpyxl是否可用
        self._check_dependencies()
    
    def _check_dependencies(self):
        """检查依赖是否可用"""
        try:
            import pandas
            import openpyxl
            logger.info("pandas and openpyxl are available")
        except ImportError as e:
            logger.warning(f"Excel dependencies not available: {e}")
            logger.warning("Please install: pip install pandas openpyxl")
    
    def parse(
        self,
        file_path: Path,
        mode: Literal["traditional", "vlm"] = "traditional"
    ) -> ParseResult:
        """
        解析Excel文档
        
        Args:
            file_path: 文件路径
            mode: 解析模式（traditional/vlm，对Excel无影响）
            
        Returns:
            ParseResult: 解析结果
        """
        logger.info(f"ExcelHandler开始解析: {file_path}")
        
        # 验证文件
        self._validate_file(file_path)
        
        try:
            # 读取所有sheet
            all_sheets = self._read_excel(file_path)
            
            # 转换为Markdown
            markdown_parts = []
            json_data = {"sheets": []}
            
            for sheet_name, df in all_sheets.items():
                # 1. 转换为Markdown表格
                md_table = self._df_to_markdown(df)
                markdown_parts.append(f"## {sheet_name}\n\n{md_table}\n")
                
                # 2. 保存JSON数据
                json_data["sheets"].append({
                    "name": sheet_name,
                    "rows": len(df),
                    "columns": list(df.columns),
                    "data": df.to_dict(orient="records")[:100]  # 限制数据量
                })
            
            markdown = "\n".join(markdown_parts)
            
            logger.info(f"ExcelHandler解析完成: {file_path}, 共 {len(all_sheets)} 个sheet")
            
            return ParseResult(
                markdown=markdown,
                json_data=json_data,
                metadata=self._get_metadata(
                    file_path,
                    parser="ExcelHandler",
                    sheets=list(all_sheets.keys()),
                    total_rows=sum(len(df) for df in all_sheets.values())
                )
            )
        
        except Exception as e:
            logger.error(f"Excel解析失败: {e}")
            return ParseResult(
                markdown="",
                metadata=self._get_metadata(
                    file_path,
                    parser="ExcelHandler",
                    error=str(e)
                )
            )
    
    def _read_excel(self, file_path: Path) -> Dict[str, Any]:
        """
        读取Excel文件的所有sheet
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            字典，key为sheet名，value为DataFrame
        """
        import pandas as pd
        
        try:
            # 读取所有sheet
            all_sheets = pd.read_excel(file_path, sheet_name=None)
            return all_sheets
        
        except Exception as e:
            logger.error(f"读取Excel失败: {e}")
            raise
    
    def _df_to_markdown(self, df) -> str:
        """
        将DataFrame转换为Markdown表格
        
        Args:
            df: pandas DataFrame
            
        Returns:
            Markdown表格字符串
        """
        try:
            # 使用tabulate转换为Markdown表格
            from tabulate import tabulate
            
            # 处理NaN值
            df_clean = df.fillna("")
            
            # 转换为Markdown
            md_table = tabulate(
                df_clean,
                headers='keys',
                tablefmt='pipe',
                showindex=False
            )
            
            return md_table
        
        except ImportError:
            # 如果tabulate不可用，使用pandas内置方法
            logger.warning("tabulate not available, using pandas to_markdown")
            return df.to_markdown(index=False)
        
        except Exception as e:
            logger.error(f"DataFrame转Markdown失败: {e}")
            # 降级：简单格式
            return self._simple_df_to_markdown(df)
    
    def _simple_df_to_markdown(self, df) -> str:
        """
        简单的DataFrame转Markdown（降级方案）
        
        Args:
            df: pandas DataFrame
            
        Returns:
            Markdown表格字符串
        """
        # 表头
        headers = "| " + " | ".join(str(col) for col in df.columns) + " |"
        separator = "| " + " | ".join("---" for _ in df.columns) + " |"
        
        # 数据行
        rows = []
        for _, row in df.iterrows():
            row_str = "| " + " | ".join(str(val) if pd.notna(val) else "" for val in row) + " |"
            rows.append(row_str)
        
        return "\n".join([headers, separator] + rows)


__all__ = ["ExcelHandler"]
