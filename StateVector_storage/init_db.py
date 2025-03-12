import sqlite3
import os

def init_database(db_path, clear_existing=False):
    """初始化向量数据库
    
    Args:
        db_path: 数据库文件路径
        clear_existing: 是否清除现有数据库内容
    """
    # 确保目录存在
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # 如果数据库文件已存在且不为空
    if os.path.exists(db_path) and os.path.getsize(db_path) > 0:
        if clear_existing:
            # 如果指定了清除现有数据，则删除数据库文件
            print(f"清除现有数据库内容: {db_path}")
            os.remove(db_path)
        else:
            try:
                # 尝试连接数据库验证其完整性
                test_conn = sqlite3.connect(db_path)
                test_cursor = test_conn.cursor()
                test_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                test_conn.close()
            except sqlite3.DatabaseError:
                # 数据库文件已损坏，删除它
                print(f"数据库文件已损坏，正在重新创建: {db_path}")
                os.remove(db_path)
    
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 创建向量表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vectors (
        id TEXT PRIMARY KEY,
        embeddings BLOB NOT NULL,
        pointers BLOB NOT NULL,
        timestamp REAL NOT NULL
    )
    """)
    
    # 创建元数据表 - 修改表结构以匹配 metadata_store.py 中的定义
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS metadata (
        item_id TEXT PRIMARY KEY,
        metadata_json TEXT,
        content_json TEXT,
        type TEXT,
        timestamp REAL,
        last_update REAL,
        FOREIGN KEY (item_id) REFERENCES vectors(id)
    )
    """)
    
    # 创建索引
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_vectors_timestamp ON vectors(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_metadata_timestamp ON metadata(timestamp)")
    
    # 提交更改
    conn.commit()
    conn.close()
    
    print(f"数据库初始化完成: {db_path}")