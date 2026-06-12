/**
 * PlaybackController - 播放控制器
 *
 * 职责：
 * - 控制播放、暂停、跳转
 * - 管理播放状态和进度
 * - 协调 TimelineManager 和 BufferManager
 * - 处理片段自动切换
 */

import { TimelineManager } from './TimelineManager';
import { BufferManager } from './BufferManager';
import type { PlaybackState, PlaybackEvent, EventCallback } from '../types';

export class PlaybackController {
    private timelineManager: TimelineManager;
    private bufferManager: BufferManager;
    private eventListeners: Map<string, Set<EventCallback>> = new Map();

    // 播放状态
    private isPlaying: boolean = false;
    private currentTime: number = 0;
    private currentClipIndex: number = -1;

    // 进度更新循环
    private animationFrameId: number | null = null;
    private lastUpdateTime: number = 0;
    private readonly UPDATE_INTERVAL = 33; // 约 30fps

    // 切换控制
    private isSwitching: boolean = false;

    constructor(timelineManager: TimelineManager, bufferManager: BufferManager) {
        this.timelineManager = timelineManager;
        this.bufferManager = bufferManager;
    }

    /**
     * 初始化播放器
     */
    async initialize(): Promise<void> {
        const clips = this.timelineManager.getClips();
        if (clips.length === 0) {
            throw new Error('No clips to play');
        }

        // 加载第一个片段
        await this.loadClip(0, 0, false);

        // 预加载第二个片段
        if (clips.length > 1) {
            await this.bufferManager.preloadClip(clips[1]);
        }
    }

    /**
     * 播放
     */
    async play(): Promise<void> {
        if (this.isPlaying) return;

        const activeVideo = this.bufferManager.getActiveVideo();
        if (!activeVideo) {
            throw new Error('No active video element');
        }

        try {
            await activeVideo.play();
            this.isPlaying = true;
            this.startProgressLoop();
            this.emit({ type: 'play' });
        } catch (error) {
            console.error('[PlaybackController] Play failed:', error);
            this.emit({ type: 'error', data: error });
            throw error;
        }
    }

    /**
     * 暂停
     */
    pause(): void {
        if (!this.isPlaying) return;

        const activeVideo = this.bufferManager.getActiveVideo();
        if (activeVideo) {
            activeVideo.pause();
        }

        this.isPlaying = false;
        this.stopProgressLoop();
        this.emit({ type: 'pause' });
    }

    /**
     * 跳转到指定时间
     */
    async seek(globalTime: number): Promise<void> {
        const wasPlaying = this.isPlaying;
        if (wasPlaying) {
            this.pause();
        }

        this.currentTime = globalTime;

        // 查找目标时间点的片段
        const result = this.timelineManager.getClipAtTime(globalTime);
        if (!result) {
            console.error('[PlaybackController] No clip found at time:', globalTime);
            return;
        }

        const { index, localTime } = result;

        // 如果跳转到不同的片段，需要重新加载
        if (index !== this.currentClipIndex) {
            await this.loadClip(index, localTime, wasPlaying);

            // 预加载下一个片段
            const nextClip = this.timelineManager.getClipByIndex(index + 1);
            if (nextClip) {
                this.bufferManager.preloadClip(nextClip).catch(err =>
                    console.error('[PlaybackController] Preload failed:', err)
                );
            }
        } else {
            // 同一片段内跳转
            const activeVideo = this.bufferManager.getActiveVideo();
            if (activeVideo) {
                activeVideo.currentTime = localTime;
            }

            if (wasPlaying) {
                await this.play();
            }
        }

        this.emit({ type: 'timeupdate', data: { time: globalTime } });
    }

    /**
     * 设置音量 (0-1)
     */
    setVolume(volume: number): void {
        this.bufferManager.setVolume(Math.max(0, Math.min(1, volume)));
    }

    /**
     * 设置静音
     */
    setMuted(muted: boolean): void {
        this.bufferManager.setMuted(muted);
    }

    /**
     * 获取当前播放状态
     */
    getState(): PlaybackState {
        return {
            isPlaying: this.isPlaying,
            currentTime: this.currentTime,
            duration: this.timelineManager.getTotalDuration(),
            currentClipIndex: this.currentClipIndex
        };
    }

    /**
     * 加载指定片段
     */
    private async loadClip(clipIndex: number, localTime: number, autoPlay: boolean): Promise<void> {
        const clip = this.timelineManager.getClipByIndex(clipIndex);
        if (!clip) {
            throw new Error(`Clip ${clipIndex} not found`);
        }

        await this.bufferManager.loadAndPlay(clip, localTime, autoPlay);
        this.currentClipIndex = clipIndex;
        this.emit({ type: 'clipchange', data: { clipIndex, clip } });
    }

