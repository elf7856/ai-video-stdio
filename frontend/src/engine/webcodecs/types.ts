/**
 * WebCodecs 引擎类型定义
 */

export interface VideoSegment {
    id: string;
    url: string;
    startTime: number; // 在时间轴上的开始时间（秒）
    duration: number;  // 在时间轴上的持续时间（秒）
    trimStart?: number; // 裁剪起始时间（秒）
    trimEnd?: number;   // 裁剪结束时间（秒）
}

export interface DecodedFrame {
    frame: VideoFrame;
    timestamp: number; // 微秒
    duration: number;  // 微秒
}

export interface VideoMetadata {
    duration: number;
    width: number;
    height: number;
    fps: number;
    codec: string;
}

export interface PlaybackState {
    isPlaying: boolean;
    currentTime: number;
    duration: number;
    currentSegmentIndex: number;
}

export type EngineEventType =
    | 'ready'
    | 'play'
    | 'pause'
    | 'timeupdate'
    | 'segmentchange'
    | 'ended'
    | 'error'
    | 'buffering';

export interface EngineEvent {
    type: EngineEventType;
    data?: any;
}

export type EventCallback = (event: EngineEvent) => void;
