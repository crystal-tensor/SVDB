# SVDB应用案例：处理Tiny Pointer.pdf文档

import os
import sys
import numpy as np
from sentence_transformers import SentenceTransformer

# 添加父目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# 导入SVDB模块
from SVDB import SVDB
from PTHash.pthash import PTHash
from StateVector_storage.vector_store import VectorStore
from Quan_Tiny_pointer_Hash_index.index_builder import HashIndexBuilder
from statistics.performance_monitor import PerformanceMonitor

# 设置数据库路径
db_path = os.path.join(os.path.dirname(__file__), 'data', 'tiny_pointer_db')
os.makedirs(os.path.dirname(db_path), exist_ok=True)

# 设置PDF文件路径
pdf_path = os.path.join(os.path.dirname(__file__), 'data', '20241206-亚洲艺术品金融商学院-中国艺术品金融行业市场发展蓝皮书（2024）.pdf')

def process_tiny_pointer_pdf():
    """处理Tiny Pointer.pdf文档并存储到SVDB"""
    print("初始化SVDB...")
    db = SVDB(db_path, num_qubits=8, depth=3, clear_existing=True)
    
    # 存储文档
    print("\n步骤1: 存储PDF文档到SVDB")
    doc_id = db.store_document(pdf_path)
    print(f"文档已存储，ID: {doc_id}")
    
    # 查询示例
    print("\n步骤2: 使用Grover算法搜索'艺术品市场的价值发展：整体价 值规律以及发展趋势'")
    # 先将查询文本转换为向量
    from utils.data_processors.text_processor import text_to_embedding
    query_text = "艺术品市场的价值发展：整体价 值规律以及发展趋势"
    query_vector = text_to_embedding(query_text)
    
    results = db.search(
        query=query_vector,  # 使用向量而非文本字符串
        top_k=5,
        use_quantum=True  # 使用量子Grover算法
    )
    
    # 显示结果
    print("\n搜索结果:")
    for i, result in enumerate(results):
        print(f"\n结果 {i+1}:")
        # 检查结果格式，适应不同的返回格式
        if isinstance(result, tuple):
            if len(result) == 2:
                item_id, score = result
                print(f"项目ID: {item_id}")
                print(f"相似度: {score:.4f}")
                # 获取元数据和完整内容
                metadata_info = db.metadata_store.retrieve(item_id)
                if metadata_info:
                    metadata, content = metadata_info
                    print(f"元数据: {metadata}")
                    if content:
                        if isinstance(content, list):
                            # 如果内容是列表，显示第一个元素的完整内容
                            print(f"\n文摘内容:\n{content[0]}")
                        else:
                            # 否则直接显示完整内容
                            print(f"\n文摘内容:\n{content}")
                    else:
                        print("无内容数据")
            elif len(result) == 3:
                item_id, score, metadata = result
                print(f"项目ID: {item_id}")
                print(f"相似度: {score:.4f}")
                if metadata and isinstance(metadata, dict):
                    print(f"元数据: {metadata}")
                    if 'text' in metadata:
                        print(f"\n文摘内容:\n{metadata['text']}")
                # 尝试获取更完整的内容
                metadata_info = db.metadata_store.retrieve(item_id)
                if metadata_info and not ('text' in metadata if isinstance(metadata, dict) else False):
                    _, content = metadata_info
                    if content:
                        if isinstance(content, list):
                            print(f"\n文摘内容:\n{content[0]}")
                        else:
                            print(f"\n文摘内容:\n{content}")
        else:
            # 如果结果不是元组，直接打印
            print(f"结果: {result}")
    
    # 获取性能统计
    stats = db.performance_monitor.get_stats()
    print("\n性能统计:")
    print(f"- 总查询次数: {stats['total_queries']}")
    print(f"- 平均查询时间: {stats['avg_query_time']:.3f} 秒")
    print(f"- 总存储项目数: {stats['total_items']}")
    
    # 关闭数据库
    db.close()

if __name__ == "__main__":
    process_tiny_pointer_pdf()