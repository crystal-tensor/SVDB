from setuptools import setup, find_packages
import os

# 读取版本信息
with open(os.path.join('SVDB', '__init__.py'), 'r', encoding='utf-8') as f:
    for line in f:
        if line.startswith('__version__'):
            version = line.split('=')[1].strip().strip('\'"')
            break

# 读取README作为长描述
with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

# 读取依赖项
with open('requirements.txt', 'r', encoding='utf-8') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name='svdb',
    version=version,
    description='量子向量数据库 - 基于量子计算原理的向量数据库系统',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Crystal Tensor',
    author_email='crystal-tensor@example.com',  # 请替换为您的实际邮箱
    url='https://github.com/crystal-tensor/SVDB',
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Database :: Database Engines/Servers',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords='quantum, vector database, embedding, search, grover algorithm',
    python_requires='>=3.8',
    entry_points={
        'console_scripts': [
            'svdb=SVDB.cli:main',
        ],
    },
)