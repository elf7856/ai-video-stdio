/**
 * API类型定义
 */

// ========== 脚本生成相关类型 ==========

export interface ScriptGenerateRequest {
  topic: string;              // 视频主题
  style?: string;             // 视频风格
  targetDuration?: number;    // 目标时长（秒）
  shotCount?: number;         // 新增：镜头数量
  additionalRequirements?: string; // 额外要求
}

export interface Shot {
  sequence: number;           // 镜头序号
  prompt: string;             // 镜头描述/提示词
  duration: number;           // 时长（秒）
  shotType?: string;          // 镜头类型
  imagePath?: string;         // 新增：分镜图路径
  videoPath?: string;         // 新增：生成视频路径
}

export interface ScriptGenerateResponse {
  success: boolean;
  script: string;             // 完整脚本
  shots: Shot[];              // 分镜列表
  totalDuration: number;      // 总时长
  metadata?: {
    style: string;
    shotCount: number;
  };
  error?: string;
}

// ========== 项目相关类型 ==========

export interface Project {
  id: string;
  title: string;
  script: string;
  targetDuration: number;
  status: string;
  createdAt: string;
  updatedAt: string;
}

export interface ProjectCreateRequest {
  title: string;
  script: string;
  targetDuration: number;
}

// ========== 视频相关类型 ==========

export interface Video {
  id: number;
  title: string;
  description?: string;
  filename: string;
  originalPath: string;
  duration?: number;
  resolution?: string;
  fileSize?: number;
  format?: string;
  createdAt: string;
}

export interface VideoUploadRequest {
  file: File;
  title?: string;
  description?: string;
}

// ========== 提示词优化相关类型 ==========

export interface PromptOptimizeRequest {
  originalPrompt: string;
  targetPlatform?: 'runway' | 'pika' | 'midjourney' | 'stable-diffusion';
  style?: string;
}

export interface PromptOptimizeResponse {
  success: boolean;
  optimizedPrompt: string;
  suggestions?: string[];
  parameters?: Record<string, any>;
  error?: string;
}

// ========== 视频生成相关类型 ==========

export interface VideoGenerationRequest {
  topic: string;
  style: string;
  targetDuration?: number;  // 可选，不传则自动计算
  shotCount?: number;       // 新增：镜头数量
  additionalRequirements?: string;
  autoGenerate?: boolean;
  // 新增：旁白/配音相关
  enableNarration?: boolean;
  narrationVoice?: string;
  narrationSpeed?: number;
  // 新增：节奏策略
  pacingStrategy?: string;
}

export interface TaskLog {
  timestamp: string;
  message: string;
  level: 'info' | 'success' | 'warning' | 'error';
}

export interface VideoGenerationTask {
  taskId: string;
  topic?: string;
  style?: string;
  targetDuration?: number; // 新增
  shotCount?: number;      // 新增
  message?: string; // 新增
  status: 'pending' | 'generating_script' | 'waiting_confirmation' | 'processing' | 'generating' | 'generating_videos' | 'merging_videos' | 'generating_narration' | 'completed' | 'failed';
  progress: number;
  script?: string;
  shots?: Shot[];
  generatedVideos?: GeneratedVideo[];
  finalVideo?: string;  // 最终合并的视频路径
  error?: string;
  createdAt: string;
  completedAt?: string;
  // 新增：旁白相关
  narrationAudioPath?: string;
  // 新增：执行日志
  logs?: TaskLog[];
}

export interface GeneratedVideo {
  sequence: number;
  shotType?: string;
  status: 'pending' | 'generating' | 'success' | 'failed';
  videoPath?: string;
  imagePath?: string; // 新增：分镜图路径
  duration?: number;
  cost?: number;
  fileSize?: number;
  generationTime?: number;
  error?: string;
}

// ========== 图像生成相关类型 ==========

export interface ImageGenerationRequest {
  prompt: string;
  provider?: 'google_imagen' | 'dalle' | 'stability' | 'replicate' | 'leonardo' | 'local';
  size?: [number, number];
  aspectRatio?: '1:1' | '3:4' | '4:3' | '9:16' | '16:9';
  resolution?: 'low' | 'medium' | 'high';
  negativePrompt?: string;
  style?: string;
}

export interface ImageGenerationResponse {
  success: boolean;
  imagePath?: string;
  provider?: string;
  error?: string;
}

export interface ImageProvider {
  name: string;
  available: boolean;
  current: boolean;
}

// ========== 项目管理相关类型 ==========

export interface ProjectDetail extends Project {
  shots?: Shot[];
  videos?: GeneratedVideo[];
  metadata?: {
    totalCost?: number;
    totalSize?: number;
    generationTime?: number;
  };
}
