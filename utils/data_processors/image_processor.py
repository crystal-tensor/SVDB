# 图像处理模块

import os
import numpy as np
from PIL import Image
from sentence_transformers import SentenceTransformer
import torch
from torchvision import transforms, models

# 预训练模型和转换器
image_transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

def load_image_model():
    """加载预训练的图像特征提取模型
    
    Returns:
        model: 预训练模型
    """
    # 使用预训练的ResNet模型
    model = models.resnet50(pretrained=True)
    # 移除最后的全连接层，只保留特征提取部分
    model = torch.nn.Sequential(*list(model.children())[:-1])
    model.eval()
    return model

def extract_features_from_image(image_path, model=None):
    """从图像中提取特征向量
    
    Args:
        image_path: 图像文件路径
        model: 预训练模型（如果为None则加载默认模型）
        
    Returns:
        features: 图像特征向量
    """
    try:
        # 加载图像
        image = Image.open(image_path).convert('RGB')
        
        # 应用转换
        image_tensor = image_transform(image).unsqueeze(0)
        
        # 如果没有提供模型，加载默认模型
        if model is None:
            model = load_image_model()
        
        # 提取特征
        with torch.no_grad():
            features = model(image_tensor)
            features = features.squeeze().flatten().numpy()
        
        return features
    except Exception as e:
        print(f"提取图像特征时出错: {e}")
        return None

def process_image(image_path, hasher):
    """处理图像并生成向量表示
    
    Args:
        image_path: 图像文件路径
        hasher: 哈希器实例
        
    Returns:
        features: 图像特征向量
        pointer: 量子哈希指针
    """
    # 提取图像特征
    features = extract_features_from_image(image_path)
    if features is None:
        return None, None
    
    # 生成量子哈希微小指针
    # 将特征向量转换为字符串表示，用于哈希
    feature_str = ",".join([str(x) for x in features[:100]])  # 使用前100个特征
    pointer = hasher.hash_to_vector(feature_str)
    
    return features, pointer

def text_to_image_search(text, model=None):
    """将文本查询转换为图像搜索向量
    
    Args:
        text: 查询文本
        model: 文本-图像联合嵌入模型（如果为None则加载默认模型）
        
    Returns:
        embedding: 查询向量
    """
    # 使用CLIP或类似模型将文本映射到图像空间
    # 这里使用sentence-transformers作为简化实现
    if model is None:
        model = SentenceTransformer('clip-ViT-B-32')
    
    embedding = model.encode(text)
    return embedding