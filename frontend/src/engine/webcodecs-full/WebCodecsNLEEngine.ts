/**
 * WebCodecsNLEEngine - 完整的 WebCodecs NLE 引擎
 *
 * 特点：
 * - 帧级精确 seek
 * - 真正的无缝切换
 * - 完全控制播放
 * - 支持专业后期编辑
 */

import { MP4BoxDemuxer } from './MP4BoxDemuxer';
import { WebCodecsDecoder } from './WebCodecsDecoder';
import { FrameBuffer } from './FrameBuffer';
import { CanvasRenderer } from '../webcodecs/CanvasRenderer';
import type { VideoSegment, PlaybackState, EngineEvent, EventCallback } from '../webcodecs/types';

export interface WebCodecsNLEEngineConfig {
    canvas: HTMLCanvasElement;
    urlHelper: (path: string) => string;
}

export class WebCodecsNLEEngine {
    // 渲染器
    private renderer: CanvasRenderer;
    private urlHelper: (path: string) => string;

    // 当前片段的解码器和缓冲
    private currentDemuxer: MP4BoxDemuxer | null = null;
    private currentDecoder: WebCodecsDecoder | null = null;
    private currentFrameBuffer: FrameBuffer;

    // 下一个片段的预加载
    private nextDemuxer: MP4BoxDemuxer | null = null;
    private nextDecoder: WebCodecsDecoder | null = null;
    private nextFrameBuffer: FrameBuffer;

    // 时间轴数据
    private segments: VideoSegment[] = [];
    private currentSegmentIndex: number = 0;
    private totalDuration: number = 0;

    // 播放状态
    private isPlaying: boolean = false;
    private currentTime: number = 0; // 全局时间（秒）
    private playbackStartTime: number = 0;
    private playbackStartOffset: number = 0;

    // 音频（暂时使用隐藏的 audio 元素）
    private audioElement: HTMLAudioElement;

    // 渲染循环
    private animationFrameId: number | null = null;

    // 事件监听
    private eventListeners: Map<string, Set<EventCallback>> = new Map();

    constructor(config: WebCodecsNLEEngineConfig) {
        this.renderer = new CanvasRenderer(config.canvas);
        this.urlHelper = config.urlHelper;
        this.currentFrameBuffer = new FrameBuffer(300);
        this.nextFrameBuffer = new FrameBuffer(300);

        // 创建音频元素
        this.audioElement = document.createElement('audio');
        this.audioElement.crossOrigin = 'anonymous';
        this.audioElement.style.display = 'none';
        document.body.appendChild(this.audioElement);

        console.log('[WebCodecsNLEEngine] Initialized');
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
        this.totalDuration = segments.reduce((sum, seg) => sum + seg.duration, 0);

        console.log('[WebCodecsNLEEngine] Loading timeline with', segments.length, 'segments');

        // 加载第一个片段
        await this.loadSegment(0);

        // 预加载第二个片段
        if (segments.length > 1) {
            this.preloadSegment(1);
        }

        this.emit({ type: 'ready' });
        console.log('[WebCodecsNLEEngine] Timeline loaded');
    }

    /**
     * 加载指定片段
     */
    private async loadSegment(index: number): Promise<void> {
        const segment = this.segments[index];
        if (!segment) {
            throw new Error(`Segment ${index} not found`);
        }

        console.log('[WebCodecsNLEEngine] Loading segment', index);

        // 清理旧的解码器
        if (this.currentDecoder) {
            await this.currentDecoder.close();
        }
        if (this.currentDemuxer) {
            this.currentDemuxer.dispose();
        }

        // 清空帧缓冲
        this.currentFrameBuffer.clear();

        // 创建新的解复用器
        this.currentDemuxer = new MP4BoxDemuxer();
        const url = this.urlHelper(segment.url);

        // 先设置样本回调，再加载文件
        this.currentDemuxer.setVideoSampleCallback((sample) => {
            if (this.currentDecoder) {
                this.currentDecoder.decode(sample);
            }
        });

        await this.currentDemuxer.load(url);

        const videoTrack = this.currentDemuxer.getVideoTrack();
        if (!videoTrack) {
            throw new Error('No video track found');
        }

        // 设置 Canvas 尺寸
        this.renderer.setSize(videoTrack.codedWidth, videoTrack.codedHeight);

        // 创建解码器
        this.currentDecoder = new WebCodecsDecoder(
            videoTrack,
            (frame) => {
                // 将解码的帧添加到缓冲区
                this.currentFrameBuffer.addFrame(frame);
                console.log('[WebCodecsNLEEngine] Frame decoded, buffer size:', this.currentFrameBuffer.getFrameCount());

                // 如果是第一帧，立即渲染
                if (this.currentFrameBuffer.getFrameCount() === 1) {
                    this.renderer.renderFrame(frame.frame);
                    console.log('[WebCodecsNLEEngine] Rendered first frame');
                }
            },
            (error) => {
                console.error('[WebCodecsNLEEngine] Decoder error:', error);
                this.emit({ type: 'error', data: { message: error.message } });
            }
        );

        // 开始解码（MP4Box 会自动开始提取样本）
        console.log('[WebCodecsNLEEngine] Starting decoding for segment', index);

        // 加载音频
        this.audioElement.src = url;
        this.audioElement.currentTime = segment.trimStart || 0;
        this.audioElement.load();

        console.log('[WebCodecsNLEEngine] Segment', index, 'loaded');
    }

