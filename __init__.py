# SVDB - 量子向量数据库

__version__ = '0.1.0'

from SVDB.PTHash.pthash import PTHash
from SVDB.StateVector_storage.vector_store import VectorStore
from SVDB.Quan_Tiny_pointer_Hash_index.index_builder import HashIndexBuilder
from SVDB.Grover.grover_search import GroverSearch
from SVDB.metadata_index.metadata_store import MetadataStore
from SVDB.statistics.performance_monitor import PerformanceMonitor
from SVDB.index_update_log.log_manager import LogManager

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
        self.log_manager = LogManager(db_path)
        self.index_builder = HashIndexBuilder(self.hasher, log_manager=self.log_manager)
        self.grover_search = GroverSearch()
        self.metadata_store = MetadataStore(db_path, clear_existing=clear_existing)
        self.performance_monitor = PerformanceMonitor()
        
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
        from SVDB.utils.data_processors.text_processor import process_document
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
    
    def store_image(self, image_path):
        """存储图像并建立索引
        
        Args:
            image_path: 图像路径
            
        Returns:
            image_id: 图像ID
        """
        # 记录操作开始
        operation_id = self.log_manager.start_operation("store_image")
        
        # 处理图像
        from SVDB.utils.data_processors.image_processor import process_image
        features, pointers = process_image(image_path, self.hasher)
        
        # 存储向量
        image_id = self.vector_store.store_vectors([features], [pointers])
        
        # 构建索引
        self.index_builder.build_index(image_id, [pointers])
        
        # 存储元数据
        metadata = {
            "type": "image",
            "path": image_path,
            "timestamp": self.log_manager.get_current_time()
        }
        self.metadata_store.store(image_id, metadata)
        
        # 记录操作完成
        self.log_manager.end_operation(operation_id, status="success")
        
        # 更新统计信息
        self.performance_monitor.update_stats("image_stored")
        
        return image_id
    
    def store_video(self, video_path, frame_interval=1):
        """存储视频并建立索引
        
        Args:
            video_path: 视频路径
            frame_interval: 帧间隔
            
        Returns:
            video_id: 视频ID
        """
        # 记录操作开始
        operation_id = self.log_manager.start_operation("store_video")
        
        # 处理视频
        from SVDB.utils.data_processors.video_processor import process_video
        frames, embeddings, pointers = process_video(video_path, self.hasher, frame_interval)
        
        # 存储向量
        video_id = self.vector_store.store_vectors(embeddings, pointers)
        
        # 构建索引
        self.index_builder.build_index(video_id, pointers)
        
        # 存储元数据
        metadata = {
            "type": "video",
            "path": video_path,
            "frames": len(frames),
            "timestamp": self.log_manager.get_current_time()
        }
        self.metadata_store.store(video_id, metadata, frames)
        
        # 记录操作完成
        self.log_manager.end_operation(operation_id, status="success")
        
        # 更新统计信息
        self.performance_monitor.update_stats("video_stored")
        
        return video_id
    
    def store_audio(self, audio_path):
        """存储音频并建立索引
        
        Args:
            audio_path: 音频路径
            
        Returns:
            audio_id: 音频ID
        """
        # 记录操作开始
        operation_id = self.log_manager.start_operation("store_audio")
        
        # 处理音频
        from SVDB.utils.data_processors.audio_processor import process_audio
        segments, embeddings, pointers = process_audio(audio_path, self.hasher)
        
        # 存储向量
        audio_id = self.vector_store.store_vectors(embeddings, pointers)
        
        # 构建索引
        self.index_builder.build_index(audio_id, pointers)
        
        # 存储元数据
        metadata = {
            "type": "audio",
            "path": audio_path,
            "segments": len(segments),
            "timestamp": self.log_manager.get_current_time()
        }
        self.metadata_store.store(audio_id, metadata, segments)
        
        # 记录操作完成
        self.log_manager.end_operation(operation_id, status="success")
        
        # 更新统计信息
        self.performance_monitor.update_stats("audio_stored")
        
        return audio_id
    
    def search(self, query, top_k=5, use_quantum=True):
        """搜索相似内容
        
        Args:
            query: 查询文本或向量
            top_k: 返回结果数量
            use_quantum: 是否使用量子搜索算法
            
        Returns:
            results: 搜索结果列表
        """
        # 记录操作开始
        operation_id = self.log_manager.start_operation("search")
        
        # 生成查询向量
        if isinstance(query, str):
            from SVDB.utils.data_processors.text_processor import text_to_embedding
            query_embedding = text_to_embedding(query)
            query_pointer = self.hasher.hash_to_vector(query)
            query_vector = query_embedding  # 简化版，实际应结合pointer
        else:
            query_vector = query
        
        # 执行搜索
        start_time = self.performance_monitor.start_timer("search")
        
        if use_quantum and self.grover_search.is_available():
            # 使用Grover量子搜索
            results = self.grover_search.search(query_vector, self.vector_store, top_k)
        else:
            # 使用传统搜索
            results = self.vector_store.search(query_vector, top_k)
        
        search_time = self.performance_monitor.end_timer("search", start_time)
        
        # 获取元数据
        for i, (item_id, score) in enumerate(results):
            metadata = self.metadata_store.retrieve(item_id)
            results[i] = (item_id, score, metadata)
        
        # 记录操作完成
        self.log_manager.end_operation(operation_id, status="success", 
                                      details={"query": query if isinstance(query, str) else "vector", 
                                               "results": len(results),
                                               "search_time": search_time})
        
        # 更新统计信息
        self.performance_monitor.update_stats("search_performed")
        
        return results
    
    def get_statistics(self):
        """获取系统统计信息
        
        Returns:
            stats: 统计信息字典
        """
        return self.performance_monitor.get_stats()
    
    def get_index_update_logs(self, start_time=None, end_time=None):
        """获取索引更新日志
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            logs: 日志列表
        """
        return self.log_manager.get_logs(start_time, end_time)
    
    def close(self):
        """关闭数据库连接"""
        self.vector_store.close()
        self.metadata_store.close()
        self.log_manager.close()
        self.performance_monitor.stop_monitoring()
        
        print(f"SVDB数据库已关闭: {self.db_path}")