# SVDB - Quantum Vector Database

## Project Overview

SVDB (StateVector Database) is a vector database system based on quantum computing principles, designed for efficient processing and retrieval of multimodal data. The system utilizes quantum hash tiny-pointer technology to build indexes and implements efficient queries through the quantum Grover algorithm.

## Core Features

- **Multimodal Data Support**: Process various data types including documents, images, videos, and audio
- **Quantum Hash Indexing**: Generate tiny pointers using PTHash quantum hash function
- **Universal Quantum Hash Adaptation Layer**: UQHash interface supporting multiple quantum computing platforms
- **Efficient Vector Storage**: Optimized vector data storage structure
- **Quantum Search Algorithm**: Efficient query mechanism based on Grover algorithm
- **Metadata Management**: Comprehensive metadata indexing system
- **Performance Statistics**: Detailed system performance monitoring
- **Index Update Logging**: Reliable index change recording

## System Architecture

SVDB consists of the following eight core modules:

1. **UQHash**: Universal Quantum Hash adaptation layer, providing a unified interface for different quantum computing platforms
2. **PTHash**: Quantum hash function module, responsible for generating deterministic quantum hash values
3. **StateVector_storage**: Vector data storage module, managing the storage and retrieval of vector data
4. **Quan_Tiny-pointer_Hash_index**: Quantum tiny-pointer hash index module, implementing efficient vector indexing
5. **Grover**: Quantum Grover algorithm query module, providing quantum-accelerated search functionality
6. **metadata_index**: Metadata index module, managing metadata associated with vectors
7. **statistics**: Statistics module, collecting and analyzing system performance data
8. **index_update_log**: Index update log module, recording the change history of indexes

## Module Relationships

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

## Data Flow

1. Input data (documents, images, videos, audio) is converted to vector representation through appropriate encoders
2. UQHash module serves as a universal quantum computing adaptation layer, providing a unified interface for different quantum computing platforms
3. PTHash module utilizes the quantum computing capabilities provided by UQHash to generate quantum hash tiny pointers for vectors
4. Vector data and hash pointers are stored in the StateVector_storage module
5. Quan_Tiny-pointer_Hash_index module builds and maintains the index structure
6. During queries, quantum-accelerated searches are implemented through the Grover module
7. metadata_index module manages metadata associated with retrieval results
8. statistics module records system performance metrics
9. index_update_log module tracks all changes to the index

## Directory Structure

```
SVDB/
├── README.md                 # Project documentation (Chinese)
├── README_EN.md              # Project documentation (English)
├── __init__.py               # Package initialization file
├── config.py                 # Configuration file
├── requirements.txt          # Dependency list
├── UQHash/                   # Universal Quantum Hash adaptation layer
│   ├── __init__.py
│   ├── UQHash.py             # UQHash core implementation
│   ├── uqhash_config.json    # UQHash configuration file
│   └── uqhash_adapters.py    # Custom adapter examples
├── PTHash/                   # Quantum hash function module
│   ├── __init__.py
│   ├── pthash.py             # PTHash core implementation
│   └── quantum_circuit.py    # Quantum circuit generator
├── StateVector_storage/      # Vector data storage module
│   ├── __init__.py
│   ├── vector_store.py       # Vector storage core
│   └── data_loader.py        # Data loading tools
├── Quan_Tiny_pointer_Hash_index/ # Quantum tiny-pointer hash index module
│   ├── __init__.py
│   ├── hash_bucket.py        # Hash bucket implementation
│   └── index_builder.py      # Index builder
├── Grover/                   # Quantum Grover algorithm query module
│   ├── __init__.py
│   ├── grover_search.py      # Grover search algorithm
│   └── quantum_oracle.py     # Quantum oracle
├── metadata_index/           # Metadata index module
│   ├── __init__.py
│   ├── metadata_store.py     # Metadata storage
│   └── metadata_indexer.py   # Metadata indexer
├── statistics/               # Statistics module
│   ├── __init__.py
│   ├── performance_monitor.py # Performance monitoring
│   └── metrics_collector.py  # Metrics collector
├── index_update_log/         # Index update log module
│   ├── __init__.py
│   ├── log_manager.py        # Log manager
│   └── change_tracker.py     # Change tracker
└── utils/                    # Common utilities
    ├── __init__.py
    ├── data_processors/      # Data processors
    │   ├── __init__.py
    │   ├── text_processor.py # Text processing
    │   ├── image_processor.py # Image processing
    │   ├── video_processor.py # Video processing
    │   └── audio_processor.py # Audio processing
    └── common.py             # Common functions
```

## Installation and Usage

### Installation via pip

```bash
# Install from PyPI
pip install svdb

# Or install from GitHub source
pip install git+https://github.com/username/SVDB.git
```

### Installing Dependencies

```bash
pip install -r requirements.txt
```

### System Requirements

- Python 3.8 or higher
- Quantum computing environment (e.g., Qiskit, pyquafu，Cirq)

### Basic Usage

```python
from SVDB import SVDB

# Initialize database
db = SVDB(db_path="path/to/database")

# Store document
doc_id = db.store_document("path/to/document.pdf")

# Store image
image_id = db.store_image("path/to/image.jpg")

# Store video
video_id = db.store_video("path/to/video.mp4")

# Store audio
audio_id = db.store_audio("path/to/audio.mp3")

# Query
results = db.search("query content", top_k=5)

# Get statistics
stats = db.get_statistics()

# View index update logs
logs = db.get_index_update_logs(start_time, end_time)
```

## Contribution

Contributions, issue reports, and improvement suggestions are welcome.

## License

[MIT License](LICENSE)