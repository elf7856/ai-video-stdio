/**
 * VideoFrameExtractor - 视频帧提取器
 *
 * 使用 requestVideoFrameCallback API 从 video 元素提取帧
 * 并绘制到 Canvas 上，实现无缝切换
 *
 * 参考：https://developer.mozilla.org/en-US/docs/Web/API/HTMLVideoElement/requestVideoFrameCallback
 */

import { CanvasRenderer } from './CanvasRenderer';

export class VideoFrameExtractor {
    private video: HTMLVideoElement;
    private renderer: CanvasRenderer;
    private callbackId: number | null = null;
    private isActive: boolean = false;
    private onFrame: (() => void) | null = null;

    constructor(video: HTMLVideoElement, renderer: CanvasRenderer) {
        this.video = video;
        this.renderer = renderer;
    }

    /**
     * 开始提取帧
     */
    start(onFrame?: () => void): void {
        if (this.isActive) return;

        this.isActive = true;
        this.onFrame = onFrame || null;
        this.scheduleFrame();

        console.log('[VideoFrameExtractor] Started');
    }

    /**
     * 停止提取帧
     */
    stop(): void {
        if (!this.isActive) return;

        this.isActive = false;

        if (this.callbackId !== null) {
            // @ts-ignore - requestVideoFrameCallback 是较新的 API
            this.video.cancelVideoFrameCallback(this.callbackId);
            this.callbackId = null;
        }

        console.log('[VideoFrameExtractor] Stopped');
    }

    /**
     * 调度下一帧
     */
    private scheduleFrame(): void {
        if (!this.isActive) return;

        // 使用 requestVideoFrameCallback
        // @ts-ignore - requestVideoFrameCallback 是较新的 API
        if (typeof this.video.requestVideoFrameCallback === 'function') {
            // @ts-ignore
            this.callbackId = this.video.requestVideoFrameCallback(
                (now: number, metadata: any) => {
                    this.handleFrame(now, metadata);
                }
            );
        } else {
            // 降级方案：使用 requestAnimationFrame
            this.callbackId = requestAnimationFrame(() => {
                this.handleFrame(performance.now(), {});
            });
        }
    }

    /**
     * 处理一帧
     */
    private handleFrame(_now: number, _metadata: any): void {
        if (!this.isActive) return;

        // 绘制当前帧到 Canvas
        try {
            this.renderer.renderFrame(this.video);
        } catch (error) {
            console.error('[VideoFrameExtractor] Failed to render frame:', error);
        }

        // 触发回调
        if (this.onFrame) {
            this.onFrame();
        }

        // 调度下一帧
        this.scheduleFrame();
    }

    /**
     * 检查是否正在运行
     */
    isRunning(): boolean {
        return this.isActive;
    }
}
