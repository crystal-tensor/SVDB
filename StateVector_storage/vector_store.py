# StateVector_storage - 向量数据存储核心实现

import os
import numpy as np
import sqlite3
import uuid
import time
import pickle  # 用于序列化向量数据

class VectorStore:
    """
    向量数据存储类，负责管理向量数据的存储和检索
    
    VectorStore提供高效的向量存储和检索功能，支持批量操作和增量更新。
    它使用优化的数据结构来存储向量和元数据，并提供高效的相似性搜索功能。
    """
    
    def __init__(self, db_path, clear_existing=False):
        """
        初始化向量存储
        
        Args:
            db_path: 数据库存储路径
            clear_existing: 是否清除现有数据库内容
        """
        self.db_path = db_path
        self.last_update = time.time()
        
        # 确保数据库目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # 初始化数据库
        from .init_db import init_database
        init_database(db_path, clear_existing)
        
        # 连接到数据库，确保有写入权限
        self.conn = sqlite3.connect(db_path, isolation_level=None)
        # 设置数据库连接为读写模式
        self.conn.execute('PRAGMA journal_mode=WAL')
        self.cursor = self.conn.cursor()
        print(f"已连接到向量数据库: {db_path}")
        if clear_existing:
            print("注意: 数据库内容已被清空，所有旧数据已删除。")
    
    def store_vectors(self, embeddings, pointers, item_id=None):
        """
        存储向量和指针
        
        Args:
            embeddings: 向量嵌入列表
            pointers: 量子哈希微小指针列表
            item_id: 可选的项目ID，如果未提供则自动生成
            
        Returns:
            item_id: 项目ID
        """
        # 生成唯一ID
        if item_id is None:
            item_id = str(uuid.uuid4())
        
        # 转换为numpy数组
        embeddings_array = np.array(embeddings)
        pointers_array = np.array(pointers)
        
        # 获取当前时间戳
        timestamp = time.time()
        
        # 保存到数据库
        self._save_vector(item_id, embeddings_array, pointers_array, timestamp)
        
        # 更新最后修改时间
        self.last_update = timestamp
        
        return item_id
    
    def retrieve_vectors(self, item_id):
        """
        检索向量和指针
        
        Args:
            item_id: 项目ID
            
        Returns:
            tuple: (embeddings, pointers) 或 None（如果ID不存在）
        """
        self.cursor.execute("SELECT embeddings, pointers FROM vectors WHERE id = ?", (item_id,))
        result = self.cursor.fetchone()
        
        if result is None:
            return None
        
        # 反序列化数据
        embeddings = pickle.loads(result[0])
        pointers = pickle.loads(result[1])
        
        return embeddings, pointers
    
    def delete_vectors(self, item_id):
        """
        删除向量和指针
        
        Args:
            item_id: 项目ID
            
        Returns:
            success: 布尔值，表示删除是否成功
        """
        if item_id not in self.vectors:
            return False
        
        # 删除向量和指针
        del self.vectors[item_id]
        if item_id in self.pointers:
            del self.pointers[item_id]
        if item_id in self.id_mapping:
            del self.id_mapping[item_id]
        
        # 更新最后修改时间
        self.last_update = time.time()
        
        # 保存到文件
        self._save()
        
        return True
    
    def search(self, query_vector, top_k=5):
        """
        搜索最相似的向量
        
        Args:
            query_vector: 查询向量
            top_k: 返回结果数量
            
        Returns:
            results: 包含(item_id, score)元组的列表
        """
        # 获取所有向量ID
        self.cursor.execute("SELECT id, embeddings FROM vectors")
        results = self.cursor.fetchall()
        
        if not results:
            return []
        
        # 确保查询向量已归一化
        if np.linalg.norm(query_vector) != 0:
            query_vector = query_vector / np.linalg.norm(query_vector)
        
        # 计算余弦相似度
        similarities = []
        for item_id, embeddings_blob in results:
            # 反序列化向量数据
            embeddings = pickle.loads(embeddings_blob)
            
            # 对每个项目中的所有向量计算相似度
            item_similarities = []
            for embedding in embeddings:
                # 确保向量已归一化
                if np.linalg.norm(embedding) != 0:
                    embedding = embedding / np.linalg.norm(embedding)
                
                # 计算余弦相似度
                similarity = np.dot(query_vector, embedding)
                item_similarities.append(similarity)
            
            # 使用最大相似度作为项目的相似度
            if item_similarities:
                max_similarity = max(item_similarities)
                similarities.append((item_id, max_similarity))
        
        # 按相似度排序
        sorted_similarities = sorted(similarities, key=lambda x: x[1], reverse=True)
        
        # 返回前top_k个结果
        return sorted_similarities[:top_k]
    
    def search_with_pointers(self, query_vector, query_pointer, top_k=5, pointer_weight=0.3):
        """
        使用向量和指针进行组合搜索
        
        Args:
            query_vector: 查询向量
            query_pointer: 查询指针
            top_k: 返回结果数量
            pointer_weight: 指针在相似度计算中的权重
            
        Returns:
            results: 包含(item_id, score)元组的列表
        """
        if len(self.vectors) == 0 or len(self.pointers) == 0:
            return []
        
        # 确保查询向量和指针已归一化
        if np.linalg.norm(query_vector) != 0:
            query_vector = query_vector / np.linalg.norm(query_vector)
        if np.linalg.norm(query_pointer) != 0:
            query_pointer = query_pointer / np.linalg.norm(query_pointer)
        
        # 计算组合相似度
        similarities = []
        for item_id in self.vectors.keys():
            if item_id not in self.pointers:
                continue
            
            embeddings = self.vectors[item_id]
            item_pointers = self.pointers[item_id]
            
            # 对每个向量和指针对计算相似度
            item_similarities = []
            for embedding, pointer in zip(embeddings, item_pointers):
                # 确保向量和指针已归一化
                if np.linalg.norm(embedding) != 0:
                    embedding = embedding / np.linalg.norm(embedding)
                if np.linalg.norm(pointer) != 0:
                    pointer = pointer / np.linalg.norm(pointer)
                
                # 计算向量相似度和指针相似度
                vector_similarity = np.dot(query_vector, embedding)
                pointer_similarity = np.dot(query_pointer, pointer)
                
                # 组合相似度
                combined_similarity = (1 - pointer_weight) * vector_similarity + pointer_weight * pointer_similarity
                item_similarities.append(combined_similarity)
            
            # 使用最大相似度作为项目的相似度
            max_similarity = max(item_similarities)
            similarities.append((item_id, max_similarity))
        
        # 按相似度排序
        sorted_similarities = sorted(similarities, key=lambda x: x[1], reverse=True)
        
        # 返回前top_k个结果
        return sorted_similarities[:top_k]
    
    def get_all_ids(self):
        """
        获取所有项目ID
        
        Returns:
            ids: 项目ID列表
        """
        return list(self.vectors.keys())
    
    def get_vector_count(self):
        """
        获取向量总数
        
        Returns:
            count: 向量总数
        """
        count = 0
        for item_id in self.vectors:
            count += len(self.vectors[item_id])
        return count
    
    def get_last_update_time(self):
        """
        获取最后更新时间
        
        Returns:
            timestamp: 最后更新时间戳
        """
        return self.last_update
    
    def _save_vector(self, item_id, embeddings, pointers, timestamp):
        """
        将向量数据保存到数据库
        """
        # 序列化向量数据
        embeddings_blob = pickle.dumps(embeddings)
        pointers_blob = pickle.dumps(pointers)
        
        # 存储到数据库
        self.cursor.execute("""
        INSERT OR REPLACE INTO vectors (id, embeddings, pointers, timestamp)
        VALUES (?, ?, ?, ?)
        """, (item_id, embeddings_blob, pointers_blob, timestamp))
        
        self.conn.commit()
    
    def close(self):
        """
        关闭向量存储
        """
        if hasattr(self, 'conn'):
            self.conn.close()
        print(f"向量存储已关闭: {self.db_path}")