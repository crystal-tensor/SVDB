# SVDB - 量子向量数据库

__version__ = '0.1.0'

import sys
import os

# 添加父目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from PTHash.pthash import PTHash
from StateVector_storage.vector_store import VectorStore
from Quan_Tiny_pointer_Hash_index.index_builder import HashIndexBuilder
from Grover.grover_search import GroverSearch
from metadata_index.metadata_store import MetadataStore
from statistics.performance_monitor import PerformanceMonitor
from index_update_log.log_manager import LogManager

class SVDB:
    """量子向量数据库主类，整合所有模块功能"""
    
    def __init__(self, db_path, num_qubits=8, depth=3, clear_existing=False):
        """初始化量子向量数据库
        
        Args:
            db_path: 数据库存储路径
            num_qubits: 量子比特数量
            depth: 量子电路深度
            clear_existing: 是否清除现有数据库内容
        """
        self.db_path = db_path
        self.num_qubits = num_qubits
        self.depth = depth
        
        # 初始化各模块
        self.hasher = PTHash(num_qubits=num_qubits, depth=depth)
        self.vector_store = VectorStore(db_path, clear_existing=clear_existing)
        self.index_builder = HashIndexBuilder(self.hasher)
        self.grover_search = GroverSearch()
        self.metadata_store = MetadataStore(db_path, clear_existing=clear_existing)
        self.performance_monitor = PerformanceMonitor()
        self.log_manager = LogManager(db_path)
        
        # 启动性能监控
        self.performance_monitor.start_monitoring()
    
    def store_document(self, doc_path, chunk_size=1000, overlap=200):
        """存储文档并建立索引
        
        Args:
            doc_path: 文档路径
            chunk_size: 文本分块大小
            overlap: 文本分块重叠大小
            
        Returns:
            doc_id: 文档ID
        """
        # 记录操作开始
        operation_id = self.log_manager.start_operation("store_document")
        
        # 处理文档
        from utils.data_processors.text_processor import process_document
        chunks, embeddings, pointers = process_document(doc_path, self.hasher, chunk_size, overlap)
        
        # 存储向量
        doc_id = self.vector_store.store_vectors(embeddings, pointers)
        
        # 构建索引
        self.index_builder.build_index(doc_id, pointers)
        
        # 存储元数据
        metadata = {
            "type": "document",
            "path": doc_path,
            "chunks": len(chunks),
            "timestamp": self.log_manager.get_current_time()
        }
        self.metadata_store.store(doc_id, metadata, chunks)
        
        # 记录操作完成
        self.log_manager.end_operation(operation_id, status="success")
        
        # 更新统计信息
        self.performance_monitor.update_stats("document_stored")
        
        return doc_id
    
    def search(self, query, top_k=5, use_quantum=True):
        """搜索数据库
        
        Args:
            query: 搜索查询
            top_k: 返回结果数量
            use_quantum: 是否使用量子Grover算法
            
        Returns:
            results: 搜索结果列表
        """
        # 记录操作开始
        operation_id = self.log_manager.start_operation("search")
        
        # 执行搜索
        if use_quantum:
            results = self.grover_search.search(query, self.vector_store, top_k)
        else:
            results = self.vector_store.classical_search(query, top_k)
        
        # 记录操作完成
        self.log_manager.end_operation(operation_id, status="success")
        
        # 更新统计信息
        self.performance_monitor.update_stats("search_performed")
        
        return results
    
    def close(self):
        """关闭数据库连接"""
        self.vector_store.close()
        self.metadata_store.close()
        self.log_manager.close()
        self.performance_monitor.stop_monitoring()