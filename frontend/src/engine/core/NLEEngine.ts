/**
 * NLEEngine - 非线性编辑引擎
 *
 * 这是整个 NLE 引擎的入口类，提供统一的 API
 * 借鉴 MLT Framework 的设计理念，但针对 Web 环境进行了优化
 *
 * 设计理念：
 * - 分层架构：Timeline (时间轴) -> Playback (播放控制) -> Buffer (缓冲管理)
 * - 事件驱动：通过事件机制与 UI 层解耦
 * - 状态管理：集中管理播放状态，避免状态不一致
 * - 资源管理：自动管理视频元素和内存
 */

import { TimelineManager } from './TimelineManager';
import { BufferManager } from './BufferManager';
import { PlaybackController } from './PlaybackController';
import type { VideoClipData, PlaybackState, EventCallback } from '../types';

export interface NLEEngineConfig {
    primaryVideoElement: HTMLVideoElement;
    secondaryVideoElement: HTMLVideoElement;
    urlHelper: (path: string) => string;
}

export class NLEEngine {
    private timelineManager: TimelineManager;
    private bufferManager: BufferManager;
    private playbackController: PlaybackController;
    private initialized: boolean = false;

    constructor(config: NLEEngineConfig) {
        // 创建管理器
        this.bufferManager = new BufferManager(config.urlHelper);
        this.timelineManager = new TimelineManager();
        this.playbackController = new PlaybackController(this.timelineManager, this.bufferManager);

        // 初始化缓冲管理器
        this.bufferManager.initialize(config.primaryVideoElement, config.secondaryVideoElement);
    }

    /**
     * 加载时间轴数据
     */
    async loadTimeline(clips: VideoClipData[]): Promise<void> {
        if (clips.length === 0) {
            throw new Error('Cannot load empty timeline');
        }

        // 设置时间轴
        this.timelineManager.setClips(clips);

        // 初始化播放控制器
        await this.playbackController.initialize();

        this.initialized = true;
        console.log('[NLEEngine] Timeline loaded with', clips.length, 'clips');
    }

    /**
     * 播放
     */
    async play(): Promise<void> {
        this.ensureInitialized();
        await this.playbackController.play();
    }

    /**
     * 暂停
     */
    pause(): void {
        this.ensureInitialized();
        this.playbackController.pause();
    }

    /**
     * 切换播放/暂停
     */
    async togglePlayPause(): Promise<void> {
        this.ensureInitialized();
        const state = this.playbackController.getState();
        if (state.isPlaying) {
            this.pause();
        } else {
            await this.play();
        }
    }

    /**
     * 跳转到指定时间
     */
    async seek(time: number): Promise<void> {
        this.ensureInitialized();
        await this.playbackController.seek(time);
    }

    /**
     * 设置音量 (0-1)
     */
    setVolume(volume: number): void {
        this.ensureInitialized();
        this.playbackController.setVolume(volume);
    }

    /**
     * 设置静音
     */
    setMuted(muted: boolean): void {
        this.ensureInitialized();
        this.playbackController.setMuted(muted);
    }

    /**
     * 获取当前播放状态
     */
    getState(): PlaybackState {
        this.ensureInitialized();
        return this.playbackController.getState();
    }

    /**
     * 获取时间轴总时长
     */
    getDuration(): number {
        this.ensureInitialized();
        return this.timelineManager.getTotalDuration();
    }

    /**
     * 获取片段数量
     */
    getClipCount(): number {
        this.ensureInitialized();
        return this.timelineManager.getClipCount();
    }

    /**
     * 获取所有片段
     */
    getClips(): VideoClipData[] {
        this.ensureInitialized();
        return this.timelineManager.getClips();
    }

    /**
     * 获取缓冲状态（用于 UI 调试）
     */
    getBufferState() {
        return this.bufferManager.getState();
    }

    /**
     * 注册事件监听器
     *
     * 支持的事件：
     * - play: 开始播放
     * - pause: 暂停
     * - timeupdate: 时间更新
     * - clipchange: 片段切换
     * - ended: 播放结束
     * - error: 错误
     */
    on(eventType: string, callback: EventCallback): void {
        this.playbackController.on(eventType, callback);
    }

    /**
     * 移除事件监听器
     */
    off(eventType: string, callback: EventCallback): void {
        this.playbackController.off(eventType, callback);
    }

    /**
     * 清理资源
     */
    dispose(): void {
        this.playbackController.dispose();
        this.initialized = false;
        console.log('[NLEEngine] Disposed');
    }

    /**
     * 确保引擎已初始化
     */
    private ensureInitialized(): void {
        if (!this.initialized) {
            throw new Error('NLE Engine not initialized. Call loadTimeline() first.');
        }
    }
}

// 导出工厂函数
export function createNLEEngine(config: NLEEngineConfig): NLEEngine {
    return new NLEEngine(config);
}
