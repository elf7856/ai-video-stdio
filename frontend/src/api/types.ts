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
  sequence: number;           // 镜头序号（必须从1开始连续）
  prompt: string;             // 镜头描述/提示词（10-1000字符）
  duration: number;           // 时长（秒，0-8.0秒）
  shotType?: string;          // 镜头类型
  imagePath?: string;         // 分镜图路径
  videoPath?: string;         // 生成视频路径
  status?: string;            // 状态
  qualityScore?: number;      // 质量分数（0-1）
  error?: string | null;      // 生成失败原因
}

// ========== ProductionBible（DirectorAgent 的全局蓝图） ==========

export type ContinuityLink = 'cut' | 'match_cut' | 'continuous';

export interface VisualStyle {
  color_palette: string;
  lighting_style: string;
  visual_quality: string;
  camera_style: string;
  overall_mood: string;
}

export interface CharacterProfile {
  character_id: string;
  name: string;
  description: string;
  visual_keywords: string[];
  reference_image_path?: string | null;
  consistency_required: boolean;
  role: string;
}

export interface SceneInfo {
  scene_id: number;
  location: string;
  time_of_day: string;
  mood: string;
  narrative_purpose: string;
  characters_present: string[];
  environment_description: string;
  reference_image_path?: string | null;
}

export interface BibleShotPlan {
  sequence: number;
  scene_id: number;
  prompt: string;
  duration: number;
  shot_type: string;
  characters_in_shot: string[];
  continuity: ContinuityLink;
  inherits_frame_from?: number | null;
  camera_movement?: string | null;
  action?: string | null;
}

export interface ProductionBible {
  logline: string;
  tone: string;
  visual_style: VisualStyle;
  characters: CharacterProfile[];
  scenes: SceneInfo[];
  shot_graph: BibleShotPlan[];
  estimated_duration: number;
  narrative_arc: string;
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

// 视频风格枚举
export type VideoStyle =
  | '专业'
  | '电影感'
  | '纪录片'
  | '商业广告'
  | '社交媒体'
  | '教育'
  | '娱乐';

// 旁白声音枚举
export type NarrationVoice =
  | 'chinese_female'
  | 'chinese_male'
  | 'english_female'
  | 'english_male';

export interface VideoGenerationRequest {
  topic: string;                    // 视频主题，2-200字符
  style: string;                    // 视频风格
  targetDuration?: number;          // 目标时长（秒），15-180秒之间
  shotCount?: number;               // 镜头数量，3-12个之间
  additionalRequirements?: string;  // 额外要求
  enableNarration?: boolean;        // 是否启用旁白
  narrationVoice?: NarrationVoice;  // 旁白声音
  narrationSpeed?: number;
  pacingStrategy?: string;
  generationMode?: 'manual' | 'autopilot';
  sourceMaterial?: SourceMaterial;
}

export type SourceMaterialType = 'webpage' | 'video' | 'image' | 'unknown';

export interface SourceImage {
  url: string;
  alt?: string;
}

export interface SourceKeyframe {
  index: number;
  timestamp: number;
  framePath?: string;
  publicPath?: string;
}

export interface SourceRecommendedSegment {
  sequence: number;
  start: number;
  end: number;
  duration: number;
  representativeTimestamp: number;
  type: 'hook' | 'context' | 'demo' | 'turning_point' | 'evidence' | 'payoff' | 'reference' | 'skip' | string;
  title: string;
  description?: string;
  reason?: string;
  suggestedUse: 'keep' | 'rewrite' | 'remix' | 'reference' | 'skip' | string;
  priority: number;
  seedanceReady?: boolean;
  source?: string;
}

export interface SourceVideoAnalysis {
  videoUnderstanding?: {
    success?: boolean;
    model?: string;
    mediaResolution?: string;
    usedProxy?: boolean;
    analysis?: Record<string, any>;
    usage?: Record<string, any>;
    error?: string | null;
  };
  recommendedSegments?: {
    success?: boolean;
    strategy?: string;
    segmentDurationRange?: { min?: number; max?: number };
    segments?: SourceRecommendedSegment[];
    error?: string | null;
  };
  summary?: Record<string, any>;
  styleStructure?: Record<string, any>;
  transcript?: {
    text?: string;
    excerpt?: string;
    confidence?: number;
    language?: string;
    provider?: string;
    success?: boolean;
    error?: string | null;
  };
  keyframes?: SourceKeyframe[];
  keyframeDescriptions?: Array<{ index?: number; timestamp?: number; description?: string }>;
}

export interface SourceMaterial {
  sourceId: string;
  type: SourceMaterialType;
  url: string;
  domain?: string;
  title?: string;
  summary?: string;
  images?: SourceImage[];
  rawContent?: string;
  metadata?: Record<string, any>;
  status?: 'ready' | 'failed' | 'partial' | 'analyzed';
  error?: string | null;
  videoPath?: string;
  publicPath?: string;
  duration?: number;
  platform?: string;
  videoInfo?: Record<string, any>;
  videoAnalysis?: SourceVideoAnalysis;
}

export interface IntentGenerationRequest {
  userInput: string;
  style?: string;
  targetDuration?: number;
  shotCount?: number;
  additionalRequirements?: string;
  enableNarration?: boolean;
  narrationVoice?: NarrationVoice;
  narrationSpeed?: number;
  pacingStrategy?: string;
  generationMode?: 'manual' | 'autopilot';
}

export interface IntentGenerationResponse {
  success: boolean;
  action: 'created' | 'needs_clarification';
  taskId?: string;
  status?: string;
  progress?: number;
  message?: string;
  sourceMaterial?: SourceMaterial | null;
  suggestions?: string[];
}

export interface TaskLog {
  timestamp: string;
  message: string;
  level: 'info' | 'success' | 'warning' | 'error';
}

export interface StrategyDecision {
  strategy: string;
  reason: string;
  steps: string[];
  estimated_cost: number;
  estimated_time: number;
  requires_asset_search: boolean;
  requires_character_ref: boolean;
  requires_first_frames: boolean;
  confidence: number;
}

export interface VideoGenerationTask {
  taskId: string;
  topic?: string;
  style?: string;
  targetDuration?: number; // 新增
  shotCount?: number;      // 新增
  message?: string; // 新增
  status: 'pending' | 'generating_script' | 'waiting_confirmation' | 'processing' | 'generating' | 'generating_videos' | 'merging_videos' | 'generating_narration' | 'completed' | 'partial_success' | 'failed';
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
  // 新增：DirectorAgent 产出的全局蓝图（角色参考图、场景参考图、转场标注）
  bible?: ProductionBible | null;
  // 新增：GenerationStrategyAgent 的观察型策略建议，不改变当前生成流程
  strategyDecision?: StrategyDecision | null;
  // 新增：自然语言输入中识别并拉取的来源材料
  sourceMaterial?: SourceMaterial | null;
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
