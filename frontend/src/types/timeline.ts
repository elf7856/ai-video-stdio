/**
 * 时间轴类型定义 - 支持多轨道编辑
 */

// ========== 轨道类型 ==========

export type TrackType = 'script' | 'video' | 'audio';

// ========== 元素类型 ==========

export type ElementType = 'media' | 'text' | 'script_segment';

// ========== 时间轴数据 ==========

export interface TimelineData {
  id: string;
  name: string;

  // 画布设置
  canvas: CanvasConfig;

  // 轨道列表
  tracks: Track[];

  // 播放状态
  currentTime: number;
  duration: number;

  // 缩放级别 (pixels per second)
  zoomLevel: number;

  // 选中的元素
  selectedElementIds: string[];
}

export interface CanvasConfig {
  width: number;
  height: number;
  fps?: number; // fps optional
  backgroundColor: string;
  fit?: 'contain' | 'cover' | 'fill'; // Add fit property
}

// ========== 轨道 ==========

export interface Track {
  id: string;
  name: string;
  type: TrackType;
  elements: TimelineElement[];

  // 轨道状态
  muted: boolean;
  locked: boolean;
  visible: boolean;

  // 轨道高度 (px)
  height: number;

  // 轨道颜色标识
  color?: string;
}

// ========== 时间轴元素 ==========

export interface TimelineElement {
  id: string;
  trackId: string;
  type: ElementType;

  // 时间信息 (秒)
  startTime: number;
  duration: number;

  // 裁剪信息 (秒)
  trimStart: number;
  trimEnd: number;

  // 内容
  content: MediaContent | TextContent | ScriptContent;

  // 效果
  transition?: TransitionEffect;
  filters?: FilterEffect[];

  // 元数据
  name?: string;
  thumbnail?: string;
}

// ========== 媒体内容 ==========

export interface MediaContent {
  type: 'video' | 'image' | 'audio';
  path: string;
  originalDuration?: number;

  // 视频/图片特有
  width?: number;
  height?: number;

  // 音频设置
  volume?: number;
  muted?: boolean;

  // 播放速度
  speed?: number;
}

// ========== 文本内容 ==========

export interface TextContent {
  text: string;
  fontFamily: string;
  fontSize: number;
  fontWeight: number;
  color: string;
  backgroundColor?: string;

  // 位置 (相对画布的百分比)
  x: number;
  y: number;

  // 对齐
  textAlign: 'left' | 'center' | 'right';

  // 动画
  animation?: TextAnimation;
}

export interface TextAnimation {
  type: 'fade' | 'slide' | 'typewriter' | 'bounce';
  duration: number;
  delay: number;
}

// ========== 脚本内容 (音频脚本轨道专用) ==========

export interface ScriptContent {
  text: string;
  audioPath?: string;

  // 关联的媒体元素ID
  linkedMediaIds: string[];

  // 配音配置
  voiceConfig: VoiceConfig;

  // 字幕样式
  subtitleStyle?: SubtitleStyle;
}

export interface VoiceConfig {
  voice: string;
  speed: number;
  pitch?: number;
}

export interface SubtitleStyle {
  enabled: boolean;
  fontFamily: string;
  fontSize: number;
  color: string;
  backgroundColor: string;
  position: 'top' | 'center' | 'bottom';
}

// ========== 转场效果 ==========

export type TransitionType =
  | 'none'
  | 'fade'
  | 'dissolve'
  | 'wipe'
  | 'slide'
  | 'zoom';

export interface TransitionEffect {
  type: TransitionType;
  duration: number;  // 秒
  easing?: 'linear' | 'ease-in' | 'ease-out' | 'ease-in-out';
}

// ========== 滤镜效果 ==========

export type FilterType =
  | 'brightness'
  | 'contrast'
  | 'saturation'
  | 'blur'
  | 'grayscale'
  | 'sepia'
  | 'hue-rotate';

export interface FilterEffect {
  type: FilterType;
  value: number;
}

// ========== 时间轴操作 ==========

export interface TimelineActions {
  // 轨道操作
  addTrack: (track: Omit<Track, 'id'>) => string;
  removeTrack: (trackId: string) => void;
  updateTrack: (trackId: string, updates: Partial<Track>) => void;
  reorderTracks: (fromIndex: number, toIndex: number) => void;

  // 元素操作
  addElement: (trackId: string, element: Omit<TimelineElement, 'id' | 'trackId'>) => string;
  removeElement: (elementId: string) => void;
  updateElement: (elementId: string, updates: Partial<TimelineElement>) => void;
  moveElement: (elementId: string, newStartTime: number) => void;
  resizeElement: (elementId: string, newDuration: number, anchor: 'start' | 'end') => void;

  // 选择操作
  selectElement: (elementId: string, addToSelection?: boolean) => void;
  deselectElement: (elementId: string) => void;
  clearSelection: () => void;

  // 播放控制
  setCurrentTime: (time: number) => void;
  setZoomLevel: (level: number) => void;

  // 工具方法
  getElementAtTime: (trackId: string, time: number) => TimelineElement | null;
  getDuration: () => number;
}

// ========== 完整Store类型 ==========

export type TimelineStore = TimelineData & TimelineActions;

// ========== 默认值 ==========

export const DEFAULT_CANVAS_CONFIG: CanvasConfig = {
  width: 1920,
  height: 1080,
  fps: 30,
  backgroundColor: '#000000'
};

export const DEFAULT_TRACK_HEIGHT = 60;

export const DEFAULT_TRANSITION: TransitionEffect = {
  type: 'fade',
  duration: 0.5,
  easing: 'ease-in-out'
};
