# UQHash - 通用量子哈希函数接口
# 基于MCP协议理念设计的通用量子计算适配层

import numpy as np
import hmac
import hashlib
import importlib
import json
import os
import sys
from decimal import Decimal, getcontext
from abc import ABC, abstractmethod
from typing import Dict, List, Union, Optional, Any, Tuple

# 设置高精度计算
getcontext().prec = 20

# 默认配置路径
DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uqhash_config.json')

class QuantumBackendAdapter(ABC):
    """
    量子后端适配器抽象基类
    
    定义了所有量子后端必须实现的接口方法，使不同的量子计算平台
    能够通过统一的接口与UQHash交互。
    """
    
    @abstractmethod
    def create_circuit(self, num_qubits: int, num_clbits: int) -> Any:
        """
        创建量子电路
        
        Args:
            num_qubits: 量子比特数量
            num_clbits: 经典比特数量
            
        Returns:
            circuit: 量子电路对象
        """
        pass
    
    @abstractmethod
    def apply_rx(self, circuit: Any, qubit: int, theta: float) -> None:
        """
        应用RX门
        
        Args:
            circuit: 量子电路对象
            qubit: 目标量子比特
            theta: 旋转角度
        """
        pass
    
    @abstractmethod
    def apply_ry(self, circuit: Any, qubit: int, theta: float) -> None:
        """
        应用RY门
        
        Args:
            circuit: 量子电路对象
            qubit: 目标量子比特
            theta: 旋转角度
        """
        pass
    
    @abstractmethod
    def apply_rz(self, circuit: Any, qubit: int, theta: float) -> None:
        """
        应用RZ门
        
        Args:
            circuit: 量子电路对象
            qubit: 目标量子比特
            theta: 旋转角度
        """
        pass
    
    @abstractmethod
    def apply_cnot(self, circuit: Any, control: int, target: int) -> None:
        """
        应用CNOT门
        
        Args:
            circuit: 量子电路对象
            control: 控制量子比特
            target: 目标量子比特
        """
        pass
    
    @abstractmethod
    def measure_all(self, circuit: Any) -> None:
        """
        测量所有量子比特
        
        Args:
            circuit: 量子电路对象
        """
        pass
    
    @abstractmethod
    def run_circuit(self, circuit: Any, shots: int, seed: Optional[int] = None) -> Dict[str, int]:
        """
        运行量子电路并返回测量结果
        
        Args:
            circuit: 量子电路对象
            shots: 运行次数
            seed: 随机数种子（可选）
            
        Returns:
            counts: 测量结果计数字典 {比特串: 计数}
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        检查后端是否可用
        
        Returns:
            available: 布尔值，表示后端是否可用
        """
        pass


class QuafuAdapter(QuantumBackendAdapter):
    """
    PyQuafu量子后端适配器
    """
    
    def __init__(self):
        """
        初始化PyQuafu适配器
        """
        try:
            from quafu import QuantumCircuit
            from quafu.simulators import simulate
            self.QuantumCircuit = QuantumCircuit
            self.simulate = simulate
            self._available = True
        except ImportError:
            self._available = False
            print("警告: PyQuafu未找到，此后端不可用")
    
    def create_circuit(self, num_qubits: int, num_clbits: int) -> Any:
        if not self._available:
            return None
        return self.QuantumCircuit(num_qubits, num_clbits)
    
    def apply_rx(self, circuit: Any, qubit: int, theta: float) -> None:
        if circuit is not None:
            circuit.rx(qubit, theta)
    
    def apply_ry(self, circuit: Any, qubit: int, theta: float) -> None:
        if circuit is not None:
            circuit.ry(qubit, theta)
    
    def apply_rz(self, circuit: Any, qubit: int, theta: float) -> None:
        if circuit is not None:
            circuit.rz(qubit, theta)
    
    def apply_cnot(self, circuit: Any, control: int, target: int) -> None:
        if circuit is not None:
            circuit.cnot(control, target)
    
    def measure_all(self, circuit: Any) -> None:
        if circuit is not None:
            num_qubits = circuit.num_qubits
            circuit.measure(list(range(num_qubits)), list(range(num_qubits)))
    
    def run_circuit(self, circuit: Any, shots: int, seed: Optional[int] = None) -> Dict[str, int]:
        if not self._available or circuit is None:
            return {}
        try:
            result = self.simulate(circuit, shots=shots, seed=seed)
            return result.counts
        except Exception as e:
            print(f"运行PyQuafu电路时出错: {e}")
            return {}
    
    def is_available(self) -> bool:
        return self._available


