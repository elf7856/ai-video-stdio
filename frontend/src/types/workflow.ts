/**
 * 工作流类型定义 - Medeo风格视频编辑工作流
 */

import type { Shot, VideoGenerationTask, GeneratedVideo } from '../api/types';
import type { TimelineData } from './timeline';

// ========== 工作流阶段 ==========

export type WorkflowStage =
  | 'ideation'           // 创意构思阶段
  | 'planning'           // AI规划阶段
  | 'editing'            // 编辑阶段
  | 'rendering'          // 渲染阶段
  | 'completed';         // 完成

// ========== 对话消息 ==========

export type MessageRole = 'user' | 'assistant' | 'system';

export type ActionType =
  | 'generate_script'    // 生成脚本
  | 'modify_shot'        // 修改镜头
  | 'add_element'        // 添加元素
  | 'change_style'       // 更改风格
  | 'adjust_timing'      // 调整时长
  | 'regenerate';        // 重新生成

export interface ConversationMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: string;
  actionType?: ActionType;
  actionPayload?: Record<string, any>;
  // AI规划展示
  planning?: PlanningInfo;
}

// ========== AI规划信息 ==========

export interface PlanningInfo {
  summary: string;
  shots: PlanningShot[];
  estimatedDuration: number;
  style: string;
}

export interface PlanningShot {
  sequence: number;
  description: string;
  duration: number;
  shotType: string;
  status: 'planned' | 'generating' | 'completed' | 'failed';
}

// ========== 创意配置 ==========

export interface CreativeConfig {
  topic: string;
  style: string;
  targetDuration: number;
  shotCount: number; // 新增
  additionalRequirements: string;
  narration: NarrationConfig;
  pacing: PacingStrategy;
}

export interface NarrationConfig {
  enabled: boolean;
  voice: string;
  speed: number;
}

export type PacingStrategy = 'balanced' | 'dynamic' | 'crescendo' | 'slow_paced';

// ========== 输出配置 ==========

export type AspectRatio = '16:9' | '9:16' | '1:1';
export type Resolution = '720p' | '1080p' | '4K';

export interface OutputConfig {
  aspectRatio: AspectRatio;
  resolution: Resolution;
  format: 'mp4' | 'webm';
  quality: 'draft' | 'standard' | 'high';
}

// ========== 资源库 ==========

export interface AssetLibrary {
  stockMedia: StockAsset[];
  uploadedMedia: UploadedAsset[];
  generatedMedia: GeneratedAsset[];
  voiceovers: VoiceoverAsset[];
  backgroundMusic: MusicAsset[];
}

export interface BaseAsset {
  id: string;
  name: string;
  type: 'video' | 'image' | 'audio';
  thumbnailUrl?: string;
  duration?: number;
}

export interface StockAsset extends BaseAsset {
  source: 'pexels' | 'pixabay' | 'unsplash';
  previewUrl: string;
  downloadUrl: string;
}

export interface UploadedAsset extends BaseAsset {
  localPath: string;
  fileSize: number;
  uploadedAt: string;
}

export interface GeneratedAsset extends BaseAsset {
  prompt: string;
  provider: 'runway' | 'pika' | 'google_veo' | 'sora';
  shotSequence?: number;
  status: 'pending' | 'generating' | 'success' | 'failed';
  localPath?: string;
  qualityScore?: number;
  generationTime?: number;
}

export interface VoiceoverAsset extends BaseAsset {
  type: 'audio';
  text: string;
  voice: string;
  speed: number;
  localPath: string;
}

export interface MusicAsset extends BaseAsset {
  type: 'audio';
  genre: string;
  mood: string;
  bpm?: number;
  localPath: string;
}

// ========== 任务状态 ==========

export interface TaskStatus {
  taskId: string;
  status: VideoGenerationTask['status'];
  progress: number;
  message?: string;
  error?: string;
  // 详细进度
  scriptReady: boolean;
  shotsReady: boolean;
  videosGenerated: number;
  totalVideos: number;
  finalVideoPath?: string;
  narrationPath?: string;
}

// ========== 主工作流状态 ==========

export interface WorkflowState {
  // 项目元信息
  projectId: string;
  projectName: string;
  createdAt: string;
  updatedAt: string;

  // 当前阶段
  stage: WorkflowStage;

  // AI对话历史
  conversation: ConversationMessage[];

  // 创意配置
  creative: CreativeConfig;

  // 脚本与分镜
  script: string;
  shots: Shot[];

  // 时间轴数据
  timeline: TimelineData;

  // 资源库
  assets: AssetLibrary;

  // 输出配置
  outputConfig: OutputConfig;

  // 任务状态
  taskStatus: TaskStatus | null;

  // 生成的视频
  generatedVideos: GeneratedVideo[];
  finalVideoPath: string | null;
}

// ========== 工作流操作 ==========

export interface WorkflowActions {
  // 阶段控制
  setStage: (stage: WorkflowStage) => void;

  // 创意配置
  setTopic: (topic: string) => void;
  setStyle: (style: string) => void;
  setCreativeConfig: (config: Partial<CreativeConfig>) => void;

  // 对话
  addMessage: (message: Omit<ConversationMessage, 'id' | 'timestamp'>) => void;
  clearConversation: () => void;

  // 脚本和分镜
  setScript: (script: string) => void;
  setShots: (shots: Shot[]) => void;
  updateShot: (index: number, shot: Partial<Shot>) => void;

  // 任务状态
  setTaskStatus: (status: TaskStatus | null) => void;
  updateProgress: (progress: number, message?: string) => void;

  // 资源
  addGeneratedAsset: (asset: GeneratedAsset) => void;

  // 输出
  setOutputConfig: (config: Partial<OutputConfig>) => void;

  // 重置
  reset: () => void;
}

// ========== 完整Store类型 ==========

export type WorkflowStore = WorkflowState & WorkflowActions;
