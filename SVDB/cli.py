#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SVDB命令行接口
提供命令行工具用于管理和操作SVDB数据库
"""

import argparse
import os
import sys
from SVDB import SVDB, __version__


def main():
    """SVDB命令行工具的主入口点"""
    parser = argparse.ArgumentParser(
        description="SVDB - 量子向量数据库命令行工具",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--version', '-v',
        action='version',
        version=f'SVDB v{__version__}'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 初始化数据库命令
    init_parser = subparsers.add_parser('init', help='初始化新的SVDB数据库')
    init_parser.add_argument('db_path', help='数据库存储路径')
    init_parser.add_argument('--qubits', type=int, default=8, help='量子比特数量')
    init_parser.add_argument('--depth', type=int, default=3, help='量子电路深度')
    init_parser.add_argument('--clear', action='store_true', help='清除现有数据库内容')
    
    # 存储文档命令
    store_parser = subparsers.add_parser('store', help='存储文档到数据库')
    store_parser.add_argument('db_path', help='数据库存储路径')
    store_parser.add_argument('doc_path', help='文档路径')
    store_parser.add_argument('--chunk-size', type=int, default=1000, help='文本分块大小')
    store_parser.add_argument('--overlap', type=int, default=200, help='文本分块重叠大小')
    
    # 搜索命令
    search_parser = subparsers.add_parser('search', help='在数据库中搜索')
    search_parser.add_argument('db_path', help='数据库存储路径')
    search_parser.add_argument('query', help='搜索查询')
    search_parser.add_argument('--top-k', type=int, default=5, help='返回结果数量')
    search_parser.add_argument('--quantum', action='store_true', help='使用量子Grover算法')
    
    # 统计命令
    stats_parser = subparsers.add_parser('stats', help='显示数据库统计信息')
    stats_parser.add_argument('db_path', help='数据库存储路径')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        if args.command == 'init':
            db = SVDB(args.db_path, num_qubits=args.qubits, depth=args.depth, clear_existing=args.clear)
            print(f"已成功初始化SVDB数据库于: {args.db_path}")
            db.close()
            
        elif args.command == 'store':
            db = SVDB(args.db_path)
            doc_id = db.store_document(args.doc_path, chunk_size=args.chunk_size, overlap=args.overlap)
            print(f"文档已存储，ID: {doc_id}")
            db.close()
            
        elif args.command == 'search':
            db = SVDB(args.db_path)
            results = db.search(query=args.query, top_k=args.top_k, use_quantum=args.quantum)
            
            print("\n搜索结果:")
            for i, result in enumerate(results):
                print(f"\n结果 {i+1}:")
                if isinstance(result, tuple):
                    if len(result) == 2:
                        item_id, score = result
                        print(f"项目ID: {item_id}")
                        print(f"相似度: {score:.4f}")
                        metadata_info = db.metadata_store.retrieve(item_id)
                        if metadata_info:
                            metadata, content = metadata_info
                            print(f"元数据: {metadata}")
                            if content:
                                if isinstance(content, list) and len(content) > 0:
                                    print(f"\n文摘内容:\n{content[0]}")
                                else:
                                    print(f"\n文摘内容:\n{content}")
                    elif len(result) == 3:
                        item_id, score, metadata = result
                        print(f"项目ID: {item_id}")
                        print(f"相似度: {score:.4f}")
                        print(f"元数据: {metadata}")
                else:
                    print(f"结果: {result}")
            db.close()
            
        elif args.command == 'stats':
            db = SVDB(args.db_path)
            stats = db.performance_monitor.get_stats()
            print("\n数据库统计信息:")
            for key, value in stats.items():
                if isinstance(value, float):
                    print(f"- {key}: {value:.3f}")
                else:
                    print(f"- {key}: {value}")
            db.close()
            
    except Exception as e:
        print(f"错误: {str(e)}")
        return 1
        
    return 0


if __name__ == "__main__":
    sys.exit(main())