class QiskitAdapter(QuantumBackendAdapter):
    """
    Qiskit量子后端适配器
    """
    
    def __init__(self, backend_name: str = 'aer_simulator'):
        """
        初始化Qiskit适配器
        
        Args:
            backend_name: 后端名称，默认为'aer_simulator'
        """
        self.backend_name = backend_name
        try:
            from qiskit import QuantumCircuit, transpile, execute
            from qiskit import Aer
            from qiskit.providers.aer import AerSimulator
            
            self.QuantumCircuit = QuantumCircuit
            self.transpile = transpile
            self.execute = execute
            
            # 初始化后端
            if backend_name == 'aer_simulator':
                self.backend = AerSimulator()
            else:
                self.backend = Aer.get_backend(backend_name)
                
            self._available = True
        except ImportError:
            self._available = False
            print("警告: Qiskit未找到，此后端不可用")
    
    def create_circuit(self, num_qubits: int, num_clbits: int) -> Any:
        if not self._available:
            return None
        return self.QuantumCircuit(num_qubits, num_clbits)
    
    def apply_rx(self, circuit: Any, qubit: int, theta: float) -> None:
        if circuit is not None:
            circuit.rx(theta, qubit)
    
    def apply_ry(self, circuit: Any, qubit: int, theta: float) -> None:
        if circuit is not None:
            circuit.ry(theta, qubit)
    
    def apply_rz(self, circuit: Any, qubit: int, theta: float) -> None:
        if circuit is not None:
            circuit.rz(theta, qubit)
    
    def apply_cnot(self, circuit: Any, control: int, target: int) -> None:
        if circuit is not None:
            circuit.cx(control, target)
    
    def measure_all(self, circuit: Any) -> None:
        if circuit is not None:
            circuit.measure_all()
    
    def run_circuit(self, circuit: Any, shots: int, seed: Optional[int] = None) -> Dict[str, int]:
        if not self._available or circuit is None:
            return {}
        try:
            # 编译电路
            compiled_circuit = self.transpile(circuit, self.backend)
            # 设置随机数种子
            if seed is not None:
                job = self.execute(compiled_circuit, self.backend, shots=shots, seed_simulator=seed)
            else:
                job = self.execute(compiled_circuit, self.backend, shots=shots)
            # 获取结果
            result = job.result()
            counts = result.get_counts(compiled_circuit)
            return counts
        except Exception as e:
            print(f"运行Qiskit电路时出错: {e}")
            return {}
    
    def is_available(self) -> bool:
        return self._available


class PaddleQuantumAdapter(QuantumBackendAdapter):
    """
    PaddleQuantum量子后端适配器
    """
    
    def __init__(self):
        """
        初始化PaddleQuantum适配器
        """
        try:
            import paddle
            import paddle_quantum
            from paddle_quantum.circuit import UAnsatz
            from paddle_quantum.state import State
            
            self.paddle = paddle
            self.paddle_quantum = paddle_quantum
            self.UAnsatz = UAnsatz
            self.State = State
            self._available = True
        except ImportError:
            self._available = False
            print("警告: PaddleQuantum未找到，此后端不可用")
    
    def create_circuit(self, num_qubits: int, num_clbits: int) -> Any:
        if not self._available:
            return None
        # PaddleQuantum使用UAnsatz作为电路
        circuit = self.UAnsatz(num_qubits)
        # 存储经典比特数量供后续使用
        circuit.num_clbits = num_clbits
        return circuit
    
    def apply_rx(self, circuit: Any, qubit: int, theta: float) -> None:
        if circuit is not None:
            circuit.rx(theta, qubit)
    
    def apply_ry(self, circuit: Any, qubit: int, theta: float) -> None:
        if circuit is not None:
            circuit.ry(theta, qubit)
    
    def apply_rz(self, circuit: Any, qubit: int, theta: float) -> None:
        if circuit is not None:
            circuit.rz(theta, qubit)
    
    def apply_cnot(self, circuit: Any, control: int, target: int) -> None:
        if circuit is not None:
            circuit.cnot([control, target])
    
    def measure_all(self, circuit: Any) -> None:
        # PaddleQuantum在运行时进行测量，这里不需要显式添加测量门
        pass
    
    def run_circuit(self, circuit: Any, shots: int, seed: Optional[int] = None) -> Dict[str, int]:
        if not self._available or circuit is None:
            return {}
        try:
            # 设置随机数种子
            if seed is not None:
                self.paddle.seed(seed)
                
            # 创建初始态|0...0⟩
            init_state = self.State(circuit.num_qubits)
            # 应用电路
            final_state = circuit(init_state)
            # 获取采样结果
            counts = final_state.measure(shots=shots)
            # 转换为与其他后端一致的格式
            return {format(k, f'0{circuit.num_qubits}b'): v for k, v in counts.items()}
        except Exception as e:
            print(f"运行PaddleQuantum电路时出错: {e}")
            return {}
    
    def is_available(self) -> bool:
        return self._available


class UQHash:
    """
    通用量子哈希函数 (Universal Quantum Hash)
    
    UQHash是一个可配置的量子哈希函数，能够使用不同的量子计算后端，
    包括模拟器和真实量子设备。它基于量子电路的概率分布特性生成
    确定性哈希值，可用于向量数据库的索引构建。
    """

    def __init__(self, config_path: Optional[str] = None, 
                 backend: Optional[str] = None,
                 num_qubits: int = 8, 
                 depth: int = 3, 
                 shots: int = 1024):
        """
        初始化UQHash量子哈希函数
        
        Args:
            config_path: 配置文件路径，默认为None（使用默认配置）
            backend: 后端名称，如果指定则覆盖配置文件中的设置
            num_qubits: 量子比特数量，决定了哈希空间的大小
            depth: 量子电路深度，影响哈希的复杂性
            shots: 量子测量次数，影响概率分布的精度
        """
        self.num_qubits = num_qubits
        self.depth = depth
        self.shots = shots
        
        # 加载配置
        self.config = self._load_config(config_path)
        
        # 如果指定了后端，覆盖配置
        if backend is not None:
            self.config['backend'] = backend