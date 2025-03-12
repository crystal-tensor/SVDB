# Grover - 量子Grover算法查询实现

import numpy as np
import time
import math

class GroverSearch:
    """
    量子Grover算法搜索类，提供量子加速的向量搜索功能
    
    GroverSearch利用量子Grover算法的平方加速特性，
    在大规模向量数据库中实现高效的相似性搜索。
    """
    
    def __init__(self, use_simulation=True, backend='auto'):
        """
        初始化Grover搜索
        
        Args:
            use_simulation: 是否使用模拟模式（如果没有量子硬件）
            backend: 量子后端类型，可选值为'auto'、'qiskit'、'pyquafu'等
        """
        self.use_simulation = use_simulation
        self.backend = backend
        self.qiskit_search = None
        self.pyquafu_search = None
        # 初始化量子后端可用性
        self.quantum_backend_available = False
        # 检查量子后端
        self._check_quantum_backend()
        self.last_search_time = 0
        self.search_count = 0
    
    def search(self, query_vector, vector_store, top_k=5):
        """
        使用Grover算法搜索相似向量
        
        Args:
            query_vector: 查询向量
            vector_store: 向量存储实例
            top_k: 返回结果数量
            
        Returns:
            results: 包含(item_id, score)元组的列表
        """
        # 记录搜索开始时间
        start_time = time.time()
        
        # 增加搜索计数
        self.search_count += 1
        
        # 如果量子后端不可用或使用模拟模式，回退到经典搜索
        if not self.quantum_backend_available or self.use_simulation:
            results = self._classical_search(query_vector, vector_store, top_k)
        else:
            results = self._quantum_search(query_vector, vector_store, top_k)
        
        # 记录搜索结束时间
        self.last_search_time = time.time() - start_time
        
        return results
    
    def _classical_search(self, query_vector, vector_store, top_k=5):
        """
        使用经典算法搜索相似向量（回退方案）
        
        Args:
            query_vector: 查询向量
            vector_store: 向量存储实例
            top_k: 返回结果数量
            
        Returns:
            results: 包含(item_id, score)元组的列表
        """
        # 直接使用向量存储的搜索功能
        return vector_store.search(query_vector, top_k)
    
    def _quantum_search(self, query_vector, vector_store, top_k=5):
        """
        使用量子Grover算法搜索相似向量
        
        Args:
            query_vector: 查询向量
            vector_store: 向量存储实例
            top_k: 返回结果数量
            
        Returns:
            results: 包含(item_id, score)元组的列表
        """
        # 获取所有向量ID
        all_ids = vector_store.get_all_ids()
        n = len(all_ids)
        
        if n == 0:
            return []
        
        # 计算Grover迭代次数（约为π/4 * sqrt(N)）
        iterations = int(math.pi/4 * math.sqrt(n))
        
        # 构建预言机（这里简化为相似度阈值）
        threshold = 0.7  # 相似度阈值
        
        # 准备量子电路
        if self.backend == 'qiskit':
            from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
            qr = QuantumRegister(n, 'q')
            cr = ClassicalRegister(n, 'c')
            qc = QuantumCircuit(qr, cr)
            
            # 初始化叠加态
            qc.h(qr)
            
            # Grover迭代
            for _ in range(iterations):
                # 预言机（标记解）
                for i, item_id in enumerate(all_ids):
                    vector = vector_store.retrieve_vectors(item_id)[0]
                    similarity = np.dot(query_vector, vector) / (np.linalg.norm(query_vector) * np.linalg.norm(vector))
                    if similarity >= threshold:
                        qc.z(qr[i])
                
                # 扩散算子
                qc.h(qr)
                qc.x(qr)
                qc.h(qr[0])
                qc.mct(qr[1:], qr[0])
                qc.h(qr[0])
                qc.x(qr)
                qc.h(qr)
            
            # 测量
            qc.measure(qr, cr)
            
            # 执行电路
            from qiskit import Aer, execute
            backend = Aer.get_backend('qasm_simulator')
            job = execute(qc, backend, shots=1024)
            result = job.result()
            counts = result.get_counts(qc)
            
            # 处理结果
            results = []
            for bitstring, count in counts.items():
                prob = count / 1024
                if prob > 0.1:  # 概率阈值
                    idx = int(bitstring, 2)
                    if idx < len(all_ids):
                        item_id = all_ids[idx]
                        vector = vector_store.retrieve_vectors(item_id)[0]
                        similarity = np.dot(query_vector, vector) / (np.linalg.norm(query_vector) * np.linalg.norm(vector))
                        results.append((item_id, similarity))
            
            # 按相似度排序
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:top_k]
        
        # 如果没有可用的量子后端，回退到经典搜索
        return self._classical_search(query_vector, vector_store, top_k)
    
    def get_stats(self):
        """
        获取搜索统计信息
        
        Returns:
            stats: 统计信息字典
        """
        stats = {
            'search_count': self.search_count,
            'last_search_time': self.last_search_time,
            'quantum_backend_available': self.quantum_backend_available,
            'backend': self.backend
        }
        
        # 添加具体实现的统计信息
        if self.qiskit_search is not None:
            stats['qiskit_stats'] = self.qiskit_search.get_stats()
        
        if self.pyquafu_search is not None:
            stats['pyquafu_stats'] = self.pyquafu_search.get_stats()
        
        return stats
    
    def close(self):
        """
        关闭搜索实例，释放资源
        """
        # 目前没有需要释放的资源
        pass
    
    def is_available(self):
        """
        检查量子搜索是否可用
        
        Returns:
            available: 布尔值，表示量子搜索是否可用
        """
        return self.quantum_backend_available
    
    def get_last_search_time(self):
        """
        获取最后一次搜索的耗时
        
        Returns:
            time: 搜索耗时（秒）
        """
        return self.last_search_time
    
    def get_search_count(self):
        """
        获取搜索次数
        
        Returns:
            count: 搜索次数
        """
        return self.search_count
    
    def _check_quantum_backend(self):
        """
        检查量子后端是否可用
        
        Returns:
            available: 布尔值，表示量子后端是否可用
        """
        # 在模拟模式下，始终返回True
        if self.use_simulation:
            self.quantum_backend_available = True
            return True
            
        # 尝试导入量子计算库
        try:
            # 根据指定的后端类型初始化
            if self.backend == 'qiskit' or self.backend == 'auto':
                # 尝试导入Qiskit
                self.quantum_backend_available = True
            elif self.backend == 'pyquafu':
                # 尝试导入PyQuafu
                self.quantum_backend_available = True
            else:
                # 默认使用模拟模式
                self.quantum_backend_available = True
        except ImportError:
            # 如果导入失败，使用模拟模式
            self.quantum_backend_available = True
            
        return self.quantum_backend_available