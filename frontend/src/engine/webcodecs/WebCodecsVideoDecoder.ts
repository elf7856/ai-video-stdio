/**
 * VideoDecoder - WebCodecs 视频解码器封装
 *
 * 职责：
 * - 初始化 WebCodecs VideoDecoder
 * - 解码视频帧
 * - 管理解码状态
 * - 提供帧回调
 */

import { MP4Demuxer } from './MP4Demuxer';
import type { DecodedFrame } from './types';

export class WebCodecsVideoDecoder {
    private decoder: VideoDecoder | null = null;
    private demuxer: MP4Demuxer | null = null;
    private url: string;
    private onFrame: (frame: DecodedFrame) => void;
    private onError: (error: Error) => void;
    private frameCount: number = 0;

    constructor(
        url: string,
        onFrame: (frame: DecodedFrame) => void,
        onError: (error: Error) => void
    ) {
        this.url = url;
        this.onFrame = onFrame;
        this.onError = onError;
    }

    /**
     * 初始化解码器
     */
    async initialize(): Promise<void> {
        // 检查 WebCodecs 支持
        if (typeof VideoDecoder === 'undefined') {
            throw new Error('WebCodecs is not supported in this browser');
        }

        // 初始化解复用器
        this.demuxer = new MP4Demuxer(this.url);
        await this.demuxer.initialize();

        // 获取视频配置
        const config = this.demuxer.getVideoConfig();

        // 创建解码器
        this.decoder = new VideoDecoder({
            output: (frame: VideoFrame) => {
                this.handleDecodedFrame(frame);
            },
            error: (error: Error) => {
                console.error('[WebCodecsVideoDecoder] Decoder error:', error);
                this.onError(error);
            }
        });

        // 配置解码器
        this.decoder.configure(config);

        console.log('[WebCodecsVideoDecoder] Initialized with config:', config);
    }

    /**
     * 处理解码后的帧
     */
    private handleDecodedFrame(frame: VideoFrame): void {
        const decodedFrame: DecodedFrame = {
            frame: frame,
            timestamp: frame.timestamp || 0,
            duration: frame.duration || 33333 // 默认 30fps
        };

        this.frameCount++;
        this.onFrame(decodedFrame);
    }

    /**
     * 解码一个 EncodedVideoChunk
     */
    decode(chunk: EncodedVideoChunk): void {
        if (!this.decoder) {
            throw new Error('Decoder not initialized');
        }

        this.decoder.decode(chunk);
    }

    /**
     * 刷新解码器缓冲区
     */
    async flush(): Promise<void> {
        if (!this.decoder) return;
        await this.decoder.flush();
    }

    /**
     * 获取解码器状态
     */
    getState(): CodecState {
        return this.decoder?.state || 'closed';
    }

    /**
     * 获取已解码的帧数
     */
    getFrameCount(): number {
        return this.frameCount;
    }

    /**
     * 关闭解码器
     */
    async close(): Promise<void> {
        if (this.decoder) {
            await this.decoder.flush();
            this.decoder.close();
            this.decoder = null;
        }

        if (this.demuxer) {
            this.demuxer.dispose();
            this.demuxer = null;
        }

        this.frameCount = 0;
    }
}
