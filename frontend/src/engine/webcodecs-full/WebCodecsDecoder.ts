/**
 * WebCodecsDecoder - 真正的 WebCodecs 视频解码器
 *
 * 职责：
 * - 使用 WebCodecs VideoDecoder 解码视频
 * - 管理解码后的 VideoFrame
 * - 提供帧级精确控制
 */

import type { MP4Sample, VideoTrackInfo } from './MP4BoxDemuxer';

export interface DecodedVideoFrame {
    frame: VideoFrame;
    timestamp: number; // 微秒
    duration: number;  // 微秒
}

export class WebCodecsDecoder {
    private decoder: VideoDecoder | null = null;
    private onFrame: ((frame: DecodedVideoFrame) => void) | null = null;
    private onError: ((error: Error) => void) | null = null;
    private frameCount: number = 0;
    private isConfigured: boolean = false;

    constructor(
        trackInfo: VideoTrackInfo,
        onFrame: (frame: DecodedVideoFrame) => void,
        onError: (error: Error) => void
    ) {
        this.onFrame = onFrame;
        this.onError = onError;

        // 检查 WebCodecs 支持
        if (typeof VideoDecoder === 'undefined') {
            throw new Error('WebCodecs is not supported in this browser');
        }

        // 创建解码器
        this.decoder = new VideoDecoder({
            output: (frame: VideoFrame) => {
                this.handleDecodedFrame(frame);
            },
            error: (error: Error) => {
                console.error('[WebCodecsDecoder] Decoder error:', error);
                if (this.onError) {
                    this.onError(error);
                }
            }
        });

        // 配置解码器
        const config: VideoDecoderConfig = {
            codec: trackInfo.codec,
            codedWidth: trackInfo.codedWidth,
            codedHeight: trackInfo.codedHeight,
            // description: trackInfo.description // 如果有的话
        };

        console.log('[WebCodecsDecoder] Configuring with:', config);

        this.decoder.configure(config);
        this.isConfigured = true;
    }

    /**
     * 处理解码后的帧
     */
    private handleDecodedFrame(frame: VideoFrame): void {
        const decodedFrame: DecodedVideoFrame = {
            frame: frame,
            timestamp: frame.timestamp || 0,
            duration: frame.duration || 33333 // 默认 30fps
        };

        this.frameCount++;

        if (this.onFrame) {
            this.onFrame(decodedFrame);
        }
    }

    /**
     * 解码一个样本
     */
    decode(sample: MP4Sample): void {
        if (!this.decoder || !this.isConfigured) {
            console.error('[WebCodecsDecoder] Decoder not ready');
            return;
        }

        try {
            const chunk = new EncodedVideoChunk({
                type: sample.isKeyFrame ? 'key' : 'delta',
                timestamp: sample.timestamp,
                duration: sample.duration,
                data: sample.data
            });

            this.decoder.decode(chunk);

            if (this.frameCount === 0) {
                console.log('[WebCodecsDecoder] First chunk decoded');
            }
        } catch (error) {
            console.error('[WebCodecsDecoder] Failed to decode chunk:', error);
            if (this.onError) {
                this.onError(error as Error);
            }
        }
    }

    /**
     * 刷新解码器缓冲区
     */
    async flush(): Promise<void> {
        if (!this.decoder) return;

        try {
            await this.decoder.flush();
            console.log('[WebCodecsDecoder] Flushed');
        } catch (error) {
            console.error('[WebCodecsDecoder] Flush failed:', error);
        }
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
     * 重置解码器
     */
    async reset(): Promise<void> {
        if (!this.decoder) return;

        try {
            await this.decoder.flush();
            this.decoder.reset();
            this.frameCount = 0;
            console.log('[WebCodecsDecoder] Reset');
        } catch (error) {
            console.error('[WebCodecsDecoder] Reset failed:', error);
        }
    }

    /**
     * 关闭解码器
     */
    async close(): Promise<void> {
        if (this.decoder) {
            try {
                await this.decoder.flush();
                this.decoder.close();
            } catch (error) {
                console.error('[WebCodecsDecoder] Close failed:', error);
            }
            this.decoder = null;
        }

        this.frameCount = 0;
        this.isConfigured = false;
        console.log('[WebCodecsDecoder] Closed');
    }
}
