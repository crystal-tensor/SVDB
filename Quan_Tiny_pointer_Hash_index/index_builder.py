# Quan_Tiny_pointer_Hash_index - 索引构建器实现

import numpy as np
import time
import hashlib
from SVDB.Quan_Tiny_pointer_Hash_index.hash_bucket import HashBucket

class HashIndexBuilder:
    """
    哈希索引构建器，负责构建和管理量子微小指针哈希索引
    
    HashIndexBuilder使用量子哈希微小指针构建高效的索引结构，
    通过哈希桶组织相似的向量，实现快速的近似最近邻搜索。
    """
    
    def __init__(self, hasher, bucket_size=100, dimension=32):
        """
        初始化哈希索引构建器
        
        Args:
            hasher: PTHash实例，用于生成量子哈希
            bucket_size: 每个哈希桶的最大容量
            dimension: 指针向量的维度
        """
        self.hasher = hasher
        self.bucket_size = bucket_size
        self.dimension = dimension
        self.buckets = {}  # 桶ID到哈希桶的映射
        self.item_to_bucket = {}  # 项目ID到桶ID的映射
        self.last_update = time.time()
    
    def build_index(self, item_id, pointers):
        """
        为项目构建索引
        
        Args:
            item_id: 项目ID
            pointers: 量子哈希微小指针列表
            
        Returns:
            success: 布尔值，表示构建是否成功
        """
        if not pointers or len(pointers) == 0:
            print(f"错误: 项目 {item_id} 没有提供指针")
            return False
        
        # 如果项目已存在，先移除旧索引
        if item_id in self.item_to_bucket:
            self.remove_index(item_id)
        
        # 为每个指针分配哈希桶
        for i, pointer in enumerate(pointers):
            # 生成桶ID
            bucket_id = self._generate_bucket_id(pointer)
            
            # 如果桶不存在，创建新桶
            if bucket_id not in self.buckets:
                self.buckets[bucket_id] = HashBucket(bucket_id, self.dimension)
            
            # 将指针添加到桶中
            sub_item_id = f"{item_id}_{i}"
            success = self.buckets[bucket_id].add_item(sub_item_id, pointer)
            
            if success:
                # 记录项目到桶的映射
                if item_id not in self.item_to_bucket:
                    self.item_to_bucket[item_id] = []
                self.item_to_bucket[item_id].append((bucket_id, sub_item_id))
        
        # 更新最后修改时间
        self.last_update = time.time()
        
        return True
    
    def remove_index(self, item_id):
        """
        移除项目的索引
        
        Args:
            item_id: 项目ID
            
        Returns:
            success: 布尔值，表示移除是否成功
        """
        if item_id not in self.item_to_bucket:
            return False
        
        # 从所有相关桶中移除项目
        for bucket_id, sub_item_id in self.item_to_bucket[item_id]:
            if bucket_id in self.buckets:
                self.buckets[bucket_id].remove_item(sub_item_id)
                
                # 如果桶为空，删除桶
                if self.buckets[bucket_id].get_item_count() == 0:
                    del self.buckets[bucket_id]
        
        # 移除项目到桶的映射
        del self.item_to_bucket[item_id]
        
        # 更新最后修改时间
        self.last_update = time.time()
        
        return True
    
    def search(self, query_pointer, top_k=5, max_buckets=3):
        """
        使用量子哈希微小指针搜索最相似的项目
        
        Args:
            query_pointer: 查询指针
            top_k: 返回结果数量
            max_buckets: 搜索的最大桶数量
            
        Returns:
            results: 包含(item_id, score)元组的列表
        """
        if len(self.buckets) == 0:
            return []
        
        # 生成查询桶ID
        query_bucket_id = self._generate_bucket_id(query_pointer)
        
        # 找到最相似的桶
        similar_buckets = self._find_similar_buckets(query_pointer, max_buckets)
        
        # 在相似桶中搜索
        all_results = []
        for bucket_id, _ in similar_buckets:
            if bucket_id in self.buckets:
                bucket_results = self.buckets[bucket_id].search(query_pointer)
                all_results.extend(bucket_results)
        
        # 合并结果（将子项目ID转换为项目ID）
        merged_results = {}
        for sub_item_id, score in all_results:
            item_id = sub_item_id.rsplit('_', 1)[0]  # 移除子项目ID后缀
            if item_id not in merged_results or score > merged_results[item_id]:
                merged_results[item_id] = score
        
        # 按相似度排序
        sorted_results = sorted(merged_results.items(), key=lambda x: x[1], reverse=True)
        
        # 返回前top_k个结果
        return sorted_results[:top_k]
    
    def get_bucket_count(self):
        """
        获取哈希桶数量
        
        Returns:
            count: 哈希桶数量
        """
        return len(self.buckets)
    
    def get_indexed_item_count(self):
        """
        获取已索引的项目数量
        
        Returns:
            count: 已索引的项目数量
        """
        return len(self.item_to_bucket)
    
    def get_last_update_time(self):
        """
        获取最后更新时间
        
        Returns:
            timestamp: 最后更新时间戳
        """
        return self.last_update
    
    def _generate_bucket_id(self, pointer):
        """
        为指针生成桶ID
        
        Args:
            pointer: 量子哈希微小指针
            
        Returns:
            bucket_id: 桶ID
        """
        # 将指针转换为字节
        pointer_bytes = pointer.tobytes()
        
        # 使用SHA-256哈希函数生成桶ID
        hasher = hashlib.sha256(pointer_bytes)
        hash_bytes = hasher.digest()
        
        # 取前4个字节作为桶ID
        bucket_id = int.from_bytes(hash_bytes[:4], 'big')
        
        return bucket_id
    
    def _find_similar_buckets(self, query_pointer, max_buckets=3):
        """
        找到与查询指针最相似的桶
        
        Args:
            query_pointer: 查询指针
            max_buckets: 返回的最大桶数量
            
        Returns:
            similar_buckets: 包含(bucket_id, similarity)元组的列表
        """
        if len(self.buckets) == 0:
            return []
        
        # 确保查询指针已归一化
        if np.linalg.norm(query_pointer) != 0:
            query_pointer = query_pointer / np.linalg.norm(query_pointer)
        
        # 计算查询指针与所有桶中心点的相似度
        similarities = []
        for bucket_id, bucket in self.buckets.items():
            centroid = bucket.get_centroid()
            if centroid is not None:
                # 计算余弦相似度
                similarity = np.dot(query_pointer, centroid)
                similarities.append((bucket_id, similarity))
        
        # 按相似度排序
        sorted_similarities = sorted(similarities, key=lambda x: x[1], reverse=True)
        
        # 返回前max_buckets个结果
        return sorted_similarities[:max_buckets]