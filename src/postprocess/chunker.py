"""
语义分片模块
使用LangChain对Markdown进行语义分片
"""
from typing import List, Dict, Any
from loguru import logger

from ..core.result import Chunk


class Chunker:
    """语义分片器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化分片器
        
        Args:
            config: 配置字典
        """
        self.chunk_size = config.get("chunk_size", 512)
        self.overlap = config.get("overlap", 64)
        
        logger.info(f"Chunker initialized, chunk_size={self.chunk_size}, overlap={self.overlap}")
    
    def chunk(self, markdown: str) -> List[Chunk]:
        """
        对Markdown进行语义分片
        
        Args:
            markdown: Markdown文本
            
        Returns:
            分片列表
        """
        if not markdown or not markdown.strip():
            return []
        
        try:
            # 尝试使用LangChain
            return self._chunk_with_langchain(markdown)
        
        except ImportError:
            logger.warning("LangChain not available, using simple chunking")
            return self._simple_chunk(markdown)
        
        except Exception as e:
            logger.error(f"语义分片失败: {e}")
            return self._simple_chunk(markdown)
    
    def _chunk_with_langchain(self, markdown: str) -> List[Chunk]:
        """
        使用LangChain进行分片
        
        Args:
            markdown: Markdown文本
            
        Returns:
            分片列表
        """
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        
        # 创建分片器
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.overlap,
            separators=["\n##", "\n###", "\n\n", "\n", " "],
            keep_separator=True
        )
        
        # 执行分片
        texts = splitter.split_text(markdown)
        
        # 转换为Chunk对象
        chunks = []
        for i, text in enumerate(texts):
            chunks.append(Chunk(
                id=i,
                content=text,
                tokens=len(text.split()),  # 简单估算
                metadata={
                    "char_count": len(text),
                    "word_count": len(text.split())
                }
            ))
        
        logger.info(f"LangChain分片完成，共 {len(chunks)} 个分片")
        return chunks
    
    def _simple_chunk(self, markdown: str) -> List[Chunk]:
        """
        简单分片（降级方案）
        
        Args:
            markdown: Markdown文本
            
        Returns:
            分片列表
        """
        # 按段落分割
        paragraphs = markdown.split("\n\n")
        
        chunks = []
        current_chunk = []
        current_size = 0
        chunk_id = 0
        
        for para in paragraphs:
            para_size = len(para.split())
            
            # 如果当前段落太大，单独作为一个chunk
            if para_size > self.chunk_size:
                # 先保存当前chunk
                if current_chunk:
                    chunks.append(Chunk(
                        id=chunk_id,
                        content="\n\n".join(current_chunk),
                        tokens=current_size
                    ))
                    chunk_id += 1
                    current_chunk = []
                    current_size = 0
                
                # 保存大段落
                chunks.append(Chunk(
                    id=chunk_id,
                    content=para,
                    tokens=para_size
                ))
                chunk_id += 1
            
            # 否则添加到当前chunk
            else:
                if current_size + para_size > self.chunk_size:
                    # 当前chunk已满，保存
                    if current_chunk:
                        chunks.append(Chunk(
                            id=chunk_id,
                            content="\n\n".join(current_chunk),
                            tokens=current_size
                        ))
                        chunk_id += 1
                    
                    # 开始新chunk（考虑overlap）
                    current_chunk = [para]
                    current_size = para_size
                else:
                    current_chunk.append(para)
                    current_size += para_size
        
        # 保存最后一个chunk
        if current_chunk:
            chunks.append(Chunk(
                id=chunk_id,
                content="\n\n".join(current_chunk),
                tokens=current_size
            ))
        
        logger.info(f"简单分片完成，共 {len(chunks)} 个分片")
        return chunks


__all__ = ["Chunker"]
