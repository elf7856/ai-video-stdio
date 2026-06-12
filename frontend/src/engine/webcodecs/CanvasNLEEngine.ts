/**
 * CanvasNLEEngine - Canvas 基础的非线性编辑引擎
 *
 * 核心思路：
 * - 使用两个隐藏的 video 元素进行解码和预加载
 * - 使用 requestVideoFrameCallback 提取当前播放的帧
 * - 将帧实时绘制到 Canvas 上
 * - 切换片段时，切换到另一个已预加载的 video 元素
 *
 * 优势：
 * - 真正的无缝切换（在 Canvas 上渲染，用户看不到切换过程）
 * - 利用浏览器原生解码能力
 * - 可以添加转场效果
 * - 兼容性好
 */

import { CanvasRenderer } from './CanvasRenderer';
import { VideoFrameExtractor } from './VideoFrameExtractor';
import type { VideoSegment, PlaybackState, EngineEvent, EventCallback } from './types';

export interface CanvasNLEEngineConfig {
    canvas: HTMLCanvasElement;
    urlHelper: (path: string) => string;
}

export class CanvasNLEEngine {
    // 渲染相关
    private renderer: CanvasRenderer;
    private urlHelper: (path: string) => string;

    // 双缓冲 video 元素
    private primaryVideo: HTMLVideoElement;
    private secondaryVideo: HTMLVideoElement;
    private activePrimary: boolean = true;

    // 帧提取器
    private frameExtractor: VideoFrameExtractor | null = null;

    // 时间轴数据
    private segments: VideoSegment[] = [];
    private currentSegmentIndex: number = 0;
    private totalDuration: number = 0;

    // 播放状态
    private isPlaying: boolean = false;
    private currentTime: number = 0;

    // 音频控制
    private volume: number = 1;

    // 事件监听
    private eventListeners: Map<string, Set<EventCallback>> = new Map();

    // 进度更新
    private progressInterval: number | null = null;

    constructor(config: CanvasNLEEngineConfig) {
        this.renderer = new CanvasRenderer(config.canvas);
        this.urlHelper = config.urlHelper;

        // 创建隐藏的 video 元素
        this.primaryVideo = this.createHiddenVideo();
        this.secondaryVideo = this.createHiddenVideo();

        console.log('[CanvasNLEEngine] Initialized');
    }

    /**
     * 创建隐藏的 video 元素
     */
    private createHiddenVideo(): HTMLVideoElement {
        const video = document.createElement('video');
        video.crossOrigin = 'anonymous';
        video.preload = 'auto';
        video.muted = false; // 不静音，用于播放音频
        video.style.display = 'none';

        // 添加到 DOM（requestVideoFrameCallback 需要）
        document.body.appendChild(video);

        return video;
    }

    /**
     * 加载时间轴
     */
    async loadTimeline(segments: VideoSegment[]): Promise<void> {
        if (segments.length === 0) {
            throw new Error('Cannot load empty timeline');
        }

        this.segments = segments;
        this.currentSegmentIndex = 0;

        // 计算总时长
        this.totalDuration = segments.reduce((sum, seg) => sum + seg.duration, 0);

        // 加载第一个片段
        await this.loadSegment(0, false);

        // 预加载第二个片段
        if (segments.length > 1) {
            this.preloadSegment(1);
        }

        // 设置 Canvas 尺寸
        if (this.primaryVideo.videoWidth > 0) {
            this.renderer.setSize(
                this.primaryVideo.videoWidth,
                this.primaryVideo.videoHeight
            );
        }

        this.emit({ type: 'ready' });
        console.log('[CanvasNLEEngine] Timeline loaded with', segments.length, 'segments');
    }

    /**
     * 加载指定片段
     */
    private async loadSegment(index: number, autoPlay: boolean): Promise<void> {
        const segment = this.segments[index];
        if (!segment) {
            throw new Error(`Segment ${index} not found`);
        }

        const video = this.getActiveVideo();
        const url = this.urlHelper(segment.url);

        return new Promise((resolve, reject) => {
            const handleLoadedData = () => {
                video.currentTime = segment.trimStart || 0;

                if (autoPlay) {
                    video.play()
                        .then(() => {
                            this.startFrameExtraction();
                            resolve();
                        })
                        .catch(reject);
                } else {
                    this.startFrameExtraction();
                    resolve();
                }

                cleanup();
            };

            const handleError = () => {
                cleanup();
                reject(new Error(`Failed to load segment ${index}`));
            };

            const cleanup = () => {
                video.removeEventListener('loadeddata', handleLoadedData);
                video.removeEventListener('error', handleError);
            };

            video.addEventListener('loadeddata', handleLoadedData, { once: true });
            video.addEventListener('error', handleError, { once: true });

            video.src = url;
            video.load();
        });
    }

