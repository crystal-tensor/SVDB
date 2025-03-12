# 文本处理模块

import os
import PyPDF2
from sentence_transformers import SentenceTransformer
import numpy as np

def extract_text_from_pdf(pdf_path):
    """从PDF文件中提取文本内容
    
    Args:
        pdf_path: PDF文件路径
        
    Returns:
        text: 提取的文本内容
    """
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"提取PDF文本时出错: {e}")
        return None

def chunk_text(text, chunk_size=1000, overlap=200):
    """将长文本分割成小块，带有重叠部分
    
    Args:
        text: 输入文本
        chunk_size: 文本块大小
        overlap: 文本块重叠大小
        
    Returns:
        chunks: 文本块列表
    """
    chunks = []
    if len(text) <= chunk_size:
        chunks.append(text)
    else:
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            if end != len(text) and text[end] != ' ':
                # 尝试在空格处断开
                space_pos = text.rfind(' ', start, end)
                if space_pos != -1:
                    end = space_pos + 1
            chunks.append(text[start:end])
            start = end - overlap if end - overlap > start else end
    return chunks

def process_document(doc_path, hasher, chunk_size=1000, overlap=200):
    """处理文档并生成向量表示
    
    Args:
        doc_path: 文档路径
        hasher: 哈希器实例
        chunk_size: 文本块大小
        overlap: 文本块重叠大小
        
    Returns:
        chunks: 文本块列表
        embeddings: 向量嵌入列表
        pointers: 量子哈希指针列表
    """
    # 提取文本
    text = extract_text_from_pdf(doc_path)
    if not text:
        return [], [], []
    
    # 分割文本
    chunks = chunk_text(text, chunk_size, overlap)
    
    # 生成向量嵌入
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = model.encode(chunks)
    
    # 生成量子哈希微小指针
    pointers = []
    for chunk in chunks:
        pointer = hasher.hash_to_vector(chunk)
        pointers.append(pointer)
    
    return chunks, embeddings, pointers


def text_to_embedding(text, model=None):
    """将文本转换为向量嵌入
    
    Args:
        text: 输入文本
        model: 预训练模型（如果为None则加载默认模型）
        
    Returns:
        embedding: 向量嵌入
    """
    if model is None:
        model = SentenceTransformer('all-MiniLM-L6-v2')
    
    embedding = model.encode(text)
    return embedding