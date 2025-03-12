# Quan_Tiny_pointer_Hash_index - 哈希桶实现

import numpy as np
import time

class HashBucket:
    """
    哈希桶类，用于存储和组织相似的向量指针
    
    哈希桶是量子微小指针哈希索引的基本单元，它存储具有相似哈希值的向量指针，
    并提供高效的检索机制。每个哈希桶都有一个唯一的ID，用于在索引中定位。
    """
    
    def __init__(self, bucket_id, dimension=32):
        """
        初始化哈希桶
        
        Args:
            bucket_id: 哈希桶ID
            dimension: 向量维度
        """
        self.bucket_id = bucket_id
        self.dimension = dimension
        self.items = {}  # 项目ID到指针的映射
        self.centroid = None  # 桶中心点
        self.last_update = time.time()
    
    def add_item(self, item_id, pointer):
        """
        向哈希桶添加项目
        
        Args:
            item_id: 项目ID
            pointer: 量子哈希微小指针
            
        Returns:
            success: 布尔值，表示添加是否成功
        """
        # 确保指针维度正确
        if len(pointer) != self.dimension:
            print(f"错误: 指针维度不匹配，预期 {self.dimension}，实际 {len(pointer)}")
            return False
        
        # 存储指针
        self.items[item_id] = np.array(pointer)
        
        # 更新桶中心点
        self._update_centroid()
        
        # 更新最后修改时间
        self.last_update = time.time()
        
        return True
    
    def remove_item(self, item_id):
        """
        从哈希桶移除项目
        
        Args:
            item_id: 项目ID
            
        Returns:
            success: 布尔值，表示移除是否成功
        """
        if item_id not in self.items:
            return False
        
        # 移除项目
        del self.items[item_id]
        
        # 更新桶中心点
        self._update_centroid()
        
        # 更新最后修改时间
        self.last_update = time.time()
        
        return True
    
    def contains(self, item_id):
        """
        检查哈希桶是否包含指定项目
        
        Args:
            item_id: 项目ID
            
        Returns:
            contains: 布尔值，表示是否包含项目
        """
        return item_id in self.items
    
    def get_pointer(self, item_id):
        """
        获取项目的指针
        
        Args:
            item_id: 项目ID
            
        Returns:
            pointer: 量子哈希微小指针，如果项目不存在则返回None
        """
        return self.items.get(item_id)
    
    def get_all_items(self):
        """
        获取哈希桶中的所有项目
        
        Returns:
            items: 项目ID到指针的映射
        """
        return self.items
    
    def get_item_count(self):
        """
        获取哈希桶中的项目数量
        
        Returns:
            count: 项目数量
        """
        return len(self.items)
    
    def get_centroid(self):
        """
        获取哈希桶的中心点
        
        Returns:
            centroid: 中心点向量，如果桶为空则返回None
        """
        return self.centroid
    
    def get_last_update_time(self):
        """
        获取最后更新时间
        
        Returns:
            timestamp: 最后更新时间戳
        """
        return self.last_update
    
    def search(self, query_pointer, top_k=5):
        """
        在哈希桶中搜索最相似的项目
        
        Args:
            query_pointer: 查询指针
            top_k: 返回结果数量
            
        Returns:
            results: 包含(item_id, score)元组的列表
        """
        if len(self.items) == 0:
            return []
        
        # 确保查询指针已归一化
        if np.linalg.norm(query_pointer) != 0:
            query_pointer = query_pointer / np.linalg.norm(query_pointer)
        
        # 计算余弦相似度
        similarities = []
        for item_id, pointer in self.items.items():
            # 确保指针已归一化
            if np.linalg.norm(pointer) != 0:
                pointer = pointer / np.linalg.norm(pointer)
            
            # 计算余弦相似度
            similarity = np.dot(query_pointer, pointer)
            similarities.append((item_id, similarity))
        
        # 按相似度排序
        sorted_similarities = sorted(similarities, key=lambda x: x[1], reverse=True)
        
        # 返回前top_k个结果
        return sorted_similarities[:top_k]
    
    def _update_centroid(self):
        """
        更新哈希桶的中心点
        """
        if len(self.items) == 0:
            self.centroid = None
            return
        
        # 计算所有指针的平均值
        pointers = np.array(list(self.items.values()))
        centroid = np.mean(pointers, axis=0)
        
        # 归一化中心点
        if np.linalg.norm(centroid) != 0:
            centroid = centroid / np.linalg.norm(centroid)
        
        self.centroid = centroid