    /**
     * 预加载下一个片段
     */
    private async preloadSegment(index: number): Promise<void> {
        const segment = this.segments[index];
        if (!segment) return;

        console.log('[WebCodecsNLEEngine] Preloading segment', index);

        // 清理旧的预加载
        if (this.nextDecoder) {
            await this.nextDecoder.close();
        }
        if (this.nextDemuxer) {
            this.nextDemuxer.dispose();
        }

        this.nextFrameBuffer.clear();

        // 创建新的解复用器
        this.nextDemuxer = new MP4BoxDemuxer();
        const url = this.urlHelper(segment.url);

        // 先设置样本回调
        this.nextDemuxer.setVideoSampleCallback((sample) => {
            if (this.nextDecoder) {
                this.nextDecoder.decode(sample);
            }
        });

        await this.nextDemuxer.load(url);

        const videoTrack = this.nextDemuxer.getVideoTrack();
        if (!videoTrack) return;

        // 创建解码器
        this.nextDecoder = new WebCodecsDecoder(
            videoTrack,
            (frame) => {
                this.nextFrameBuffer.addFrame(frame);
            },
            (error) => {
                console.error('[WebCodecsNLEEngine] Preload decoder error:', error);
            }
        );

        // 开始解码（MP4Box 会自动开始提取样本）
        console.log('[WebCodecsNLEEngine] Starting decoding for preload segment', index);

        console.log('[WebCodecsNLEEngine] Segment', index, 'preloaded');
    }

    /**
     * 播放
     */
    async play(): Promise<void> {
        if (this.isPlaying) return;

        this.isPlaying = true;
        this.playbackStartTime = performance.now();
        this.playbackStartOffset = this.currentTime;

        // 播放音频
        try {
            await this.audioElement.play();
        } catch (error) {
            console.warn('[WebCodecsNLEEngine] Audio play failed:', error);
        }

        // 开始渲染循环
        this.startRenderLoop();

        this.emit({ type: 'play' });
        console.log('[WebCodecsNLEEngine] Playing from', this.currentTime);
    }

