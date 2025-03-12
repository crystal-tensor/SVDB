# 视频处理模块

import os
import numpy as np
import cv2
from PIL import Image
import torch
from torchvision import transforms, models

# 导入图像处理模块以复用图像特征提取功能
from SVDB.utils.data_processors.image_processor import extract_features_from_image, load_image_model

def extract_frames(video_path, frame_interval=1):
    """从视频中提取帧
    
    Args:
        video_path: 视频文件路径
        frame_interval: 帧间隔（每隔多少帧提取一帧）
        
    Returns:
        frames: 提取的帧列表
    """
    frames = []
    try:
        # 打开视频文件
        video = cv2.VideoCapture(video_path)
        
        # 检查视频是否成功打开
        if not video.isOpened():
            print(f"无法打开视频: {video_path}")
            return frames
        
        # 获取视频信息
        fps = video.get(cv2.CAP_PROP_FPS)
        frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        
        print(f"视频信息: {frame_count} 帧, {fps} FPS, 时长 {duration:.2f} 秒")
        
        # 提取帧
        frame_idx = 0
        while True:
            ret, frame = video.read()
            if not ret:
                break
            
            if frame_idx % frame_interval == 0:
                # 转换BGR到RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames.append(frame_rgb)
            
            frame_idx += 1
        
        # 释放视频对象
        video.release()
        
        print(f"提取了 {len(frames)} 帧")
        return frames
    
    except Exception as e:
        print(f"提取视频帧时出错: {e}")
        return frames

def process_video(video_path, hasher, frame_interval=1):
    """处理视频并生成向量表示
    
    Args:
        video_path: 视频文件路径
        hasher: 哈希器实例
        frame_interval: 帧间隔
        
    Returns:
        frames: 提取的帧列表
        embeddings: 向量嵌入列表
        pointers: 量子哈希指针列表
    """
    # 提取视频帧
    frames = extract_frames(video_path, frame_interval)
    if not frames:
        return [], [], []
    
    # 加载图像模型
    model = load_image_model()
    
    # 为每一帧生成特征向量和哈希指针
    embeddings = []
    pointers = []
    
    for i, frame in enumerate(frames):
        print(f"处理帧 {i+1}/{len(frames)}...")
        
        # 将OpenCV帧转换为PIL图像
        pil_image = Image.fromarray(frame)
        
        # 保存临时图像文件
        temp_path = f"/tmp/frame_{i}.jpg"
        pil_image.save(temp_path)
        
        # 提取特征
        features = extract_features_from_image(temp_path, model)
        
        # 删除临时文件
        os.remove(temp_path)
        
        if features is not None:
            embeddings.append(features)
            
            # 生成量子哈希微小指针
            feature_str = ",".join([str(x) for x in features[:100]])  # 使用前100个特征
            pointer = hasher.hash_to_vector(feature_str)
            pointers.append(pointer)
    
    return frames, embeddings, pointers

def video_frame_to_embedding(frame, model=None):
    """将视频帧转换为向量表示
    
    Args:
        frame: 视频帧（numpy数组）
        model: 预训练模型（如果为None则加载默认模型）
        
    Returns:
        embedding: 帧向量表示
    """
    # 将numpy数组转换为PIL图像
    pil_image = Image.fromarray(frame)
    
    # 保存临时图像文件
    temp_path = "/tmp/temp_frame.jpg"
    pil_image.save(temp_path)
    
    # 提取特征
    features = extract_features_from_image(temp_path, model)
    
    # 删除临时文件
    os.remove(temp_path)
    
    return features