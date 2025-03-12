# metadata_index - 元数据存储实现

import os
import json
import time
import sqlite3

class MetadataStore:
    """
    元数据存储类，负责管理与向量关联的元数据
    
    MetadataStore提供高效的元数据存储和检索功能，支持结构化查询和全文搜索。
    它使用SQLite数据库存储元数据，提供高性能的索引和查询能力。
    """
    
    def __init__(self, db_path, clear_existing=False):
        """
        初始化元数据存储
        
        Args:
            db_path: 数据库存储路径
            clear_existing: 是否清除现有数据库内容
        """
        # 使用与向量存储相同的数据库文件
        self.db_path = db_path
        self.conn = None
        self.last_update = 0
        self.clear_existing = clear_existing
        
        # 初始化数据库连接
        self._init_db()
    
    def _init_db(self):
        """
        初始化SQLite数据库连接
        """
        # 确保数据库目录存在
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # 连接数据库 - 使用WAL模式提高并发性能
        self.conn = sqlite3.connect(self.db_path, isolation_level=None)
        self.conn.execute('PRAGMA journal_mode=WAL')
        self.cursor = self.conn.cursor()
    
    def store(self, item_id, metadata, content=None):
        """
        存储元数据
        
        Args:
            item_id: 项目ID
            metadata: 元数据字典
            content: 可选的内容数据
            
        Returns:
            success: 布尔值，表示存储是否成功
        """
        if self.conn is None:
            self._init_db()
        
        cursor = self.conn.cursor()
        
        # 准备数据
        timestamp = time.time()
        metadata_json = json.dumps(metadata, ensure_ascii=False)
        content_json = json.dumps(content, ensure_ascii=False) if content is not None else None
        item_type = metadata.get('type', 'unknown')
        
        # 检查项目是否已存在
        cursor.execute("SELECT item_id FROM metadata WHERE item_id = ?", (item_id,))
        exists = cursor.fetchone() is not None
        
        if exists:
            # 更新现有记录
            cursor.execute("""
            UPDATE metadata SET 
                metadata_json = ?,
                content_json = ?,
                type = ?,
                last_update = ?
            WHERE item_id = ?
            """, (metadata_json, content_json, item_type, timestamp, item_id))
        else:
            # 插入新记录
            cursor.execute("""
            INSERT INTO metadata (
                item_id, metadata_json, content_json, type, timestamp, last_update
            ) VALUES (?, ?, ?, ?, ?, ?)
            """, (item_id, metadata_json, content_json, item_type, timestamp, timestamp))
        
        # 提交更改
        self.conn.commit()
        
        # 更新最后修改时间
        self.last_update = timestamp
        
        return True
    
    def retrieve(self, item_id):
        """
        检索元数据
        
        Args:
            item_id: 项目ID
            
        Returns:
            tuple: (metadata, content) 或 None（如果ID不存在）
        """
        if self.conn is None:
            self._init_db()
        
        cursor = self.conn.cursor()
        
        # 查询记录
        cursor.execute("""
        SELECT metadata_json, content_json FROM metadata WHERE item_id = ?
        """, (item_id,))
        
        result = cursor.fetchone()
        if result is None:
            return None
        
        # 解析JSON数据
        metadata_json, content_json = result
        metadata = json.loads(metadata_json)
        content = json.loads(content_json) if content_json is not None else None
        
        return metadata, content
    
    def delete(self, item_id):
        """
        删除元数据
        
        Args:
            item_id: 项目ID
            
        Returns:
            success: 布尔值，表示删除是否成功
        """
        if self.conn is None:
            self._init_db()
        
        cursor = self.conn.cursor()
        
        # 删除记录
        cursor.execute("DELETE FROM metadata WHERE item_id = ?", (item_id,))
        
        # 提交更改
        self.conn.commit()
        
        # 更新最后修改时间
        self.last_update = time.time()
        
        return cursor.rowcount > 0
    
    def search_by_type(self, item_type, limit=100):
        """
        按类型搜索元数据
        
        Args:
            item_type: 项目类型
            limit: 返回结果数量限制
            
        Returns:
            results: 包含(item_id, metadata)元组的列表
        """
        if self.conn is None:
            self._init_db()
        
        cursor = self.conn.cursor()
        
        # 查询记录
        cursor.execute("""
        SELECT item_id, metadata_json FROM metadata WHERE type = ? ORDER BY timestamp DESC LIMIT ?
        """, (item_type, limit))
        
        results = []
        for item_id, metadata_json in cursor.fetchall():
            metadata = json.loads(metadata_json)
            results.append((item_id, metadata))
        
        return results
    
    def search_by_time_range(self, start_time=None, end_time=None, limit=100):
        """
        按时间范围搜索元数据
        
        Args:
            start_time: 开始时间戳
            end_time: 结束时间戳
            limit: 返回结果数量限制
            
        Returns:
            results: 包含(item_id, metadata)元组的列表
        """
        if self.conn is None:
            self._init_db()
        
        cursor = self.conn.cursor()
        
        # 构建查询条件
        query = "SELECT item_id, metadata_json FROM metadata WHERE 1=1"
        params = []
        
        if start_time is not None:
            query += " AND timestamp >= ?"
            params.append(start_time)
        
        if end_time is not None:
            query += " AND timestamp <= ?"
            params.append(end_time)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        # 执行查询
        cursor.execute(query, params)
        
        results = []
        for item_id, metadata_json in cursor.fetchall():
            metadata = json.loads(metadata_json)
            results.append((item_id, metadata))
        
        return results
    
    def get_all_metadata(self, limit=1000):
        """
        获取所有元数据
        
        Args:
            limit: 返回结果数量限制
            
        Returns:
            results: 包含(item_id, metadata)元组的列表
        """
        if self.conn is None:
            self._init_db()
        
        cursor = self.conn.cursor()
        
        # 查询记录
        cursor.execute("""
        SELECT item_id, metadata_json FROM metadata ORDER BY timestamp DESC LIMIT ?
        """, (limit,))
        
        results = []
        for item_id, metadata_json in cursor.fetchall():
            metadata = json.loads(metadata_json)
            results.append((item_id, metadata))
        
        return results
    
    def get_metadata_count(self):
        """
        获取元数据总数
        
        Returns:
            count: 元数据总数
        """
        if self.conn is None:
            self._init_db()
        
        cursor = self.conn.cursor()
        
        # 查询记录数
        cursor.execute("SELECT COUNT(*) FROM metadata")
        count = cursor.fetchone()[0]
        
        return count
    
    def get_last_update_time(self):
        """
        获取最后更新时间
        
        Returns:
            timestamp: 最后更新时间戳
        """
        return self.last_update
    
    def close(self):
        """
        关闭元数据存储
        """
        if self.conn is not None:
            self.conn.close()
            self.conn = None
            print(f"元数据存储已关闭: {self.db_path}")