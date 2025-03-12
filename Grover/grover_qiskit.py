# Grover - 基于Qiskit的量子Grover算法实现

import numpy as np
import time
import math
from typing import List, Tuple, Dict, Any

try:
    from qiskit import QuantumCircuit, Aer, execute
    from qiskit.circuit.library import GroverOperator
    from qiskit.quantum_info import Statevector
    from qiskit.algorithms import AmplificationProblem, Grover
    HAS_QISKIT = True
except ImportError:
    HAS_QISKIT = False
    print("警告: Qiskit未找到，将使用经典回退模式。")
    print("建议安装Qiskit以获得完整功能: pip install qiskit")

class GroverQiskitSearch:
    """
    基于Qiskit的量子Grover算法搜索类
    
    GroverQiskitSearch利用量子Grover算法的平方加速特性，
    在大规模向量数据库中实现高效的相似性搜索。
    """
    
    def __init__(self, use_simulation=True):
        """
        初始化Grover搜索
        
        Args:
            use_simulation: 是否使用模拟模式（如果没有量子硬件）
        """
        self.use_simulation = use_simulation
        self.quantum_backend_available = self._check_quantum_backend()
        self.last_search_time = 0
        self.search_count = 0
    
    def _check_quantum_backend(self):
        """
        检查量子后端是否可用
        
        Returns:
            available: 布尔值，表示量子后端是否可用
        """
        return HAS_QISKIT
    
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
        
        # 相似度阈值
        threshold = 0.7
        
        # 构建预言机函数
        def oracle_function(item_id):
            # 检索向量
            vectors_data = vector_store.retrieve_vectors(item_id)
            if vectors_data is None:
                return False
            
            embeddings, _ = vectors_data
            
            # 计算相似度
            max_similarity = 0
            for embedding in embeddings:
                # 归一化向量
                if np.linalg.norm(query_vector) != 0:
                    norm_query = query_vector / np.linalg.norm(query_vector)
                else:
                    norm_query = query_vector
                    
                if np.linalg.norm(embedding) != 0:
                    norm_embedding = embedding / np.linalg.norm(embedding)
                else:
                    norm_embedding = embedding
                
                # 计算余弦相似度
                similarity = np.dot(norm_query, norm_embedding)
                max_similarity = max(max_similarity, similarity)
            
            # 如果相似度超过阈值，则标记为目标
            return max_similarity >= threshold
        
        # 使用Qiskit的Grover算法实现
        if HAS_QISKIT:
            # 创建预言机
            n_qubits = int(np.ceil(np.log2(n)))
            oracle = QuantumCircuit(n_qubits)
            
            # 标记满足条件的状态
            marked_states = []
            for i, item_id in enumerate(all_ids):
                if oracle_function(item_id):
                    # 将索引转换为二进制表示
                    binary = format(i, f'0{n_qubits}b')
                    marked_states.append(binary)
            
            # 如果没有标记状态，返回空结果
            if not marked_states:
                return []
            
            # 创建振幅放大问题
            problem = AmplificationProblem(
                oracle=oracle,
                state_preparation=QuantumCircuit(n_qubits),
                is_good_state=lambda x: x in marked_states
            )
            
            # 创建Grover算法实例
            backend = Aer.get_backend('qasm_simulator')
            grover = Grover(quantum_instance=backend)
            
            # 执行Grover搜索
            result = grover.amplify(problem)
            counts = result.circuit_results[0]
            
            # 处理结果
            results = []
            for state, count in counts.items():
                # 将二进制状态转换回索引
                try:
                    idx = int(state, 2)
                    if idx < len(all_ids):
                        item_id = all_ids[idx]
                        # 获取实际相似度
                        vectors_data = vector_store.retrieve_vectors(item_id)
                        if vectors_data is not None:
                            embeddings, _ = vectors_data
                            max_similarity = 0
                            for embedding in embeddings:
                                # 计算相似度
                                if np.linalg.norm(query_vector) != 0 and np.linalg.norm(embedding) != 0:
                                    similarity = np.dot(query_vector / np.linalg.norm(query_vector), 
                                                        embedding / np.linalg.norm(embedding))
                                    max_similarity = max(max_similarity, similarity)
                            
                            # 添加到结果
                            results.append((item_id, max_similarity))
                except ValueError:
                    continue
            
            # 按相似度排序并返回前top_k个结果
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:top_k]
        
        # 如果没有Qiskit，回退到经典搜索
        return self._classical_search(query_vector, vector_store, top_k)
    
    def get_stats(self):
        """
        获取搜索统计信息
        
        Returns:
            stats: 统计信息字典
        """
        return {
            'search_count': self.search_count,
            'last_search_time': self.last_search_time,
            'quantum_backend_available': self.quantum_backend_available
        }