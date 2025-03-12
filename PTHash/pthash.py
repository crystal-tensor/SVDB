# PTHash - 量子哈希函数核心实现

import numpy as np
import hmac
import hashlib
from decimal import Decimal, getcontext
import sys

# 设置高精度计算
getcontext().prec = 20

# 尝试导入量子模拟器
try:
    from quafu import QuantumCircuit
    from quafu.simulators import simulate
    HAS_QUAFU = True
except ImportError:
    HAS_QUAFU = False
    print("警告: PyQuafu未找到，将使用经典回退模式。")
    print("建议安装PyQuafu以获得完整功能: pip install pyquafu")

class PTHash:
    """
    确定性量子增强哈希函数
    
    PTHash (Parameterized Tiny Hash) 是一种基于量子电路的哈希函数，
    它利用量子态的概率分布特性生成确定性哈希值。该哈希函数可用于
    生成微小指针，用于向量数据库的索引构建。
    """

    def __init__(self, num_qubits=8, depth=3, shots=1024):
        """
        初始化PTHash量子哈希函数
        
        Args:
            num_qubits: 量子比特数量，决定了哈希空间的大小
            depth: 量子电路深度，影响哈希的复杂性
            shots: 量子测量次数，影响概率分布的精度
        """
        self.num_qubits = num_qubits
        self.depth = depth
        self.shots = shots
        self.has_quantum_backend = HAS_QUAFU
    
    def _generate_circuit(self, seed):
        """
        基于种子生成确定性量子电路
        
        Args:
            seed: 整数种子值
            
        Returns:
            qc: 量子电路对象
        """
        # 确保种子在有效范围内 (0 到 2^32-1)
        seed = seed % (2**32)
        
        if not self.has_quantum_backend:
            # 如果没有量子后端，返回None
            return None
        
        # 初始化量子电路
        qc = QuantumCircuit(self.num_qubits, self.num_qubits)
        
        # 分层参数化结构
        for d in range(self.depth):
            # 参数化旋转层
            for qubit in range(self.num_qubits):
                # 使用HMAC生成确定性角度
                hmac_theta = hmac.new(
                    key=seed.to_bytes(4, 'big'),
                    msg=f"{d}_{qubit}_theta".encode(),
                    digestmod='sha256'
                )
                theta = int.from_bytes(hmac_theta.digest(), 'big') % (2**32)
                theta = theta / 2**32 * 2 * np.pi
                
                hmac_phi = hmac.new(
                    key=seed.to_bytes(4, 'big'),
                    msg=f"{d}_{qubit}_phi".encode(),
                    digestmod='sha256'
                )
                phi = int.from_bytes(hmac_phi.digest(), 'big') % (2**32)
                phi = phi / 2**32 * 2 * np.pi
                
                # 使用PyQuafu支持的旋转门
                qc.rx(qubit, theta)  # 绕X轴旋转
                qc.ry(qubit, phi)    # 绕Y轴旋转
                qc.rz(qubit, 0)      # 绕Z轴旋转（角度为0）
            
            # 确定性纠缠模式
            for qubit in range(self.num_qubits):
                target = (qubit + d) % self.num_qubits
                if qubit != target:
                    qc.cnot(qubit, target)
        
        qc.measure(list(range(self.num_qubits)), list(range(self.num_qubits)))
        return qc

    def _circuit_to_distribution(self, circuit, seed):
        """
        量子模拟与确定性回退
        
        Args:
            circuit: 量子电路对象
            seed: 整数种子值
            
        Returns:
            distribution: 测量结果的概率分布
        """
        # 确保种子在有效范围内
        seed = seed % (2**32)
        
        if self.has_quantum_backend and circuit is not None:
            try:
                # 使用固定的随机状态进行模拟
                np.random.seed(seed)
                result = simulate(circuit, shots=self.shots)
                counts = result.counts
                total = sum(counts.values())
                return {k: v/total for k,v in counts.items()}
            except Exception as e:
                print(f"量子模拟出错，回退到确定性模拟: {e}")
        
        # 回退到确定性模拟
        return self._fallback_simulation(self.num_qubits, seed)

    def _fallback_simulation(self, num_qubits, seed):
        """
        基于种子的确定性模拟
        
        Args:
            num_qubits: 量子比特数量
            seed: 整数种子值
            
        Returns:
            distribution: 模拟的概率分布
        """
        # 确保种子在有效范围内
        seed = seed % (2**32)
        rng = np.random.RandomState(seed)
        
        # 生成概率权重
        bitstrings = [format(i, f'0{num_qubits}b') for i in range(2**num_qubits)]
        weights = rng.rand(len(bitstrings))
        weights /= weights.sum()
        
        # 分配测量次数
        counts = {}
        remaining = self.shots
        for i, bs in enumerate(bitstrings[:-1]):
            cnt = int(weights[i] * self.shots)
            counts[bs] = cnt
            remaining -= cnt
        counts[bitstrings[-1]] = remaining
        
        # 计算概率
        total = sum(counts.values())
        return {k: v/total for k,v in counts.items()}

    def _distribution_to_hash(self, distribution):
        """
        抗碰撞哈希转换
        
        Args:
            distribution: 概率分布字典
            
        Returns:
            hash_hex: 十六进制哈希字符串
        """
        # 高精度编码
        sorted_dist = sorted(distribution.items())
        dist_bytes = bytearray()
        
        for bs, prob in sorted_dist:
            # 使用Decimal保留精度
            int_val = int(Decimal(prob) * Decimal(10**18))
            dist_bytes.extend(int_val.to_bytes(16, 'big'))
            dist_bytes.extend(bs.encode())
        
        # 使用SHAKE可调长度哈希
        hasher = hashlib.shake_256()
        hasher.update(dist_bytes)
        return hasher.hexdigest(32)  # 256-bit输出

    def hash(self, data):
        """
        计算数据的量子增强哈希值
        
        Args:
            data: 输入数据（字符串或字节）
            
        Returns:
            hash_hex: 十六进制哈希字符串
        """
        # 生成主种子
        if isinstance(data, str):
            data = data.encode()
        # 确保种子在有效范围内 (0 到 2^32-1)
        seed = int.from_bytes(hashlib.shake_256(data).digest(4), 'big')
        
        # 生成电路
        circuit = self._generate_circuit(seed)
        
        # 获取分布
        distribution = self._circuit_to_distribution(circuit, seed)
        
        # 生成最终哈希
        return self._distribution_to_hash(distribution)

    def hash_to_vector(self, data, vector_size=32):
        """
        将哈希值转换为向量表示
        
        Args:
            data: 输入数据（字符串或字节）
            vector_size: 输出向量的维度
            
        Returns:
            vector: 归一化的向量表示
        """
        # 获取哈希值（十六进制字符串）
        hash_hex = self.hash(data)
        
        # 将十六进制字符串转换为字节
        hash_bytes = bytes.fromhex(hash_hex)
        
        # 确保向量大小合适
        if len(hash_bytes) < vector_size:
            # 如果哈希值不够长，重复填充
            hash_bytes = hash_bytes * (vector_size // len(hash_bytes) + 1)
        
        # 截取所需长度
        hash_bytes = hash_bytes[:vector_size]
        
        # 转换为浮点数向量，范围[-1, 1]
        vector = np.array([b/127.5 - 1 for b in hash_bytes], dtype=np.float32)
        
        # 归一化向量（使其长度为1，适合量子态表示）
        vector = vector / np.linalg.norm(vector)
        
        return vector
    
    def batch_hash_to_vectors(self, data_list, vector_size=32):
        """
        批量将数据转换为哈希向量
        
        Args:
            data_list: 输入数据列表
            vector_size: 输出向量的维度
            
        Returns:
            vectors: 向量数组
        """
        vectors = []
        for data in data_list:
            vector = self.hash_to_vector(data, vector_size)
            vectors.append(vector)
        return np.array(vectors)
    
    def is_quantum_available(self):
        """
        检查量子后端是否可用
        
        Returns:
            available: 布尔值，表示量子后端是否可用
        """
        return self.has_quantum_backend