    /**
     * 预加载指定片段到非活跃的 video
     */
    private preloadSegment(index: number): void {
        const segment = this.segments[index];
        if (!segment) return;

        const video = this.getInactiveVideo();
        const url = this.urlHelper(segment.url);

        video.addEventListener('loadeddata', () => {
            console.log('[CanvasNLEEngine] Preloaded segment', index);
        }, { once: true });

        video.src = url;
        video.currentTime = segment.trimStart || 0;
        video.load();
    }

    /**
     * 开始帧提取
     */
    private startFrameExtraction(): void {
        // 停止旧的提取器
        if (this.frameExtractor) {
            this.frameExtractor.stop();
        }

        // 创建新的提取器
        const video = this.getActiveVideo();
        this.frameExtractor = new VideoFrameExtractor(video, this.renderer);
        this.frameExtractor.start();
    }

    /**
     * 播放
     */
    async play(): Promise<void> {
        if (this.isPlaying) return;

        const video = this.getActiveVideo();

        try {
            await video.play();
            this.isPlaying = true;
            this.startProgressTracking();
            this.emit({ type: 'play' });
        } catch (error) {
            console.error('[CanvasNLEEngine] Play failed:', error);
            throw error;
        }
    }

    /**
     * 暂停
     */
    pause(): void {
        if (!this.isPlaying) return;

        const video = this.getActiveVideo();
        video.pause();

        this.isPlaying = false;
        this.stopProgressTracking();
        this.emit({ type: 'pause' });
    }

    /**
     * 切换播放/暂停
     */
    async togglePlayPause(): Promise<void> {
        if (this.isPlaying) {
            this.pause();
        } else {
            await this.play();
        }
    }

    /**
     * 跳转到指定时间
     */
    async seek(time: number): Promise<void> {
        console.log('[CanvasNLEEngine] Seeking to time:', time);

        const wasPlaying = this.isPlaying;
        if (wasPlaying) {
            this.pause();
        }

        // 立即更新当前时间并触发事件，给用户即时反馈
        this.currentTime = time;
        this.emit({ type: 'timeupdate', data: { time } });

        // 查找目标片段
        let accTime = 0;
        for (let i = 0; i < this.segments.length; i++) {
            const segment = this.segments[i];
            if (time >= accTime && time < accTime + segment.duration) {
                const localTime = time - accTime + (segment.trimStart || 0);

                console.log('[CanvasNLEEngine] Found segment', i, 'localTime:', localTime);

                if (i !== this.currentSegmentIndex) {
                    // 切换到不同片段
                    console.log('[CanvasNLEEngine] Switching to segment', i);
                    await this.loadSegment(i, false);
                    this.currentSegmentIndex = i;

                    // 设置正确的时间
                    const video = this.getActiveVideo();
                    video.currentTime = localTime;

                    // 等待视频准备好并渲染
                    await this.waitForVideoReady(video);
                    this.renderCurrentFrame();

                    // 预加载下一个片段
                    if (i + 1 < this.segments.length) {
                        this.preloadSegment(i + 1);
                    }

                    // 如果之前在播放，恢复播放
                    if (wasPlaying) {
                        await this.play();
                    }
                } else {
                    // 同一片段内跳转
                    console.log('[CanvasNLEEngine] Seeking within same segment');
                    const video = this.getActiveVideo();

                    const targetTime = localTime;
                    console.log('[CanvasNLEEngine] Target time:', targetTime);

                    video.currentTime = targetTime;

                    // 等待 seeked 事件
                    await this.waitForVideoSeeked(video);

                    const actualTime = video.currentTime;
                    const diff = Math.abs(actualTime - targetTime);
                    console.log('[CanvasNLEEngine] Actual time after seek:', actualTime, 'diff:', diff.toFixed(3));

                    // 如果误差较大，尝试微调（通过短暂播放）
                    if (diff > 0.1 && actualTime < targetTime) {
                        console.log('[CanvasNLEEngine] Fine-tuning seek position...');
                        await this.fineTuneSeek(video, targetTime);
                    }

                    // 渲染当前帧
                    if (!wasPlaying) {
                        this.renderCurrentFrame();
                    }

                    if (wasPlaying) {
                        await this.play();
                    }
                }

                return;
            }
            accTime += segment.duration;
        }
    }

