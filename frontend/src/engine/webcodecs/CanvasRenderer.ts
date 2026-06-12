/**
 * CanvasRenderer - Canvas 渲染器
 *
 * 职责：
 * - 将 VideoFrame 渲染到 Canvas
 * - 处理缩放和裁剪
 * - 支持转场效果（可选）
 */

export class CanvasRenderer {
    private canvas: HTMLCanvasElement;
    private ctx: CanvasRenderingContext2D;
    private width: number;
    private height: number;

    constructor(canvas: HTMLCanvasElement) {
        this.canvas = canvas;
        const ctx = canvas.getContext('2d', {
            alpha: false,
            desynchronized: true // 提高性能
        });

        if (!ctx) {
            throw new Error('Failed to get 2D context');
        }

        this.ctx = ctx;
        this.width = canvas.width;
        this.height = canvas.height;
    }

    /**
     * 设置 Canvas 尺寸
     */
    setSize(width: number, height: number): void {
        this.width = width;
        this.height = height;
        this.canvas.width = width;
        this.canvas.height = height;
    }

    /**
     * 渲染一帧到 Canvas
     * 支持 VideoFrame 和 HTMLVideoElement
     */
    renderFrame(source: VideoFrame | HTMLVideoElement): void {
        // 清空 Canvas
        this.ctx.fillStyle = '#000';
        this.ctx.fillRect(0, 0, this.width, this.height);

        // 获取源的宽高
        let sourceWidth: number;
        let sourceHeight: number;

        if (source instanceof VideoFrame) {
            sourceWidth = source.displayWidth;
            sourceHeight = source.displayHeight;
        } else if (source instanceof HTMLVideoElement) {
            sourceWidth = source.videoWidth;
            sourceHeight = source.videoHeight;
        } else {
            return;
        }

        if (sourceWidth === 0 || sourceHeight === 0) {
            return;
        }

        // 计算缩放以适应 Canvas（保持宽高比）
        const videoAspect = sourceWidth / sourceHeight;
        const canvasAspect = this.width / this.height;

        let drawWidth = this.width;
        let drawHeight = this.height;
        let x = 0;
        let y = 0;

        if (videoAspect > canvasAspect) {
            // 视频更宽，以宽度为准
            drawHeight = this.width / videoAspect;
            y = (this.height - drawHeight) / 2;
        } else {
            // 视频更高，以高度为准
            drawWidth = this.height * videoAspect;
            x = (this.width - drawWidth) / 2;
        }

        // 绘制帧
        this.ctx.drawImage(source as any, x, y, drawWidth, drawHeight);
    }

    /**
     * 清空 Canvas
     */
    clear(): void {
        this.ctx.fillStyle = '#000';
        this.ctx.fillRect(0, 0, this.width, this.height);
    }

    /**
     * 获取 Canvas 元素
     */
    getCanvas(): HTMLCanvasElement {
        return this.canvas;
    }
}
