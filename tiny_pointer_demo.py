# SVDB应用案例：处理Tiny Pointer.pdf文档并使用量子搜索

import os
import sys
import numpy as np
import PyPDF2
from sentence_transformers import SentenceTransformer
import time

# 导入SVDB模块
from SVDB import SVDB
from SVDB.PTHash.pthash import PTHash
from SVDB.StateVector_storage.vector_store import VectorStore
from SVDB.Quan_Tiny_pointer_Hash_index.index_builder import HashIndexBuilder
from SVDB.Grover.grover_search import GroverSearch
from SVDB.metadata_index.metadata_store import MetadataStore
from SVDB.statistics.performance_monitor import PerformanceMonitor
from SVDB.index_update_log.log_manager import LogManager

# 设置数据库路径
db_path = os.path.join(os.path.dirname(__file__), 'data', 'tiny_pointer_db')
os.makedirs(os.path.dirname(db_path), exist_ok=True)

# 设置PDF文件路径
pdf_path = os.path.join(os.path.dirname(__file__), 'Tiny Pointer.pdf')

# 自定义文本处理函数
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

def chunk_text(text, chunk_size=1000, overlap=200):
    """将长文本分割成小块，带有重叠部分"""
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

# 主函数：处理PDF并使用量子搜索
def process_and_search():
    print("\n===== SVDB应用案例：处理Tiny Pointer.pdf文档并使用量子搜索 =====")
    
    # 步骤1：初始化SVDB组件
    print("\n步骤1: 初始化SVDB组件")
    hasher = PTHash(num_qubits=8, depth=3)
    vector_store = VectorStore(db_path)
    index_builder = HashIndexBuilder(hasher)
    metadata_store = MetadataStore(db_path)
    performance_monitor = PerformanceMonitor()
    log_manager = LogManager(db_path)
    
    # 启动性能监控
    performance_monitor.start_monitoring()
    
    # 步骤2：处理PDF文档
    print("\n步骤2: 处理PDF文档")
    # 记录操作开始
    operation_id = log_manager.start_operation("process_pdf")
    
    # 提取文本
    print("提取文本...")
    text = extract_text_from_pdf(pdf_path)
    if not text:
        print("无法提取文本，退出处理")
        return
    
    # 分割文本
    print("分割文本...")
    chunks = chunk_text(text)
    print(f"共分割成 {len(chunks)} 个文本块")
    
    # 生成向量嵌入
    print("生成向量嵌入...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
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
    
    # 步骤3：存储向量和构建索引
    print("\n步骤3: 存储向量和构建索引")
    # 存储向量
    doc_id = vector_store.store_vectors(embeddings, pointers)
    print(f"向量已存储，文档ID: {doc_id}")
    
    # 构建索引
    index_builder.build_index(doc_id, pointers)
    print("索引已构建")
    
    # 存储元数据
    metadata = {
        "type": "document",
        "path": pdf_path,
        "chunks": len(chunks),
        "timestamp": log_manager.get_current_time()
    }
    metadata_store.store(doc_id, metadata, chunks)
    print("元数据已存储")
    
    # 记录操作完成
    log_manager.end_operation(operation_id, status="success")
    
    # 更新统计信息
    performance_monitor.update_stats("document_stored")
    
    # 步骤4：使用Grover算法搜索
    print("\n步骤4: 使用Grover算法搜索'lowest-common ancestor'")
    # 初始化Grover搜索
    grover_search = GroverSearch(backend='auto')
    
    # 生成查询向量
    query_text = "lowest-common ancestor"
    query_vector = model.encode(query_text)
    
    # 记录搜索操作
    search_operation_id = log_manager.start_operation("search")
    
    # 执行搜索
    print(f"执行搜索: '{query_text}'")
    start_time = time.time()
    results = grover_search.search(query_vector, vector_store, top_k=5)
    search_time = time.time() - start_time
    
    # 显示结果
    print(f"\n搜索完成，耗时: {search_time:.3f}秒")
    print("搜索结果:")
    for i, (item_id, score) in enumerate(results):
        print(f"\n结果 {i+1}:")
        print(f"项目ID: {item_id}")
        print(f"相似度: {score:.4f}")
        
        # 获取元数据和内容
        metadata_info = metadata_store.get(item_id)
        if metadata_info:
            metadata_dict, content = metadata_info
            if content and isinstance(content, list) and len(content) > 0:
                # 显示内容片段
                content_text = content[0] if isinstance(content, list) else content
                print(f"内容片段: {content_text[:300]}...")
    
    # 记录搜索操作完成
    log_manager.end_operation(search_operation_id, status="success")
    
    # 更新统计信息
    performance_monitor.update_stats("search_performed")
    
    # 步骤5：显示性能统计
    print("\n步骤5: 显示性能统计")
    stats = performance_monitor.get_stats()
    print("性能统计:")
    print(f"- 总查询次数: {stats.get('total_queries', 0)}")
    print(f"- 平均查询时间: {stats.get('avg_query_time', 0):.3f} 秒")
    print(f"- 总存储项目数: {stats.get('total_items', 0)}")
    print(f"- 当前内存使用: {stats.get('current_memory', 0):.2f} MB")
    
    # 停止性能监控
    performance_monitor.stop_monitoring()
    
    print("\n===== 应用案例演示完成 =====")

if __name__ == "__main__":
    process_and_search()