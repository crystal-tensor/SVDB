# statistics - 性能监控实现

import time
import threading
import os
import psutil
import json
from collections import defaultdict, deque

class PerformanceMonitor:
    """
    性能监控类，负责收集和分析系统性能指标
    
    PerformanceMonitor提供实时的性能监控功能，记录系统资源使用情况、
    操作耗时和吞吐量等指标，帮助优化SVDB的运行状态。
    """
    
    def __init__(self, stats_file=None, monitor_interval=5.0):
        """
        初始化性能监控器
        
        Args:
            stats_file: 统计信息文件路径
            monitor_interval: 监控间隔（秒）
        """
        self.stats_file = stats_file
        self.monitor_interval = monitor_interval
        self.monitoring = False
        self.monitor_thread = None
        
        # 统计数据
        self.stats = {
            'start_time': time.time(),
            'uptime': 0,
            'operations': defaultdict(int),
            'timers': defaultdict(list),
            'system_stats': [],
            'current_memory': 0,
            'peak_memory': 0,
            'total_queries': 0,
            'avg_query_time': 0,
            'total_items': 0
        }
        
        # 查询时间窗口（用于计算平均查询时间）
        self.query_times = deque(maxlen=100)
        
        # 加载现有统计数据
        if stats_file and os.path.exists(stats_file):
            try:
                with open(stats_file, 'r') as f:
                    saved_stats = json.load(f)
                    # 合并保存的统计数据
                    for key, value in saved_stats.items():
                        if key != 'start_time':
                            self.stats[key] = value
            except Exception as e:
                print(f"加载统计数据时出错: {e}")
    
    def start_monitoring(self):
        """
        启动性能监控
        """
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("性能监控已启动")
    
    def stop_monitoring(self):
        """
        停止性能监控
        """
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
            self.monitor_thread = None
        
        # 保存统计数据
        self._save_stats()
        print("性能监控已停止")
    
    def update_stats(self, operation_name):
        """
        更新操作统计信息
        
        Args:
            operation_name: 操作名称
        """
        self.stats['operations'][operation_name] += 1
        
        # 更新总项目数
        if operation_name.endswith('_stored'):
            self.stats['total_items'] += 1
        
        # 更新总查询数
        if operation_name == 'search_performed':
            self.stats['total_queries'] += 1
    
    def start_timer(self, operation_name):
        """
        启动操作计时器
        
        Args:
            operation_name: 操作名称
            
        Returns:
            start_time: 开始时间
        """
        return time.time()
    
    def end_timer(self, operation_name, start_time):
        """
        结束操作计时器并记录耗时
        
        Args:
            operation_name: 操作名称
            start_time: 开始时间
            
        Returns:
            elapsed: 耗时（秒）
        """
        elapsed = time.time() - start_time
        self.stats['timers'][operation_name].append(elapsed)
        
        # 如果是搜索操作，更新查询时间窗口
        if operation_name == 'search':
            self.query_times.append(elapsed)
            self.stats['avg_query_time'] = sum(self.query_times) / len(self.query_times)
        
        return elapsed
    
    def get_stats(self):
        """
        获取统计信息
        
        Returns:
            stats: 统计信息字典
        """
        # 更新运行时间
        self.stats['uptime'] = time.time() - self.stats['start_time']
        
        # 计算平均操作时间
        avg_times = {}
        for op_name, times in self.stats['timers'].items():
            if times:
                avg_times[op_name] = sum(times) / len(times)
        
        # 构建返回结果
        result = {
            'uptime': self.stats['uptime'],
            'operations': dict(self.stats['operations']),
            'avg_times': avg_times,
            'current_memory': self.stats['current_memory'],
            'peak_memory': self.stats['peak_memory'],
            'total_queries': self.stats['total_queries'],
            'avg_query_time': self.stats['avg_query_time'],
            'total_items': self.stats['total_items']
        }
        
        return result
    
    def _monitor_loop(self):
        """
        监控循环，定期收集系统资源使用情况
        """
        process = psutil.Process(os.getpid())
        
        while self.monitoring:
            try:
                # 收集内存使用情况
                memory_info = process.memory_info()
                current_memory = memory_info.rss / (1024 * 1024)  # MB
                
                # 更新统计数据
                self.stats['current_memory'] = current_memory
                self.stats['peak_memory'] = max(self.stats['peak_memory'], current_memory)
                
                # 收集CPU使用情况
                cpu_percent = process.cpu_percent(interval=0.1)
                
                # 收集系统状态
                system_stat = {
                    'timestamp': time.time(),
                    'memory_mb': current_memory,
                    'cpu_percent': cpu_percent
                }
                
                # 添加到系统统计数据（保留最近100条记录）
                self.stats['system_stats'].append(system_stat)
                if len(self.stats['system_stats']) > 100:
                    self.stats['system_stats'] = self.stats['system_stats'][-100:]
                
                # 定期保存统计数据
                if self.stats_file and time.time() % 60 < self.monitor_interval:
                    self._save_stats()
                
            except Exception as e:
                print(f"监控过程中出错: {e}")
            
            # 等待下一个监控间隔
            time.sleep(self.monitor_interval)
    
    def _save_stats(self):
        """
        保存统计数据到文件
        """
        if not self.stats_file:
            return
        
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.stats_file), exist_ok=True)
            
            # 保存统计数据
            with open(self.stats_file, 'w') as f:
                # 将defaultdict转换为普通dict
                serializable_stats = self.stats.copy()
                serializable_stats['operations'] = dict(serializable_stats['operations'])
                serializable_stats['timers'] = {k: list(v) for k, v in serializable_stats['timers'].items()}
                
                json.dump(serializable_stats, f, indent=2)
        except Exception as e:
            print(f"保存统计数据时出错: {e}")