    /**
     * 微调 seek 位置（通过短暂播放到达精确位置）
     */
    private async fineTuneSeek(video: HTMLVideoElement, targetTime: number): Promise<void> {
        return new Promise((resolve) => {
            let checkCount = 0;
            const maxChecks = 30; // 最多检查 30 次（约 1 秒）

            const checkTime = () => {
                checkCount++;
                const currentTime = video.currentTime;

                if (currentTime >= targetTime - 0.033 || checkCount >= maxChecks) {
                    // 到达目标或超时
                    video.pause();
                    console.log('[CanvasNLEEngine] Fine-tune complete. Final time:', currentTime);
                    resolve();
                } else {
                    // 继续等待
                    requestAnimationFrame(checkTime);
                }
            };

            // 开始播放
            video.play().then(() => {
                requestAnimationFrame(checkTime);
            }).catch(() => {
                resolve();
            });
        });
    }

    /**
     * 等待视频准备好
     */
    private waitForVideoReady(video: HTMLVideoElement): Promise<void> {
        if (video.readyState >= 2) {
            return Promise.resolve();
        }

        return new Promise((resolve) => {
            const handler = () => {
                resolve();
            };
            video.addEventListener('loadeddata', handler, { once: true });

            // 超时保护
            setTimeout(() => {
                video.removeEventListener('loadeddata', handler);
                resolve();
            }, 1000);
        });
    }

    /**
     * 等待视频 seek 完成（精确到帧）
     */
    private waitForVideoSeeked(video: HTMLVideoElement): Promise<void> {
        return new Promise((resolve) => {
            let resolved = false;

            const handler = () => {
                if (resolved) return;
                resolved = true;

                // seek 完成后，等待下一帧渲染
                requestAnimationFrame(() => {
                    resolve();
                });
            };

            video.addEventListener('seeked', handler, { once: true });

            // 超时保护
            setTimeout(() => {
                if (!resolved) {
                    resolved = true;
                    video.removeEventListener('seeked', handler);
                    resolve();
                }
            }, 1000);
        });
    }

    /**
     * 渲染当前帧（用于暂停时的 seek）
     */
    private renderCurrentFrame(): void {
        const video = this.getActiveVideo();
        if (video.readyState >= 2) {
            this.renderer.renderFrame(video);
            console.log('[CanvasNLEEngine] Rendered current frame at', video.currentTime);
        } else {
            console.warn('[CanvasNLEEngine] Video not ready for rendering, readyState:', video.readyState);
        }
    }

    /**
     * 开始进度跟踪
     */
    private startProgressTracking(): void {
        if (this.progressInterval !== null) return;

        this.progressInterval = window.setInterval(() => {
            this.updateProgress();
        }, 33); // 约 30fps
    }

    /**
     * 停止进度跟踪
     */
    private stopProgressTracking(): void {
        if (this.progressInterval !== null) {
            clearInterval(this.progressInterval);
            this.progressInterval = null;
        }
    }

    /**
     * 更新进度
     */
    private updateProgress(): void {
        const video = this.getActiveVideo();
        const segment = this.segments[this.currentSegmentIndex];
        if (!segment) return;

        const localTime = video.currentTime;
        const trimStart = segment.trimStart || 0;
        const effectiveLocalTime = localTime - trimStart;

        // 计算全局时间
        let accTime = 0;
        for (let i = 0; i < this.currentSegmentIndex; i++) {
            accTime += this.segments[i].duration;
        }
        this.currentTime = accTime + effectiveLocalTime;

        // 每秒打印一次进度（用于调试）
        if (Math.floor(this.currentTime) !== Math.floor(this.currentTime - 0.033)) {
            console.log('[CanvasNLEEngine] Progress:', this.currentTime.toFixed(2), '/', this.totalDuration.toFixed(2));
        }

        this.emit({ type: 'timeupdate', data: { time: this.currentTime } });

        // 检查是否需要切换片段
        if (effectiveLocalTime >= segment.duration - 0.05) {
            this.switchToNextSegment();
        }
    }

