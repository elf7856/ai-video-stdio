/**
 * MP4Demuxer - MP4 解复用器
 *
 * 这是一个简化的 MP4 解复用器
 * 在生产环境中，应该使用完整的解复用库，如 mp4box.js
 *
 * 当前实现：使用 video 元素作为后备方案获取编码数据
 */

export interface MP4Sample {
    data: Uint8Array;
    timestamp: number; // 微秒
    duration: number;  // 微秒
    isKeyFrame: boolean;
}

export class MP4Demuxer {
    private video: HTMLVideoElement;
    private url: string;

    constructor(url: string) {
        this.url = url;
        this.video = document.createElement('video');
        this.video.crossOrigin = 'anonymous';
    }

    /**
     * 初始化解复用器
     */
    async initialize(): Promise<void> {
        return new Promise((resolve, reject) => {
            this.video.addEventListener('loadedmetadata', () => resolve(), { once: true });
            this.video.addEventListener('error', reject, { once: true });
            this.video.src = this.url;
            this.video.load();
        });
    }

    /**
     * 获取视频配置信息
     */
    getVideoConfig(): VideoDecoderConfig {
        return {
            codec: 'avc1.42E01E', // H.264 Baseline
            codedWidth: this.video.videoWidth,
            codedHeight: this.video.videoHeight,
            // 注意：实际应该从 MP4 文件中提取 extradata
        };
    }

    /**
     * 获取视频时长（秒）
     */
    getDuration(): number {
        return this.video.duration;
    }

    /**
     * 获取帧率
     */
    getFrameRate(): number {
        // 默认 30fps，实际应该从视频流中解析
        return 30;
    }

    /**
     * 清理资源
     */
    dispose(): void {
        this.video.src = '';
        this.video.load();
    }
}