    /**
     * 暂停
     */
    pause(): void {
        if (!this.isPlaying) return;

        this.isPlaying = false;
        this.audioElement.pause();
        this.stopRenderLoop();

        this.emit({ type: 'pause' });
        console.log('[WebCodecsNLEEngine] Paused at', this.currentTime);
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
     * Seek 到指定时间（帧级精确）
     */
    async seek(time: number): Promise<void> {
        console.log('[WebCodecsNLEEngine] Seeking to', time);

        const wasPlaying = this.isPlaying;
        if (wasPlaying) {
            this.pause();
        }

        this.currentTime = time;

        // 查找目标片段
        let accTime = 0;
        for (let i = 0; i < this.segments.length; i++) {
            const segment = this.segments[i];
            if (time >= accTime && time < accTime + segment.duration) {
                const localTime = time - accTime;

                if (i !== this.currentSegmentIndex) {
                    // 切换到不同片段
                    await this.loadSegment(i);
                    this.currentSegmentIndex = i;

                    // 预加载下一个
                    if (i + 1 < this.segments.length) {
                        this.preloadSegment(i + 1);
                    }
                }

                // 精确 seek 到帧
                await this.seekToFrame(localTime);

                // 同步音频
                this.audioElement.currentTime = localTime + (segment.trimStart || 0);

                if (wasPlaying) {
                    await this.play();
                }

                this.emit({ type: 'timeupdate', data: { time } });
                return;
            }
            accTime += segment.duration;
        }
    }

    /**
     * Seek 到精确的帧
     */
    private async seekToFrame(localTime: number): Promise<void> {
        const targetTimestamp = localTime * 1000000; // 转换为微秒

        // 从帧缓冲获取最接近的帧
        const frame = this.currentFrameBuffer.getClosestFrame(targetTimestamp);

        if (frame) {
            // 渲染该帧
            this.renderer.renderFrame(frame.frame);
            console.log('[WebCodecsNLEEngine] Rendered frame at', (frame.timestamp / 1000000).toFixed(3), 's');
        } else {
            console.warn('[WebCodecsNLEEngine] No frame found for time', localTime);
            // 如果没有缓存的帧，需要重新解码
            // TODO: 实现按需解码
        }
    }

    /**
     * 开始渲染循环
     */
    private startRenderLoop(): void {
        const render = () => {
            if (!this.isPlaying) return;

            // 计算当前时间
            const elapsed = (performance.now() - this.playbackStartTime) / 1000;
            this.currentTime = this.playbackStartOffset + elapsed;

            // 获取当前片段的本地时间
            let accTime = 0;
            for (let i = 0; i < this.currentSegmentIndex; i++) {
                accTime += this.segments[i].duration;
            }
            const localTime = this.currentTime - accTime;
            const targetTimestamp = localTime * 1000000;

            // 获取并渲染当前帧
            const frame = this.currentFrameBuffer.getClosestFrame(targetTimestamp);
            if (frame) {
                this.renderer.renderFrame(frame.frame);
            } else {
                // 如果没有帧，记录警告
                if (this.animationFrameId && this.currentFrameBuffer.getFrameCount() === 0) {
                    console.warn('[WebCodecsNLEEngine] No frames in buffer during playback');
                }
            }

            // 触发时间更新事件
            this.emit({ type: 'timeupdate', data: { time: this.currentTime } });

            // 检查是否需要切换片段
            const currentSegment = this.segments[this.currentSegmentIndex];
            if (currentSegment && localTime >= currentSegment.duration - 0.05) {
                this.switchToNextSegment();
            }

            this.animationFrameId = requestAnimationFrame(render);
        };

        this.animationFrameId = requestAnimationFrame(render);
    }

    /**
     * 停止渲染循环
     */
    private stopRenderLoop(): void {
        if (this.animationFrameId !== null) {
            cancelAnimationFrame(this.animationFrameId);
            this.animationFrameId = null;
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

        console.log('[WebCodecsNLEEngine] Switching to segment', nextIndex);

        // 如果已预加载，直接切换
        if (this.nextFrameBuffer.getFrameCount() > 0) {
            // 交换缓冲区
            const tempBuffer = this.currentFrameBuffer;
            this.currentFrameBuffer = this.nextFrameBuffer;
            this.nextFrameBuffer = tempBuffer;
            this.nextFrameBuffer.clear();

            // 交换解码器
            const tempDecoder = this.currentDecoder;
            const tempDemuxer = this.currentDemuxer;
            this.currentDecoder = this.nextDecoder;
            this.currentDemuxer = this.nextDemuxer;
            this.nextDecoder = tempDecoder;
            this.nextDemuxer = tempDemuxer;

            this.currentSegmentIndex = nextIndex;

            // 切换音频
            const nextSegment = this.segments[nextIndex];
            this.audioElement.src = this.urlHelper(nextSegment.url);
            this.audioElement.currentTime = nextSegment.trimStart || 0;
            await this.audioElement.play();

            // 预加载下下个片段
            if (nextIndex + 1 < this.segments.length) {
                this.preloadSegment(nextIndex + 1);
            }

            this.emit({ type: 'segmentchange', data: { index: nextIndex } });
        } else {
            // 回退到加载
            await this.loadSegment(nextIndex);
            this.currentSegmentIndex = nextIndex;

            if (nextIndex + 1 < this.segments.length) {
                this.preloadSegment(nextIndex + 1);
            }

            this.emit({ type: 'segmentchange', data: { index: nextIndex } });
        }
    }

    /**
     * 设置音量
     */
    setVolume(volume: number): void {
        this.audioElement.volume = Math.max(0, Math.min(1, volume));
    }

    /**
     * 设置静音
     */
    setMuted(muted: boolean): void {
        this.audioElement.muted = muted;
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
    async dispose(): Promise<void> {
        this.stopRenderLoop();

        if (this.currentDecoder) {
            await this.currentDecoder.close();
        }
        if (this.currentDemuxer) {
            this.currentDemuxer.dispose();
        }
        if (this.nextDecoder) {
            await this.nextDecoder.close();
        }
        if (this.nextDemuxer) {
            this.nextDemuxer.dispose();
        }

        this.currentFrameBuffer.clear();
        this.nextFrameBuffer.clear();

        this.audioElement.pause();
        this.audioElement.remove();

        this.eventListeners.clear();
        this.renderer.clear();

        console.log('[WebCodecsNLEEngine] Disposed');
    }
}

// 导出工厂函数
export function createWebCodecsNLEEngine(config: WebCodecsNLEEngineConfig): WebCodecsNLEEngine {
    return new WebCodecsNLEEngine(config);
}
