# index_update_log - 日志管理器实现

import os
import json
import time
import uuid
import sqlite3

class LogManager:
    """
    日志管理器类，负责记录索引更新日志
    
    LogManager提供可靠的索引变更记录功能，支持操作审计和状态跟踪。
    它使用SQLite数据库存储日志记录，确保日志的持久性和查询效率。
    """
    
    def __init__(self, db_path):
        """
        初始化日志管理器
        
        Args:
            db_path: 数据库存储路径
        """
        self.db_path = db_path.replace('.pkl', '.log.db')
        self.conn = None
        
        # 初始化数据库连接
        self._init_db()
    
    def _init_db(self):
        """
        初始化SQLite数据库
        """
        # 确保数据库目录存在
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # 连接数据库
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()
        
        # 创建操作日志表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS operations (
            operation_id TEXT PRIMARY KEY,
            operation_type TEXT,
            start_time REAL,
            end_time REAL,
            status TEXT,
            details_json TEXT
        )
        """)
        
        # 创建索引更新日志表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS index_updates (
            update_id TEXT PRIMARY KEY,
            operation_id TEXT,
            item_id TEXT,
            action TEXT,
            bucket_id TEXT,
            timestamp REAL,
            details_json TEXT,
            FOREIGN KEY (operation_id) REFERENCES operations(operation_id)
        )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_operation_type ON operations(operation_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_operation_status ON operations(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_operation_time ON operations(start_time)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_update_item ON index_updates(item_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_update_action ON index_updates(action)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_update_time ON index_updates(timestamp)")
        
        # 提交更改
        self.conn.commit()
    
    def start_operation(self, operation_type):
        """
        记录操作开始
        
        Args:
            operation_type: 操作类型
            
        Returns:
            operation_id: 操作ID
        """
        if self.conn is None:
            self._init_db()
        
        # 生成唯一操作ID
        operation_id = str(uuid.uuid4())
        
        # 记录操作开始
        cursor = self.conn.cursor()
        cursor.execute("""
        INSERT INTO operations (
            operation_id, operation_type, start_time, status
        ) VALUES (?, ?, ?, ?)
        """, (operation_id, operation_type, time.time(), "running"))
        
        # 提交更改
        self.conn.commit()
        
        return operation_id
    
    def end_operation(self, operation_id, status="success", details=None):
        """
        记录操作结束
        
        Args:
            operation_id: 操作ID
            status: 操作状态（success, failed, canceled）
            details: 操作详情
            
        Returns:
            success: 布尔值，表示记录是否成功
        """
        if self.conn is None:
            self._init_db()
        
        # 记录操作结束
        cursor = self.conn.cursor()
        details_json = json.dumps(details) if details is not None else None
        
        cursor.execute("""
        UPDATE operations SET 
            end_time = ?,
            status = ?,
            details_json = ?
        WHERE operation_id = ?
        """, (time.time(), status, details_json, operation_id))
        
        # 提交更改
        self.conn.commit()
        
        return cursor.rowcount > 0
    
    def log_index_update(self, operation_id, item_id, action, bucket_id=None, details=None):
        """
        记录索引更新
        
        Args:
            operation_id: 操作ID
            item_id: 项目ID
            action: 更新动作（add, remove, update）
            bucket_id: 哈希桶ID
            details: 更新详情
            
        Returns:
            update_id: 更新ID
        """
        if self.conn is None:
            self._init_db()
        
        # 生成唯一更新ID
        update_id = str(uuid.uuid4())
        
        # 记录索引更新
        cursor = self.conn.cursor()
        details_json = json.dumps(details) if details is not None else None
        
        cursor.execute("""
        INSERT INTO index_updates (
            update_id, operation_id, item_id, action, bucket_id, timestamp, details_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (update_id, operation_id, item_id, action, bucket_id, time.time(), details_json))
        
        # 提交更改
        self.conn.commit()
        
        return update_id
    
    def get_operation_logs(self, operation_type=None, status=None, start_time=None, end_time=None, limit=100):
        """
        获取操作日志
        
        Args:
            operation_type: 操作类型
            status: 操作状态
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回结果数量限制
            
        Returns:
            logs: 操作日志列表
        """
        if self.conn is None:
            self._init_db()
        
        # 构建查询条件
        query = "SELECT * FROM operations WHERE 1=1"
        params = []
        
        if operation_type is not None:
            query += " AND operation_type = ?"
            params.append(operation_type)
        
        if status is not None:
            query += " AND status = ?"
            params.append(status)
        
        if start_time is not None:
            query += " AND start_time >= ?"
            params.append(start_time)
        
        if end_time is not None:
            query += " AND start_time <= ?"
            params.append(end_time)
        
        query += " ORDER BY start_time DESC LIMIT ?"
        params.append(limit)
        
        # 执行查询
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        
        # 处理结果
        logs = []
        for row in cursor.fetchall():
            operation_id, operation_type, start_time, end_time, status, details_json = row
            log = {
                'operation_id': operation_id,
                'operation_type': operation_type,
                'start_time': start_time,
                'end_time': end_time,
                'status': status,
                'details': json.loads(details_json) if details_json else None
            }
            logs.append(log)
        
        return logs
    
    def get_index_update_logs(self, item_id=None, action=None, start_time=None, end_time=None, limit=100):
        """
        获取索引更新日志
        
        Args:
            item_id: 项目ID
            action: 更新动作
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回结果数量限制
            
        Returns:
            logs: 索引更新日志列表
        """
        if self.conn is None:
            self._init_db()
        
        # 构建查询条件
        query = "SELECT * FROM index_updates WHERE 1=1"
        params = []
        
        if item_id is not None:
            query += " AND item_id = ?"
            params.append(item_id)
        
        if action is not None:
            query += " AND action = ?"
            params.append(action)
        
        if start_time is not None:
            query += " AND timestamp >= ?"
            params.append(start_time)
        
        if end_time is not None:
            query += " AND timestamp <= ?"
            params.append(end_time)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        # 执行查询
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        
        # 处理结果
        logs = []
        for row in cursor.fetchall():
            update_id, operation_id, item_id, action, bucket_id, timestamp, details_json = row
            log = {
                'update_id': update_id,
                'operation_id': operation_id,
                'item_id': item_id,
                'action': action,
                'bucket_id': bucket_id,
                'timestamp': timestamp,
                'details': json.loads(details_json) if details_json else None
            }
            logs.append(log)
        
        return logs
    
    def get_logs(self, start_time=None, end_time=None, limit=100):
        """
        获取所有日志
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回结果数量限制
            
        Returns:
            logs: 包含操作日志和索引更新日志的字典
        """
        operation_logs = self.get_operation_logs(start_time=start_time, end_time=end_time, limit=limit)
        update_logs = self.get_index_update_logs(start_time=start_time, end_time=end_time, limit=limit)
        
        return {
            'operations': operation_logs,
            'index_updates': update_logs
        }
    
    def get_current_time(self):
        """
        获取当前时间
        
        Returns:
            timestamp: 当前时间戳
        """
        return time.time()
    
    def close(self):
        """
        关闭日志管理器
        """
        if self.conn is not None:
            self.conn.close()
            self.conn = None
            print(f"日志管理器已关闭: {self.db_path}")