    /**
     * 切换到下一个片段
     */
    private async switchToNextSegment(): Promise<void> {
        const nextIndex = this.currentSegmentIndex + 1;

        if (nextIndex >= this.segments.length) {
            // 播放完毕
            this.pause();
            this.emit({ type: 'ended' });
            return;
        }

        const nextSegment = this.segments[nextIndex];
        const inactiveVideo = this.getInactiveVideo();

        // 检查是否已预加载
        if (inactiveVideo.src.includes(nextSegment.url) && inactiveVideo.readyState >= 2) {
            // 无缝切换
            console.log('[CanvasNLEEngine] Seamless switch to segment', nextIndex);

            // 暂停当前视频
            this.getActiveVideo().pause();

            // 切换活跃标志
            this.activePrimary = !this.activePrimary;
            this.currentSegmentIndex = nextIndex;

            // 开始播放新视频
            const newVideo = this.getActiveVideo();
            newVideo.currentTime = nextSegment.trimStart || 0;
            await newVideo.play();

            // 切换帧提取器
            this.startFrameExtraction();

            this.emit({ type: 'segmentchange', data: { index: nextIndex } });

            // 预加载下下个片段
            if (nextIndex + 1 < this.segments.length) {
                this.preloadSegment(nextIndex + 1);
            }
        } else {
            // 回退到传统加载
            console.warn('[CanvasNLEEngine] Preload failed, falling back to load');
            await this.loadSegment(nextIndex, true);
            this.currentSegmentIndex = nextIndex;

            this.emit({ type: 'segmentchange', data: { index: nextIndex } });

            // 预加载下下个片段
            if (nextIndex + 1 < this.segments.length) {
                this.preloadSegment(nextIndex + 1);
            }
        }
    }

    /**
     * 设置音量
     */
    setVolume(volume: number): void {
        this.volume = Math.max(0, Math.min(1, volume));
        this.primaryVideo.volume = this.volume;
        this.secondaryVideo.volume = this.volume;
    }

    /**
     * 设置静音
     */
    setMuted(muted: boolean): void {
        this.primaryVideo.muted = muted;
        this.secondaryVideo.muted = muted;
    }

    /**
     * 获取播放状态
     */
    getState(): PlaybackState {
        return {
            isPlaying: this.isPlaying,
            currentTime: this.currentTime,
            duration: this.totalDuration,
            currentSegmentIndex: this.currentSegmentIndex
        };
    }

    /**
     * 获取当前活跃的 video 元素
     */
    private getActiveVideo(): HTMLVideoElement {
        return this.activePrimary ? this.primaryVideo : this.secondaryVideo;
    }

    /**
     * 获取当前非活跃的 video 元素
     */
    private getInactiveVideo(): HTMLVideoElement {
        return this.activePrimary ? this.secondaryVideo : this.primaryVideo;
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
    private emit(event: EngineEvent): void {
        const listeners = this.eventListeners.get(event.type);
        if (listeners) {
            listeners.forEach(callback => callback(event));
        }
    }

    /**
     * 清理资源
     */
    dispose(): void {
        // 停止帧提取
        if (this.frameExtractor) {
            this.frameExtractor.stop();
            this.frameExtractor = null;
        }

        // 停止进度跟踪
        this.stopProgressTracking();

        // 清理 video 元素
        this.primaryVideo.pause();
        this.primaryVideo.src = '';
        this.primaryVideo.remove();

        this.secondaryVideo.pause();
        this.secondaryVideo.src = '';
        this.secondaryVideo.remove();

        // 清空事件监听
        this.eventListeners.clear();

        // 清空 Canvas
        this.renderer.clear();

        console.log('[CanvasNLEEngine] Disposed');
    }
}

// 导出工厂函数
export function createCanvasNLEEngine(config: CanvasNLEEngineConfig): CanvasNLEEngine {
    return new CanvasNLEEngine(config);
}
