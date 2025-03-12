# 查询SVDB中特定项目ID对应的文摘内容

import os
import sys

# 添加父目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# 导入SVDB模块
from SVDB import SVDB

# 设置数据库路径
db_path = os.path.join(os.path.dirname(__file__), 'data', 'tiny_pointer_db')

# 要查询的项目ID列表
item_ids = [
    '0c158c24-55d5-4867-aed5-9cb4d0bccf46',
    'b891496d-9003-4b6d-a1b6-f1bea0a4c2a2'
]

def retrieve_content():
    """查询特定项目ID对应的文摘内容"""
    print("初始化SVDB...")
    db = SVDB(db_path, num_qubits=8, depth=3)
    
    print("\n查询项目ID对应的文摘内容:")
    for i, item_id in enumerate(item_ids):
        print(f"\n项目 {i+1}:")
        print(f"项目ID: {item_id}")
        
        # 获取元数据和内容
        metadata_info = db.metadata_store.retrieve(item_id)
        
        if metadata_info:
            metadata, content = metadata_info
            print(f"元数据: {metadata}")
            
            if content:
                if isinstance(content, list):
                    # 如果内容是列表，显示第一个元素
                    print(f"\n文摘内容:\n{content[0]}")
                else:
                    # 否则直接显示内容
                    print(f"\n文摘内容:\n{content}")
            else:
                print("无内容数据")
        else:
            print(f"未找到项目ID为 {item_id} 的数据")
    
    # 关闭数据库
    db.close()

if __name__ == "__main__":
    retrieve_content()