    /**
     * 开始进度更新循环
     */
    private startProgressLoop(): void {
        if (this.animationFrameId !== null) {
            return;
        }

        const updateProgress = (timestamp: number) => {
            if (!this.isPlaying) {
                return;
            }

            // 节流：约 30fps
            if (timestamp - this.lastUpdateTime < this.UPDATE_INTERVAL) {
                this.animationFrameId = requestAnimationFrame(updateProgress);
                return;
            }
            this.lastUpdateTime = timestamp;

            const activeVideo = this.bufferManager.getActiveVideo();
            if (!activeVideo) {
                this.animationFrameId = requestAnimationFrame(updateProgress);
                return;
            }

            const currentClip = this.timelineManager.getClipByIndex(this.currentClipIndex);
            if (!currentClip) {
                this.animationFrameId = requestAnimationFrame(updateProgress);
                return;
            }

            // 更新当前时间
            const localTime = activeVideo.currentTime;
            const globalTime = this.timelineManager.clipTimeToGlobalTime(this.currentClipIndex, localTime);
            if (globalTime !== null) {
                this.currentTime = globalTime;
                this.emit({ type: 'timeupdate', data: { time: globalTime } });
            }

            // 检查是否需要切换片段
            const clipDuration = currentClip.endTime - currentClip.startTime;
            const effectiveLocalTime = localTime - (currentClip.trimStart || 0);

            // 提前 50ms 切换，减少卡顿
            if (effectiveLocalTime >= clipDuration - 0.05) {
                this.handleClipEnd();
            }

            this.animationFrameId = requestAnimationFrame(updateProgress);
        };

        this.animationFrameId = requestAnimationFrame(updateProgress);
    }

    /**
     * 停止进度更新循环
     */
    private stopProgressLoop(): void {
        if (this.animationFrameId !== null) {
            cancelAnimationFrame(this.animationFrameId);
            this.animationFrameId = null;
        }
    }

    /**
     * 处理片段播放结束
     */
    private async handleClipEnd(): Promise<void> {
        if (this.isSwitching) {
            return;
        }

        const nextIndex = this.currentClipIndex + 1;
        const clips = this.timelineManager.getClips();

        // 检查是否到达末尾
        if (nextIndex >= clips.length) {
            this.pause();
            this.emit({ type: 'ended' });
            return;
        }

        this.isSwitching = true;

        const nextClip = clips[nextIndex];

        // 尝试无缝切换
        const switched = await this.bufferManager.switchToPreloadedClip(nextClip, nextClip.trimStart || 0);

        if (switched) {
            // 切换成功
            this.currentClipIndex = nextIndex;
            this.emit({ type: 'clipchange', data: { clipIndex: nextIndex, clip: nextClip } });

            // 预加载下下个片段
            if (nextIndex + 1 < clips.length) {
                this.bufferManager.preloadClip(clips[nextIndex + 1]).catch(err =>
                    console.error('[PlaybackController] Preload failed:', err)
                );
            }
        } else {
            // 切换失败，回退到传统加载
            console.warn('[PlaybackController] Seamless switch failed, falling back to load');
            await this.loadClip(nextIndex, nextClip.trimStart || 0, true);

            // 预加载下下个片段
            if (nextIndex + 1 < clips.length) {
                this.bufferManager.preloadClip(clips[nextIndex + 1]).catch(err =>
                    console.error('[PlaybackController] Preload failed:', err)
                );
            }
        }

        this.isSwitching = false;
    }

    /**
     * 注册事件监听器
     */
    on(eventType: string, callback: EventCallback): void {
        if (!this.eventListeners.has(eventType)) {
            this.eventListeners.set(eventType, new Set());
        }
        this.eventListeners.get(eventType)!.add(callback);
    }

    /**
     * 移除事件监听器
     */
    off(eventType: string, callback: EventCallback): void {
        const listeners = this.eventListeners.get(eventType);
        if (listeners) {
            listeners.delete(callback);
        }
    }

    /**
     * 触发事件
     */
    private emit(event: PlaybackEvent): void {
        const listeners = this.eventListeners.get(event.type);
        if (listeners) {
            listeners.forEach(callback => callback(event));
        }
    }

    /**
     * 清理资源
     */
    dispose(): void {
        this.stopProgressLoop();
        this.bufferManager.dispose();
        this.eventListeners.clear();
    }
}
