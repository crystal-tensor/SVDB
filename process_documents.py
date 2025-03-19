# SVDB文档处理脚本：将PDF和DOC文件转换为向量数据并存储到StateVector_storageDB

import os
import sys
import numpy as np
import PyPDF2
import docx2txt
from sentence_transformers import SentenceTransformer
import time
import glob

# 导入SVDB模块
from SVDB import SVDB
from PTHash.pthash import PTHash
from StateVector_storage.vector_store import VectorStore
from Quan_Tiny_pointer_Hash_index.index_builder import HashIndexBuilder
from Grover.grover_search import GroverSearch
from metadata_index.metadata_store import MetadataStore
from statistics.performance_monitor import PerformanceMonitor
from index_update_log.log_manager import LogManager

# 设置数据库路径 - 使用新的StateVector_storageDB目录
db_dir = os.path.join(os.path.dirname(__file__), 'StateVector_storageDB')
os.makedirs(db_dir, exist_ok=True)
db_path = os.path.join(db_dir, 'vector_db.sqlite')

# 设置数据目录路径
data_dir = os.path.join(os.path.dirname(__file__), 'data')

# 文本处理函数
def extract_text_from_pdf(pdf_path):
    """从PDF文件中提取文本内容"""
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

def extract_text_from_docx(docx_path):
    """从DOCX文件中提取文本内容"""
    try:
        text = docx2txt.process(docx_path)
        return text
    except Exception as e:
        print(f"提取DOCX文本时出错: {e}")
        return None

def chunk_text(text, chunk_size=1000, overlap=200):
    """将长文本分割成小块，带有重叠部分"""
    chunks = []
    if not text:
        return chunks
        
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

# 处理单个文档的函数
def process_document(file_path, hasher, vector_store, index_builder, metadata_store, log_manager, model):
    """处理单个文档并存储向量数据"""
    print(f"\n处理文档: {os.path.basename(file_path)}")
    
    # 记录操作开始
    operation_id = log_manager.start_operation(f"process_{os.path.basename(file_path)}")
    
    # 根据文件类型提取文本
    file_ext = os.path.splitext(file_path)[1].lower()
    if file_ext == '.pdf':
        text = extract_text_from_pdf(file_path)
    elif file_ext in ['.doc', '.docx']:
        text = extract_text_from_docx(file_path)
    else:
        print(f"不支持的文件类型: {file_ext}")
        log_manager.end_operation(operation_id, status="failed")
        return None
    
    if not text:
        print("无法提取文本，跳过处理")
        log_manager.end_operation(operation_id, status="failed")
        return None
    
    # 分割文本
    print("分割文本...")
    chunks = chunk_text(text)
    print(f"共分割成 {len(chunks)} 个文本块")
    
    # 生成向量嵌入
    print("生成向量嵌入...")
    embeddings = model.encode(chunks)
    print(f"生成了 {len(embeddings)} 个向量嵌入")
    
    # 生成量子哈希微小指针
    print("生成量子哈希微小指针...")
    pointers = []
    for i, chunk in enumerate(chunks):
        print(f"处理文本块 {i+1}/{len(chunks)}...")
        pointer = hasher.hash_to_vector(chunk)
        pointers.append(pointer)
    print(f"生成了 {len(pointers)} 个量子哈希微小指针")
    
    # 存储向量
    doc_id = vector_store.store_vectors(embeddings, pointers)
    print(f"向量已存储，文档ID: {doc_id}")
    
    # 构建索引
    index_builder.build_index(doc_id, pointers)
    print("索引已构建")
    
    # 存储元数据
    metadata = {
        "type": "document",
        "path": file_path,
        "filename": os.path.basename(file_path),
        "chunks": len(chunks),
        "timestamp": log_manager.get_current_time()
    }
    metadata_store.store(doc_id, metadata, chunks)
    print("元数据已存储")
    
    # 记录操作完成
    log_manager.end_operation(operation_id, status="success")
    
    return doc_id

# 主函数：处理所有文档
def process_all_documents():
    print("\n===== SVDB批量文档处理：将PDF和DOC文件转换为向量数据 =====")
    
    # 步骤1：初始化SVDB组件
    print("\n步骤1: 初始化SVDB组件")
    hasher = PTHash(num_qubits=8, depth=3)
    vector_store = VectorStore(db_path)
    log_manager = LogManager(db_path)
    index_builder = HashIndexBuilder(hasher, log_manager=log_manager)
    metadata_store = MetadataStore(db_path)
    performance_monitor = PerformanceMonitor()
    
    # 启动性能监控
    performance_monitor.start_monitoring()
    
    # 步骤2：加载模型
    print("\n步骤2: 加载文本嵌入模型")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # 步骤3：查找所有PDF和DOC文件
    print("\n步骤3: 查找所有PDF和DOC文件")
    pdf_files = glob.glob(os.path.join(data_dir, "*.pdf"))
    doc_files = glob.glob(os.path.join(data_dir, "*.doc*"))
    all_files = pdf_files + doc_files
    print(f"找到 {len(all_files)} 个文件需要处理")
    
    # 步骤4：处理所有文件
    print("\n步骤4: 处理所有文件")
    processed_docs = []
    for file_path in all_files:
        doc_id = process_document(
            file_path, hasher, vector_store, index_builder, 
            metadata_store, log_manager, model
        )
        if doc_id:
            processed_docs.append((doc_id, os.path.basename(file_path)))
    
    # 步骤5：显示处理结果
    print("\n步骤5: 处理结果")
    print(f"成功处理了 {len(processed_docs)} 个文档:")
    for doc_id, filename in processed_docs:
        print(f"- {filename} (ID: {doc_id})")
    
    # 步骤6：显示性能统计
    print("\n步骤6: 显示性能统计")
    stats = performance_monitor.get_stats()
    print("性能统计:")
    print(f"- 总处理文档数: {len(processed_docs)}")
    print(f"- 总存储项目数: {stats.get('total_items', 0)}")
    print(f"- 当前内存使用: {stats.get('current_memory', 0):.2f} MB")
    
    # 停止性能监控
    performance_monitor.stop_monitoring()
    
    print("\n===== 批量文档处理完成 =====")

if __name__ == "__main__":
    process_all_documents()