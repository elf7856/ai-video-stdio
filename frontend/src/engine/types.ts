/**
 * NLE Engine 类型定义
 *
 * 这个文件定义了非线性编辑引擎的核心类型
 */

export interface VideoClipData {
    id: string;
    videoPath: string;
    duration: number;
    startTime: number; // 在时间轴上的开始时间
    endTime: number;   // 在时间轴上的结束时间
    trimStart?: number; // 视频文件内的裁剪起始点
    trimEnd?: number;   // 视频文件内的裁剪结束点
}

export interface PlaybackState {
    isPlaying: boolean;
    currentTime: number;
    duration: number;
    currentClipIndex: number;
}

export interface BufferState {
    primaryVideoElement: HTMLVideoElement | null;
    secondaryVideoElement: HTMLVideoElement | null;
    activePrimary: boolean; // true = primary 活跃, false = secondary 活跃
    preloadedClipId: string | null;
}

export type PlaybackEventType =
    | 'play'
    | 'pause'
    | 'timeupdate'
    | 'clipchange'
    | 'ended'
    | 'error';

export interface PlaybackEvent {
    type: PlaybackEventType;
    data?: any;
}

export type EventCallback = (event: PlaybackEvent) => void;
