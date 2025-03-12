# SVDB - 量子向量数据库

## 项目概述

SVDB（StateVector Database）是一个基于量子计算原理的向量数据库系统，专为高效处理和检索多模态数据而设计。该系统利用量子哈希微小指针技术构建索引，并通过量子Grover算法实现高效查询。

## 核心特性

- **多模态数据支持**：处理文档、图片、视频、音频等多种数据类型
- **量子哈希索引**：使用PTHash量子哈希函数生成微小指针
- **通用量子哈希适配层**：支持多种量子计算平台的UQHash接口
- **高效向量存储**：优化的向量数据存储结构
- **量子搜索算法**：基于Grover算法的高效查询机制
- **元数据管理**：完善的元数据索引系统
- **性能统计**：详细的系统性能监控
- **索引更新日志**：可靠的索引变更记录

## 系统架构

SVDB由以下八个核心模块组成：

1. **UQHash**：通用量子哈希适配层，为不同量子计算平台提供统一接口
2. **PTHash**：量子哈希函数模块，负责生成确定性量子哈希值
3. **StateVector_storage**：向量数据存储模块，管理向量数据的存储和检索
4. **Quan_Tiny-pointer_Hash_index**：量子微小指针哈希索引模块，实现高效的向量索引
5. **Grover**：量子Grover算法查询模块，提供量子加速的搜索功能
6. **metadata_index**：元数据索引模块，管理与向量关联的元数据
7. **statistics**：统计信息模块，收集和分析系统性能数据
8. **index_update_log**：索引更新日志模块，记录索引的变更历史

## 模块关系

```
+-------------+      +-------------+      +-------------------+      +-------------------------+
|   UQHash    |----->|   PTHash    |----->| StateVector_storage |----->| Quan_Tiny-pointer_Hash_index |
+-------------+      +-------------+      +-------------------+      +-------------------------+
                           |                      |                             |
                           |                      |                             |
                           v                      v                             v
                     +-------------+      +-------------------+      +-------------------------+
                     |   Grover    |<---->| metadata_index    |<---->|      statistics         |
                     +-------------+      +-------------------+      +-------------------------+
                                                  |
                                                  |
                                                  v
                                          +-------------------+
                                          | index_update_log  |
                                          +-------------------+
```

## 数据流程

1. 输入数据（文档、图片、视频、音频）通过适当的编码器转换为向量表示
2. UQHash模块作为通用量子计算适配层，为不同的量子计算平台提供统一接口
3. PTHash模块利用UQHash提供的量子计算能力为向量生成量子哈希微小指针
4. 向量数据和哈希指针存储在StateVector_storage模块中
5. Quan_Tiny-pointer_Hash_index模块构建和维护索引结构
6. 查询时，通过Grover模块实现量子加速搜索
7. metadata_index模块管理与检索结果关联的元数据
8. statistics模块记录系统性能指标
9. index_update_log模块跟踪索引的所有变更

## 目录结构

```
SVDB/
├── README.md                 # 项目说明文档
├── __init__.py               # 包初始化文件
├── config.py                 # 配置文件
├── requirements.txt          # 依赖包列表
├── UQHash/                   # 通用量子哈希适配层
│   ├── __init__.py
│   ├── UQHash.py             # UQHash核心实现
│   ├── uqhash_config.json    # UQHash配置文件
│   └── uqhash_adapters.py    # 自定义适配器示例
├── PTHash/                   # 量子哈希函数模块
│   ├── __init__.py
│   ├── pthash.py             # PTHash核心实现
│   └── quantum_circuit.py    # 量子电路生成器
├── StateVector_storage/      # 向量数据存储模块
│   ├── __init__.py
│   ├── vector_store.py       # 向量存储核心
│   └── data_loader.py        # 数据加载工具
├── Quan_Tiny_pointer_Hash_index/ # 量子微小指针哈希索引模块
│   ├── __init__.py
│   ├── hash_bucket.py        # 哈希桶实现
│   └── index_builder.py      # 索引构建器
├── Grover/                   # 量子Grover算法查询模块
│   ├── __init__.py
│   ├── grover_search.py      # Grover搜索算法
│   └── quantum_oracle.py     # 量子预言机
├── metadata_index/           # 元数据索引模块
│   ├── __init__.py
│   ├── metadata_store.py     # 元数据存储
│   └── metadata_indexer.py   # 元数据索引器
├── statistics/               # 统计信息模块
│   ├── __init__.py
│   ├── performance_monitor.py # 性能监控
│   └── metrics_collector.py  # 指标收集器
├── index_update_log/         # 索引更新日志模块
│   ├── __init__.py
│   ├── log_manager.py        # 日志管理器
│   └── change_tracker.py     # 变更跟踪器
└── utils/                    # 通用工具
    ├── __init__.py
    ├── data_processors/      # 数据处理器
    │   ├── __init__.py
    │   ├── text_processor.py # 文本处理
    │   ├── image_processor.py # 图像处理
    │   ├── video_processor.py # 视频处理
    │   └── audio_processor.py # 音频处理
    └── common.py             # 通用函数
```

## 安装与使用

### 通过pip安装

```bash
# 从PyPI安装
pip install svdb

# 或从GitHub源码安装
pip install git+https://github.com/username/SVDB.git
```

### 安装依赖

```bash
pip install -r requirements.txt
```

### 系统要求

- Python 3.8 或更高版本
- 支持量子计算的环境（如Qiskit、Pyquafu，Cirq等）

### 基本使用

```python
from SVDB import SVDB

# 初始化数据库
db = SVDB(db_path="path/to/database")

# 存储文档
doc_id = db.store_document("path/to/document.pdf")

# 存储图像
image_id = db.store_image("path/to/image.jpg")

# 存储视频
video_id = db.store_video("path/to/video.mp4")

# 存储音频
audio_id = db.store_audio("path/to/audio.mp3")

# 查询
results = db.search("查询内容", top_k=5)

# 获取统计信息
stats = db.get_statistics()

# 查看索引更新日志
logs = db.get_index_update_logs(start_time, end_time)
```

## 贡献

欢迎贡献代码、报告问题或提出改进建议。

## 许可证

[MIT License](LICENSE)