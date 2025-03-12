# 音频处理模块

import os
import numpy as np
import librosa
from sentence_transformers import SentenceTransformer

def extract_audio_features(audio_path, sr=22050, n_fft=2048, hop_length=512):
    """从音频文件中提取特征
    
    Args:
        audio_path: 音频文件路径
        sr: 采样率
        n_fft: FFT窗口大小
        hop_length: 帧移
        
    Returns:
        features: 音频特征字典
    """
    try:
        # 加载音频文件
        y, sr = librosa.load(audio_path, sr=sr)
        
        # 提取特征
        # 1. 梅尔频谱图
        mel_spec = librosa.feature.melspectrogram(y=y, sr=sr, n_fft=n_fft, hop_length=hop_length)
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
        
        # 2. MFCC特征
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20)
        
        # 3. 色度特征
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        
        # 4. 光谱对比度
        contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
        
        # 5. 零交叉率
        zcr = librosa.feature.zero_crossing_rate(y)
        
        # 组合特征
        features = {
            'mel_spec': mel_spec_db,
            'mfcc': mfcc,
            'chroma': chroma,
            'contrast': contrast,
            'zcr': zcr
        }
        
        return features
    
    except Exception as e:
        print(f"提取音频特征时出错: {e}")
        return None

def segment_audio(audio_path, segment_duration=10, overlap=2):
    """将音频分割成片段
    
    Args:
        audio_path: 音频文件路径
        segment_duration: 每个片段的持续时间（秒）
        overlap: 片段之间的重叠时间（秒）
        
    Returns:
        segments: 音频片段列表
    """
    try:
        # 加载音频文件
        y, sr = librosa.load(audio_path)
        
        # 计算每个片段的样本数
        segment_samples = int(segment_duration * sr)
        overlap_samples = int(overlap * sr)
        hop_samples = segment_samples - overlap_samples
        
        # 分割音频
        segments = []
        for i in range(0, len(y) - segment_samples + 1, hop_samples):
            segment = y[i:i + segment_samples]
            segments.append(segment)
        
        # 处理最后一个可能不完整的片段
        if len(y) > i + segment_samples:
            last_segment = y[i + hop_samples:]
            if len(last_segment) > segment_samples / 2:  # 只保留长度超过一半的片段
                segments.append(last_segment)
        
        return segments, sr
    
    except Exception as e:
        print(f"分割音频时出错: {e}")
        return [], None

def features_to_embedding(features):
    """将音频特征转换为向量嵌入
    
    Args:
        features: 音频特征字典
        
    Returns:
        embedding: 向量嵌入
    """
    # 提取关键特征并展平
    mfcc_mean = np.mean(features['mfcc'], axis=1)
    chroma_mean = np.mean(features['chroma'], axis=1)
    contrast_mean = np.mean(features['contrast'], axis=1)
    zcr_mean = np.mean(features['zcr'])
    
    # 组合特征
    combined = np.concatenate([mfcc_mean, chroma_mean, contrast_mean, [zcr_mean]])
    
    return combined

def process_audio(audio_path, hasher, segment_duration=10, overlap=2):
    """处理音频并生成向量表示
    
    Args:
        audio_path: 音频文件路径
        hasher: 哈希器实例
        segment_duration: 每个片段的持续时间（秒）
        overlap: 片段之间的重叠时间（秒）
        
    Returns:
        segments: 音频片段列表
        embeddings: 向量嵌入列表
        pointers: 量子哈希指针列表
    """
    # 分割音频
    segments, sr = segment_audio(audio_path, segment_duration, overlap)
    if not segments:
        return [], [], []
    
    # 为每个片段生成特征向量和哈希指针
    embeddings = []
    pointers = []
    
    for i, segment in enumerate(segments):
        print(f"处理音频片段 {i+1}/{len(segments)}...")
        
        # 提取特征
        # 保存临时音频文件
        temp_path = f"/tmp/segment_{i}.wav"
        librosa.output.write_wav(temp_path, segment, sr)
        
        # 提取特征
        features = extract_audio_features(temp_path)
        
        # 删除临时文件
        os.remove(temp_path)
        
        if features is not None:
            # 转换为向量嵌入
            embedding = features_to_embedding(features)
            embeddings.append(embedding)
            
            # 生成量子哈希微小指针
            feature_str = ",".join([str(x) for x in embedding[:100]])  # 使用前100个特征
            pointer = hasher.hash_to_vector(feature_str)
            pointers.append(pointer)
    
    return segments, embeddings, pointers

def text_to_audio_search(text, model=None):
    """将文本查询转换为音频搜索向量
    
    Args:
        text: 查询文本
        model: 文本-音频联合嵌入模型（如果为None则加载默认模型）
        
    Returns:
        embedding: 查询向量
    """
    # 使用sentence-transformers作为简化实现
    if model is None:
        model = SentenceTransformer('all-MiniLM-L6-v2')
    
    embedding = model.encode(text)
    return embedding